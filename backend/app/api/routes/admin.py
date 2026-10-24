from typing import Annotated

import logging
from fastapi import APIRouter, Depends
import asyncio
import psycopg

from app.core.response_factory import success
from app.dependencies.auth import CurrentUser, require_admin
from app.schemas.common.api_response import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

logger = logging.getLogger(__name__)


def _get_indexed_chunk_ids(database_url: str, chunk_ids: list[str]) -> set[str]:
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id::text FROM document_chunks WHERE id::text = ANY(%s)",
                (chunk_ids,),
            )
            return {row[0] for row in cursor.fetchall()}


@router.get("/users", response_model=ApiResponse[dict])
def admin_users(user: Annotated[CurrentUser, Depends(require_admin)]):
    return success(
        data={
            "mode": "admin",
            "user_id": user.user_id,
            "roles": user.roles,
        }
    )


@router.get("/audit", response_model=ApiResponse[dict])
def admin_audit(user: Annotated[CurrentUser, Depends(require_admin)]):
    return success(
        data={
            "audit_events": [
                {
                    "actor_user_id": user.user_id,
                    "action": "ADMIN_AUDIT_VIEW",
                    "target_type": "admin_audit",
                    "target_id": None,
                    "metadata": {"scope": "admin"},
                }
            ]
        }
    )


@router.post("/cache/invalidate", response_model=ApiResponse[dict])
async def admin_cache_invalidate(user: Annotated[CurrentUser, Depends(require_admin)]):
    """Bump the search pipeline generation to invalidate all cached search results.

    Implements semanticAdditions.md §4: bumping generation makes all old
    cache entries unreachable without deleting individual Redis keys.
    """
    from app.services.cache.generation import async_get_generation, bump_generation

    old_generation = await async_get_generation()
    new_generation = await bump_generation()

    return success(
        data={
            "action": "CACHE_INVALIDATE",
            "old_generation": old_generation,
            "new_generation": new_generation,
            "message": "All cached search results are now unreachable. "
                       "New requests will use the new generation.",
        }
    )


@router.get("/evaluation/report", response_model=ApiResponse[dict])
async def admin_evaluation_report(user: Annotated[CurrentUser, Depends(require_admin)]):
    """Generate a retrieval evaluation report comparing strategies.

    Implements semanticAdditions.md §21 and §1205 (Phase 6 — Evaluation).
    """
    from app.services.evaluation.retrieval_evaluator import RetrievalEvaluator
    from app.services.retrieval.retrieval_service import RetrievalService
    from app.services.retrieval.bm25_sparse_search import BM25SparseSearch
    from app.services.retrieval.vector_search import VectorSearch
    from app.services.embedding.embedding_service import EmbeddingService
    from app.services.vectorstore.vector_store_service import VectorStoreService
    from app.services.reranking.reranker_service import RerankerService
    from app.services.embedding.providers.i_embedding_provider import IEmbeddingProvider
    from app.services.vectorstore.i_vector_store import IVectorStore
    from app.services.reranking.interfaces.i_reranker import IReranker
    from app.services.embedding.embedding_factory import EmbeddingFactory
    from app.services.vectorstore.vector_factory import VectorStoreFactory
    from app.services.reranking.reranker_factory import RerankerFactory
    from app.services.resilience.factory import (
        create_embedding_resilience_policy,
        create_reranker_resilience_policy,
    )
    from app.core.settings import settings

    evaluator = RetrievalEvaluator()
    evaluator.load_dataset("app/services/evaluation/sample_dataset.json")

    if not evaluator.queries:
        return success(
            data={
                "action": "EVALUATION_REPORT",
                "queries_loaded": 0,
                "metrics": ["recall", "mrr", "ndcg"],
                "strategies": ["bm25", "dense", "hybrid", "hybrid_reranker"],
                "note": "No evaluation dataset loaded.",
            }
        )

    relevant_chunk_ids = sorted(
        {
            chunk_id
            for query in evaluator.queries
            for chunk_id in (query.relevant_chunk_ids or [])
        }
    )
    indexed_chunk_ids = await asyncio.to_thread(
        _get_indexed_chunk_ids,
        settings.vector_store.database_url,
        relevant_chunk_ids,
    )
    ground_truth_issues = evaluator.ground_truth_issues(indexed_chunk_ids)
    if ground_truth_issues:
        return success(
            data={
                "action": "EVALUATION_REPORT",
                "status": "not_run",
                "queries_loaded": len(evaluator.queries),
                "reason": "Evaluation labels must reference indexed chunks.",
                "ground_truth_issues": ground_truth_issues,
            }
        )

    # Build providers directly from settings (not via DI)
    embedding_provider: IEmbeddingProvider = EmbeddingFactory.create(
        provider_name=settings.embedding.provider,
        model_name=settings.embedding.model_name,
    )
    vector_store_provider: IVectorStore = VectorStoreFactory.create(
        provider_name=settings.vector_store.provider,
        database_url=settings.vector_store.database_url,
    )
    reranker_provider: IReranker | None = None
    if settings.reranking.enabled:
        reranker_provider = RerankerFactory.create(
            provider_name=settings.reranking.provider,
            model_name=settings.reranking.model_name,
        )

    # Build services with resilience policies
    embedding_svc = EmbeddingService(
        provider=embedding_provider,
        resilience_policy=create_embedding_resilience_policy(),
    )
    vector_store_svc = VectorStoreService(provider=vector_store_provider)
    vector_search = VectorSearch(
        embedding_service=embedding_svc,
        vector_store_service=vector_store_svc,
    )
    bm25_search = BM25SparseSearch(database_url=settings.vector_store.database_url)

    # BM25 only
    bm25_svc = RetrievalService(
        vector_search=None,
        bm25_search=bm25_search,
        reranker_service=None,
    )

    # Dense only
    dense_svc = RetrievalService(
        vector_search=vector_search,
        bm25_search=None,
        reranker_service=None,
    )

    # Hybrid
    hybrid_svc = RetrievalService(
        vector_search=vector_search,
        bm25_search=bm25_search,
        reranker_service=None,
    )

    # Hybrid + Reranker
    reranker_svc = None
    if reranker_provider:
        reranker_svc = RerankerService(
            provider=reranker_provider,
            resilience_policy=create_reranker_resilience_policy(),
        )
    hybrid_reranker_svc = RetrievalService(
        vector_search=vector_search,
        bm25_search=bm25_search,
        reranker_service=reranker_svc,
    )

    async def run_evaluation():
        strategies = {
            "bm25": bm25_svc,
            "dense": dense_svc,
            "hybrid": hybrid_svc,
            "hybrid_reranker": hybrid_reranker_svc,
        }

        # Collect results per strategy
        strategies_results: dict[str, list[list[str]]] = {
            name: [] for name in strategies
        }

        for query in evaluator.queries:
            for name, svc in strategies.items():
                try:
                    results = await svc.retrieve(query.query, limit=10)
                    retrieved_ids = [str(r.id) for r in results]
                    strategies_results[name].append(retrieved_ids)
                except Exception as e:
                    logger.error(f"Strategy {name} failed for query '{query.query}': {e}")
                    strategies_results[name].append([])

        return evaluator.generate_report(strategies_results, k=10)

    # Run asynchronously
    report = await run_evaluation()

    return success(
        data={
            "action": "EVALUATION_REPORT",
            "queries_loaded": len(evaluator.queries),
            "metrics": ["recall", "mrr", "ndcg"],
            "strategies": ["bm25", "dense", "hybrid", "hybrid_reranker"],
            "report": report,
        }
    )
