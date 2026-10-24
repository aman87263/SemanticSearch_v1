from typing_extensions import Annotated
from fastapi import Depends
from app.core.settings import settings
from app.services.embedding.embedding_service import EmbeddingService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.retrieval.vector_search import VectorSearch
from app.services.retrieval.bm25_sparse_search import BM25SparseSearch
from app.services.retrieval.query_rewriter import QueryRewriter

from app.dependencies.embedding import get_embedding_service
from app.dependencies.vector import get_vector_store_service
from app.services.vectorstore.vector_store_service import VectorStoreService
from app.services.reranking.reranker_service import RerankerService
from app.dependencies.reranker import get_reranker_service
from app.services.resilience.policies import get_llm_resilience_policy as get_singleton_llm_policy


def get_bm25_search() -> BM25SparseSearch:
    """Create a BM25 sparse search provider using the configured database URL."""
    return BM25SparseSearch(database_url=settings.vector_store.database_url)


def get_query_rewriter() -> QueryRewriter:
    """Build the query rewriter, wiring in the configured LLM when available.

    When the primary LLM provider fails, the rewriter falls back to the
    configured LLM fallback provider (e.g., Groq if Ollama fails).
    Falls back to the rule-based expander if no LLM providers are available.
    """
    from app.services.llm.providers.llm_factory import LLMFactory

    llm_provider = None
    fallback_provider = None

    try:
        llm_provider = LLMFactory.create(
            provider_name=settings.llm.provider,
            model_name=settings.llm.model,
            temperature=0.0,
            max_tokens=200,
        )
    except Exception:
        llm_provider = None

    # Try to create fallback provider if configured
    if settings.llm.fallback_provider and settings.llm.fallback_model:
        try:
            fallback_provider = LLMFactory.create(
                provider_name=settings.llm.fallback_provider,
                model_name=settings.llm.fallback_model,
                temperature=0.0,
                max_tokens=200,
            )
        except Exception:
            fallback_provider = None

    return QueryRewriter(
        llm_provider=llm_provider,
        fallback_provider=fallback_provider,
        llm_resilience_policy=get_singleton_llm_policy(),
        enabled=bool(settings.retrieval.query_expansion_enabled),
    )


def get_vector_search(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
) -> VectorSearch:
    return VectorSearch(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
    )


def get_retrieval_service(
    vector_search: VectorSearch = Depends(get_vector_search),
    bm25_search: BM25SparseSearch = Depends(get_bm25_search),
    reranker_service: RerankerService | None = Depends(get_reranker_service),
    query_rewriter: QueryRewriter = Depends(get_query_rewriter),
) -> RetrievalService:
    return RetrievalService(
        vector_search=vector_search,
        bm25_search=bm25_search,
        reranker_service=reranker_service,
        query_rewriter=query_rewriter,
    )
