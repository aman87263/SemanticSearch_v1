"""Multi-level cache with versioned keys for search results and embeddings.

Implements the cache hierarchy described in semanticAdditions.md §1, §2, §3,
§4, and §15:
  - L1: process-local LRU cache (fast, bounded)
  - L2: Redis (shared across instances)
  - Versioned cache keys to enable clean invalidation via generation bumps
    rather than deleting millions of keys.

Cache keys follow the format:
  search:v{generation}:{tenant_id}:{scope}:{query_hash}
  embedding:{provider}:{model}:{version}:{text_hash}
"""

import hashlib
import json
import time
from collections import OrderedDict
from functools import lru_cache
from typing import Any

import redis.asyncio as redis


class LRUCache:
    """Simple thread-safe LRU cache with TTL for process-local L1 caching."""

    def __init__(self, max_items: int = 1000, ttl_seconds: int = 300):
        self._max_items = max_items
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self._max_items:
            # Pop least recently used (first item)
            self._store.popitem(last=False)
        self._store[key] = (value, time.time() + self._ttl)


class CacheKeyBuilder:
    """Builds versioned cache keys for different cache types."""

    @staticmethod
    def compute_hash(text: str) -> str:
        """Deterministic SHA-256 hash truncated to 32 chars."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def build_search_key(
        *,
        generation: int,
        tenant_id: str | None = None,
        scope: str | None = None,
        canonical_query: str,
        filters_hash: str | None = None,
        embedding_model: str | None = None,
        pipeline_version: str = "v1",
        limit: int | None = None,
        strategy: str | None = None,
    ) -> str:
        """Build a versioned search cache key.

        The generation acts as a cache-invalidation knob: bumping generation
        makes all old entries unreachable without deleting individual keys.
        Authorization scope and tenant participate in the key to prevent
        leaking one user's results to another.
        The limit parameter ensures different result counts don't share cache.
        The strategy parameter ensures different retrieval strategies (bm25,
        dense, hybrid, hybrid_reranker) don't contaminate each other.
        """
        query_hash = CacheKeyBuilder.compute_hash(canonical_query)
        parts = [
            f"search:{pipeline_version}",
            f"gen:{generation}",
            f"tenant:{tenant_id or 'public'}",
            f"scope:{scope or 'anonymous'}",
            f"q:{query_hash}",
        ]
        if filters_hash:
            parts.append(f"f:{filters_hash}")
        if embedding_model:
            parts.append(f"emb:{embedding_model}")
        if limit is not None:
            parts.append(f"lim:{limit}")
        if strategy is not None:
            parts.append(f"strat:{strategy}")
        return ":".join(parts)

    @staticmethod
    def build_embedding_key(
        *,
        provider: str,
        model: str,
        model_version: str,
        text_hash: str,
    ) -> str:
        """Build an embedding cache key that includes provider/model/version."""
        return f"embedding:{provider}:{model}:{model_version}:{text_hash}"


class SearchCache:
    """Multi-level cache for search results.

    L1: in-process LRU (bounded, fast)
    L2: Redis (shared across backend instances)
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        l1_max_items: int = 1000,
        l1_ttl_seconds: int = 300,
        l2_ttl_seconds: int = 3600,
        enabled: bool = True,
    ):
        self._enabled = enabled
        self._redis = redis_client
        self._l1_ttl = l1_ttl_seconds
        self._l2_ttl = l2_ttl_seconds
        self._l1: LRUCache = LRUCache(max_items=l1_max_items, ttl_seconds=l1_ttl_seconds)

    async def get_search_result(self, key: str) -> list[dict] | None:
        if not self._enabled:
            return None

        # L1: process-local
        result = self._l1.get(key)
        if result is not None:
            return result

        # L2: Redis
        if self._redis:
            try:
                cached = await self._redis.get(key)
                if cached:
                    result = json.loads(cached)
                    # Populate L1 for next time
                    self._l1.set(key, result)
                    return result
            except Exception:
                # Redis unavailable — fallback gracefully
                return None

        return None

    async def set_search_result(self, key: str, results: list[dict]) -> None:
        if not self._enabled:
            return

        # Always populate L1
        self._l1.set(key, results)

        # Populate L2 if available
        if self._redis:
            try:
                await self._redis.setex(key, self._l2_ttl, json.dumps(results))
            except Exception:
                pass  # Redis unavailable, L1 still has it

    async def get_embedding(self, key: str) -> list[float] | None:
        if not self._enabled:
            return None

        # L1
        result = self._l1.get(key)
        if result is not None:
            return result

        # L2
        if self._redis:
            try:
                cached = await self._redis.get(key)
                if cached:
                    result = [float(x) for x in json.loads(cached)]
                    self._l1.set(key, result)
                    return result
            except Exception:
                return None

        return None

    async def set_embedding(self, key: str, vector: list[float]) -> None:
        if not self._enabled:
            return

        self._l1.set(key, vector)

        if self._redis:
            try:
                await self._redis.setex(key, self._l2_ttl, json.dumps(vector))
            except Exception:
                pass


_cache: SearchCache | None = None


@lru_cache
def get_search_cache() -> SearchCache:
    """Process-wide cache singleton. Redis is wired from environment."""
    import os
    from app.core.settings import settings

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = None
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
    except Exception:
        redis_client = None

    return SearchCache(
        redis_client=redis_client,
        l1_max_items=getattr(settings, 'cache', None) and getattr(settings.cache, 'l1_max_items', 1000) or 1000,
        l1_ttl_seconds=getattr(settings, 'cache', None) and getattr(settings.cache, 'l1_ttl_seconds', 300) or 300,
        l2_ttl_seconds=getattr(settings, 'cache', None) and getattr(settings.cache, 'l2_ttl_seconds', 3600) or 3600,
        enabled=getattr(settings, 'cache', None) and getattr(settings.cache, 'enabled', True),
    )
