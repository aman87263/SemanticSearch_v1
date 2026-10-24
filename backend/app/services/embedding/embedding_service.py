"""Enhanced embedding service with caching, single-flight, and resilience.

Implements the embedding cache strategy from semanticAdditions.md §3 and §17:
  - Cache key includes provider, model, version, and text hash
  - L1 (process-local LRU) + L2 (Redis) multi-level cache
  - Single-flight: concurrent requests for the same text share one API call
  - Resilience: timeout, semaphore, retry+jitter, circuit breaker

This significantly reduces embedding API costs and latencies, especially for
repeated queries.
"""

import logging

from app.schemas.chunk.entities.chunk import Chunk
from app.schemas.embedding.embedded_chunk import EmbeddedChunk
from app.services.cache.search_cache import CacheKeyBuilder, get_search_cache
from app.services.cache.single_flight import get_single_flight
from app.services.embedding.providers.i_embedding_provider import (
    IEmbeddingProvider,
)
from app.services.llm.providers.provider_router import ProviderRouter
from app.services.resilience.factory import create_embedding_resilience_policy

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service with multi-level caching, single-flight, and resilience."""

    def __init__(
        self,
        provider: IEmbeddingProvider,
        resilience_policy=None,
        provider_router: ProviderRouter | None = None,
    ):
        self._provider = provider
        self._cache = get_search_cache()
        self._provider_router = provider_router
        self._resilience = resilience_policy
        if self._provider_router is None and self._resilience is None:
            self._resilience = create_embedding_resilience_policy()

    @property
    def provider_label(self) -> str:
        """Human-readable provider/model label for cache key namespacing."""
        return getattr(self._provider, "_model_name", "unknown")

    def _build_cache_key(self, text: str) -> str:
        """Build a versioned embedding cache key.

        Key format: embedding:{provider}:{model}:{version}:{text_hash}
        The model version is derived from the provider's model name.
        """
        text_hash = CacheKeyBuilder.compute_hash(text)
        provider_name = type(self._provider).__name__.lower()
        model_name = self.provider_label
        return CacheKeyBuilder.build_embedding_key(
            provider=provider_name,
            model=model_name,
            model_version="v1",
            text_hash=text_hash,
        )

    async def _embed_text(self, text: str) -> list[float]:
        """Fetch and cache a single text embedding."""
        cache_key = self._build_cache_key(text)

        # Check cache first
        cached = await self._cache.get_embedding(cache_key)
        if cached is not None:
            logger.debug(f"Embedding cache HIT for text hash: {cache_key}")
            return cached

        # Single-flight: concurrent calls for the same text share one provider
        # call. The resilient fetch is the single-flight callback so that
        # retries/circuit-breaker state are also deduplicated.
        sf = get_single_flight()

        async def _fetch() -> list[float]:
            vectors = await self._embed_with_fallback([text])
            if len(vectors) != 1:
                raise RuntimeError(
                    "Embedding provider returned an unexpected number of vectors."
                )
            return vectors[0]

        # Wrap with resilience, then deduplicate via single-flight
        async def _resilient_fetch() -> list[float]:
            # When a provider router is available, use its resilience policy
            # which handles fallback between primary and backup providers
            if self._provider_router is not None:
                policy = self._provider_router.get_resilience_policy()
                fallback = self._provider_router.get_fallback()

                if fallback is None:
                    return await policy.execute(_fetch)

                fallback_provider, _ = fallback
                async def _fallback_fetch() -> list[float]:
                    vectors = await fallback_provider.embed([text])
                    if len(vectors) != 1:
                        raise RuntimeError("Fallback provider returned unexpected vector count.")
                    return vectors[0]

                return await policy.execute_with_fallback(
                    primary_call=_fetch,
                    fallback_call=_fallback_fetch,
                )

            if self._resilience is not None:
                return await self._resilience.execute(_fetch)
            raise RuntimeError("Embedding resilience policy is not configured.")

        result = await sf.execute(cache_key, _resilient_fetch)

        # Cache the result
        await self._cache.set_embedding(cache_key, result)
        return result

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if self._provider_router is not None:
            return await self._provider_router.embed(texts)
        return await self._provider.embed(texts)

    async def _embed_with_fallback(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using provider router with fallback."""
        if self._provider_router is None:
            return await self._provider.embed(texts)

        policy = self._provider_router.get_resilience_policy()
        fallback = self._provider_router.get_fallback()

        async def _primary():
            return await self._provider.embed(texts)

        if fallback is None:
            return await policy.execute(_primary)

        fallback_provider, fallback_policy = fallback

        async def _fallback():
            return await fallback_provider.embed(texts)

        return await policy.execute_with_fallback(
            primary_call=_primary,
            fallback_call=_fallback,
        )

    async def generate(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """Generate embeddings for a batch of chunks with caching and single-flight."""
        if not chunks:
            return []

        results: list[EmbeddedChunk | None] = [None] * len(chunks)

        for i, chunk in enumerate(chunks):
            embedding = await self._embed_text(chunk.text)
            results[i] = EmbeddedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                index=chunk.index,
                text=chunk.text,
                vector=embedding,
                metadata=chunk.metadata,
                token_count=chunk.token_count,
            )

        return [r for r in results if r is not None]

    async def generate_query(self, query: str) -> list[float]:
        """Generate an embedding for a query with caching and single-flight."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        return await self._embed_text(query)