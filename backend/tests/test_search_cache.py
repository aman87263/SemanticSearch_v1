"""Tests for cache key builders and versioning (semanticAdditions.md §1, §3, §4, §22)."""

import pytest

from app.services.cache.search_cache import CacheKeyBuilder, LRUCache


class TestCacheKeyBuilder:
    def test_search_key_contains_all_components(self):
        """Search key must include generation, tenant, scope, and query hash."""
        key = CacheKeyBuilder.build_search_key(
            generation=42,
            tenant_id="user_123",
            scope="user",
            canonical_query="how do i reset my password",
            filters_hash="abc123",
            embedding_model="all-MiniLM-L6-v2",
            pipeline_version="v1",
        )

        assert "search:v1" in key
        assert "gen:42" in key
        assert "tenant:user_123" in key
        assert "scope:user" in key
        assert "q:" in key
        assert "f:abc123" in key
        assert "emb:all-MiniLM-L6-v2" in key

    def test_search_key_does_not_contain_raw_query(self):
        """Raw query text must not appear in the cache key (security)."""
        key = CacheKeyBuilder.build_search_key(
            generation=1,
            tenant_id=None,
            scope="anonymous",
            canonical_query="SECRET_API_KEY_12345",
        )

        assert "SECRET_API_KEY_12345" not in key

    def test_search_key_differs_for_different_tenants(self):
        """Different users must have different cache keys (anti-leak §1)."""
        key_user_a = CacheKeyBuilder.build_search_key(
            generation=1,
            tenant_id="user_a",
            scope="user",
            canonical_query="how do i reset my password",
        )
        key_user_b = CacheKeyBuilder.build_search_key(
            generation=1,
            tenant_id="user_b",
            scope="user",
            canonical_query="how do i reset my password",
        )

        assert key_user_a != key_user_b

    def test_search_key_changes_with_generation(self):
        """Bumping generation must produce a completely different key (§4)."""
        key_v1 = CacheKeyBuilder.build_search_key(
            generation=1,
            tenant_id="user_a",
            scope="user",
            canonical_query="test query",
        )
        key_v2 = CacheKeyBuilder.build_search_key(
            generation=2,
            tenant_id="user_a",
            scope="user",
            canonical_query="test query",
        )

        assert key_v1 != key_v2

    def test_embedding_key_includes_provider_and_model(self):
        """Embedding key must include provider, model, version, text hash (§3, §22)."""
        key = CacheKeyBuilder.build_embedding_key(
            provider="openai",
            model="text-embedding-3-small",
            model_version="v1",
            text_hash="abc123",
        )

        assert "embedding" in key
        assert "openai" in key
        assert "text-embedding-3-small" in key
        assert "v1" in key
        assert "abc123" in key

    def test_embedding_key_differs_by_provider(self):
        """Same text embedded by different providers must have different keys."""
        key_a = CacheKeyBuilder.build_embedding_key(
            provider="openai",
            model="text-embedding-3-small",
            model_version="v1",
            text_hash="abc",
        )
        key_b = CacheKeyBuilder.build_embedding_key(
            provider="groq",
            model="text-embedding-3-small",
            model_version="v1",
            text_hash="abc",
        )

        assert key_a != key_b

    def test_embedding_key_differs_by_model_version(self):
        """Different model versions must have different cache keys (§214-218)."""
        key_v1 = CacheKeyBuilder.build_embedding_key(
            provider="openai",
            model="text-embedding-3-small",
            model_version="v1",
            text_hash="abc",
        )
        key_v2 = CacheKeyBuilder.build_embedding_key(
            provider="openai",
            model="text-embedding-3-small",
            model_version="v2",
            text_hash="abc",
        )

        assert key_v1 != key_v2


class TestLRUCache:
    def test_basic_put_get(self):
        cache = LRUCache(max_items=10, ttl_seconds=10)
        cache.set("key1", {"data": "value1"})
        assert cache.get("key1") == {"data": "value1"}

    def test_missing_key_returns_none(self):
        cache = LRUCache(max_items=10, ttl_seconds=10)
        assert cache.get("nonexistent") is None

    def test_eviction_on_max_items(self):
        """LRU eviction should remove the least recently used item."""
        cache = LRUCache(max_items=2, ttl_seconds=10)
        cache.set("a", 1)
        cache.set("b", 2)

        # Access 'a' to make it recently used
        cache.get("a")

        # Add 'c' — should evict 'b' (least recently used)
        cache.set("c", 3)

        assert cache.get("a") == 1
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3

    def test_ttl_expiry(self):
        """Expired entries should not be returned."""
        cache = LRUCache(max_items=10, ttl_seconds=0.1)
        cache.set("key1", "value1")

        import time
        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_lru_promotes_on_get(self):
        """Accessing a key should move it to most-recently-used."""
        cache = LRUCache(max_items=3, ttl_seconds=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access 'a' — it becomes MRU
        cache.get("a")

        # Add 'd' — should evict 'b' (now LRU)
        cache.set("d", 4)

        assert cache.get("a") == 1
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3
        assert cache.get("d") == 4
