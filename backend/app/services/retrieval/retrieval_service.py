"""Enhanced retrieval service with hybrid BM25 + dense vector search,
multi-level caching, and single-flight protection.

Implements the hybrid search pipeline described in semanticAdditions.md §10,
§12, §13:

  1. BM25 (PostgreSQL FTS) sparse retrieval
  2. Dense vector retrieval (pgvector)
  3. Reciprocal Rank Fusion (RRF) to combine rankings
  4. Optional reranker for final context selection

Also includes multi-level caching (§1, §15) and single-flight protection (§17)
to reduce latency and provider costs.
"""

import asyncio
import hashlib
import logging
import time
from uuid import UUID

from app.core.settings import settings
from app.middleware.observability_middleware import record_stage, get_search_metrics
from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.cache.search_cache import CacheKeyBuilder, SearchCache, get_search_cache
from app.services.cache.single_flight import get_single_flight
from app.services.cache.generation import get_generation, async_get_generation
from app.services.reranking.reranker_service import RerankerService
from app.services.retrieval.bm25_sparse_search import BM25SparseSearch
from app.services.retrieval.query_normalizer import normalize_query
from app.services.retrieval.query_rewriter import (
    QueryRewriter,
    SimpleLLMForRewriting,
)
from app.services.retrieval.rrf_fusion import reciprocal_rank_fusion
from app.services.retrieval.vector_search import VectorSearch

logger = logging.getLogger(__name__)


def _compute_filters_hash(
    document_id: UUID | None,
    user_id: str | None,
    is_admin: bool,
) -> str:
    """Compute a hash of authorization filters for cache scoping."""
    parts = []
    if document_id:
        parts.append(f"doc:{document_id}")
    if user_id:
        parts.append(f"user:{user_id}")
    parts.append(f"admin:{is_admin}")
    raw = "|".join(parts) if parts else "none"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _dedupe_by_id(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Deduplicate chunks by ID, keeping the highest-scoring occurrence.

    Needed because query expansion can retrieve the same chunk via multiple
    variants; duplicates would otherwise distort RRF ranking.
    """
    best: dict[UUID, RetrievedChunk] = {}
    for chunk in chunks:
        existing = best.get(chunk.id)
        if existing is None or chunk.similarity > existing.similarity:
            best[chunk.id] = chunk
    return list(best.values())


class RetrievalService:
    """Orchestrates hybrid retrieval with caching, single-flight, and RRF.

    The search pipeline:

        query
          ? normalize/canonicalize
          ? check L1 + L2 cache (single-flight protected)
          ? if miss -> BM25 + dense retrieval (parallel)
              ? RRF fusion
              ? optional reranker
              ? cache result
    """

    def __init__(
        self,
        vector_search: VectorSearch | None = None,
        bm25_search: BM25SparseSearch | None = None,
        reranker_service: RerankerService | None = None,
        cache: SearchCache | None = None,
        query_rewriter: QueryRewriter | None = None,
    ):
        self._vector_search = vector_search
        self._bm25_search = bm25_search
        self._reranker_service = reranker_service
        self._cache = cache or get_search_cache()
        self._rewriter = query_rewriter or QueryRewriter(
            llm_provider=SimpleLLMForRewriting(),
            enabled=bool(
                getattr(settings.retrieval, "query_expansion_enabled", True)
            ),
        )
        # Determine strategy label for cache key isolation
        has_bm25 = self._bm25_search is not None
        has_dense = self._vector_search is not None
        has_reranker = self._reranker_service is not None
        if has_bm25 and has_dense and has_reranker:
            self._strategy = "hybrid_reranker"
        elif has_bm25 and has_dense:
            self._strategy = "hybrid"
        elif has_dense:
            self._strategy = "dense"
        elif has_bm25:
            self._strategy = "bm25"
        else:
            self._strategy = "none"

    async def retrieve(
        self,
        query: str,
        limit: int | None = None,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[RetrievedChunk]:
        """Execute hybrid retrieval for a query.

        Args:
            query: Raw user query text.
            limit: Maximum number of final results.
            document_id: Optional document filter.
            user_id: Optional user ID for authorization scoping.
            is_admin: Whether the user has admin privileges.

        Returns:
            List of RetrievedChunk results, fused and optionally reranked.
        """
        if not query or not query.strip():
            return []

        final_limit = limit if limit is not None else settings.retrieval.default_limit

        # --- Step 1: Normalize query ---
        canonical_query = normalize_query(query)
        filters_hash = _compute_filters_hash(document_id, user_id, is_admin)

        # --- Step 2: Expand query into variants (§14) ---
        # Simple queries return just [canonical]; complex ones may return
        # additional LLM-generated variants. Cache key stays tied to the
        # canonical query so identical user queries share one cache entry.
        query_variants = await self._rewriter.expand(query)

        # --- Step 3: Build cache key ---
        # Use async_get_generation to read from Redis if available
        generation = await async_get_generation()
        cache_key = CacheKeyBuilder.build_search_key(
            generation=generation,
            tenant_id=user_id,
            scope="user" if user_id else "anonymous",
            canonical_query=canonical_query,
            filters_hash=filters_hash,
            embedding_model=getattr(settings.embedding, "model_name", None),
            pipeline_version="v1",
            limit=final_limit,
            strategy=self._strategy,
        )

        # --- Step 4: Check cache ---
        cached = await self._cache.get_search_result(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT for query: {query[:80]}")
            record_stage("cache_hit", 0)
            # Populate observability fields
            metrics = get_search_metrics()
            if metrics:
                metrics.cache_hit = True
            return [RetrievedChunk(**chunk) for chunk in cached]

        # --- Step 5: Single-flight execution ---
        sf = get_single_flight()

        async def _execute_pipeline() -> list[RetrievedChunk]:
            # Double-check cache after acquiring single-flight lock
            cached_inner = await self._cache.get_search_result(cache_key)
            if cached_inner is not None:
                logger.debug(f"Cache HIT (post-flight) for: {query[:80]}")
                metrics = get_search_metrics()
                if metrics:
                    metrics.cache_hit = True
                return [RetrievedChunk(**chunk) for chunk in cached_inner]

            start_time = time.time()

            # --- Step 6: Retrieve across all query variants (§14) ---
            candidate_limit = settings.retrieval.candidate_limit

            # Keep per-variant ranked lists for proper RRF fusion
            # Each variant contributes its own BM25 and dense ranked lists
            bm25_ranked_lists: list[list[RetrievedChunk]] = []
            dense_ranked_lists: list[list[RetrievedChunk]] = []

            for variant in query_variants:
                bm25_r, dense_r = await self._parallel_retrieval(
                    query=query if variant == canonical_query else variant,
                    canonical_query=variant,
                    limit=candidate_limit,
                    document_id=document_id,
                    user_id=user_id,
                    is_admin=is_admin,
                )
                bm25_ranked_lists.append(bm25_r)
                dense_ranked_lists.append(dense_r)

            # Flatten with dedup for logging
            all_bm25: list[RetrievedChunk] = []
            for vlist in bm25_ranked_lists:
                all_bm25.extend(vlist)
            all_dense: list[RetrievedChunk] = []
            for vlist in dense_ranked_lists:
                all_dense.extend(vlist)

            all_bm25 = _dedupe_by_id(all_bm25)
            all_dense = _dedupe_by_id(all_dense)

            # Record retrieval stage and populate observability
            retrieval_elapsed = time.time() - start_time
            record_stage("retrieval", retrieval_elapsed)
            metrics = get_search_metrics()
            if metrics:
                metrics.variants_count = len(query_variants)
                metrics.bm25_count = len(all_bm25)
                metrics.dense_count = len(all_dense)

            # --- Step 7: RRF fusion across ALL variant lists ---
            # Combine all BM25 lists and all dense lists as separate ranked inputs
            all_ranked_lists = bm25_ranked_lists + dense_ranked_lists
            fused_results = self._rrf_fusion_multi(all_ranked_lists, candidate_limit)

            fusion_elapsed = time.time() - start_time - retrieval_elapsed
            record_stage("rrf_fusion", fusion_elapsed)
            if metrics:
                metrics.fused_count = len(fused_results)

            # --- Step 8: Filter by similarity threshold ---
            results = [
                chunk
                for chunk in fused_results
                if chunk.similarity >= settings.retrieval.similarity_threshold
            ]

            # --- Step 9: Rerank ---
            if self._reranker_service:
                rerank_start = time.time()
                try:
                    results = await self._reranker_service.rerank(
                        query=query,
                        chunks=results,
                    )
                except Exception:
                    logger.exception(
                        "Reranking failed; returning unfused retrieval results"
                    )
                rerank_elapsed = time.time() - rerank_start
                record_stage("rerank", rerank_elapsed)
                if metrics:
                    metrics.reranked = True

            # --- Step 10: Apply top_k from reranker settings ---
            top_k = settings.reranking.top_k
            if top_k is not None:
                results = results[:top_k]

            # --- Step 11: Final limit ---
            results = results[:final_limit]

            total_elapsed = time.time() - start_time
            logger.info(
                f"Search pipeline completed in {total_elapsed:.3f}s: "
                f"variants={len(query_variants)}, "
                f"bm25={len(all_bm25)}, dense={len(all_dense)}, "
                f"fused={len(fused_results)}, final={len(results)}"
            )

            if metrics:
                metrics.final_count = len(results)

            # --- Step 12: Cache the result ---
            cacheable = [chunk.model_dump(mode="json") for chunk in results]
            await self._cache.set_search_result(cache_key, cacheable)

            return results

        return await sf.execute(cache_key, _execute_pipeline)

    async def _parallel_retrieval(
        self,
        *,
        query: str,
        canonical_query: str,
        limit: int,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
        """Run BM25 and dense retrieval concurrently, handling missing searchers."""
        bm25_task = None
        if self._bm25_search:
            bm25_task = self._bm25_search.search(
                query=canonical_query,
                limit=limit,
                document_id=document_id,
                user_id=user_id,
                is_admin=is_admin,
            )

        dense_task = None
        if self._vector_search:
            dense_task = self._vector_search.search(
                query=query,
                limit=limit,
                document_id=document_id,
                user_id=user_id,
                is_admin=is_admin,
            )

        if bm25_task and dense_task:
            return await asyncio.gather(bm25_task, dense_task)
        elif bm25_task:
            bm25_results = await bm25_task
            return bm25_results, []
        elif dense_task:
            dense_results = await dense_task
            return [], dense_results
        else:
            return [], []

    def _rrf_fusion(
        self,
        bm25_results: list[RetrievedChunk],
        dense_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Fuse BM25 and dense results using RRF, then return merged chunks."""
        all_chunks: dict[UUID, RetrievedChunk] = {}

        bm25_ids = [chunk.id for chunk in bm25_results]
        dense_ids = [chunk.id for chunk in dense_results]

        for chunk in bm25_results:
            all_chunks[chunk.id] = chunk
        for chunk in dense_results:
            if chunk.id not in all_chunks:
                all_chunks[chunk.id] = chunk
            else:
                # Keep the chunk with the higher similarity from either source
                if chunk.similarity > all_chunks[chunk.id].similarity:
                    all_chunks[chunk.id] = chunk

        fused = reciprocal_rank_fusion(
            ranked_lists=[bm25_ids, dense_ids],
            k=60,
            top_k=top_k,
        )

        results: list[RetrievedChunk] = []
        for chunk_id, _rrf_score in fused:
            chunk = all_chunks.get(chunk_id)
            if chunk:
                results.append(chunk)

        return results

    def _rrf_fusion_multi(
        self,
        ranked_lists: list[list[RetrievedChunk]],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Fuse multiple ranked lists using RRF, then return merged chunks.

        Each ranked list is treated as an independent ranked input to RRF.
        This preserves the ranking contribution of each query variant.
        """
        all_chunks: dict[UUID, RetrievedChunk] = {}
        id_lists: list[list[UUID]] = []

        for chunks in ranked_lists:
            ids = [chunk.id for chunk in chunks]
            id_lists.append(ids)
            for chunk in chunks:
                if chunk.id not in all_chunks:
                    all_chunks[chunk.id] = chunk
                else:
                    # Keep the chunk with the higher similarity from any source
                    if chunk.similarity > all_chunks[chunk.id].similarity:
                        all_chunks[chunk.id] = chunk

        fused = reciprocal_rank_fusion(
            ranked_lists=id_lists,
            k=60,
            top_k=top_k,
        )

        results: list[RetrievedChunk] = []
        for chunk_id, _rrf_score in fused:
            chunk = all_chunks.get(chunk_id)
            if chunk:
                results.append(chunk)

        return results

    def _deduplicate_adjacent(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Dedupe chunks that are adjacent in the same document."""
        # Higher-scoring chunks get priority.
        sorted_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.similarity,
            reverse=True,
        )

        selected: list[RetrievedChunk] = []
        seen_indices: dict[UUID, set[int]] = {}

        for chunk in sorted_chunks:
            doc_seen = seen_indices.setdefault(
                chunk.document_id,
                set(),
            )

            if any(
                index in doc_seen
                for index in (
                    chunk.index - 1,
                    chunk.index,
                    chunk.index + 1,
        )
            ):
                continue

            selected.append(chunk)
            doc_seen.add(chunk.index)

        return selected
