"""Shared cache generation state for cross-module invalidation.

This module provides a single source of truth for the search pipeline generation.
Bumping the generation makes all old cache entries unreachable without deleting
individual keys — the core invalidation strategy from semanticAdditions.md §4, §22.

Implements both Redis-backed (durable/shared across workers) and process-local
fallback for when Redis is unavailable.
"""

import logging
import os
import threading
from contextlib import contextmanager

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis key for persistent generation counter
_REDIS_GENERATION_KEY = "search:generation"
_GENERATION_TTL = 86400  # 24 hours
_BUMP_GENERATION_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
    redis.call('SET', KEYS[1], ARGV[1], 'NX')
end
local generation = redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], ARGV[2])
return generation
"""

# Process-wide generation counter (thread-safe, fallback when Redis unavailable)
# Initialized from cache.search_generation config on first read
_generation = 1
_lock = threading.Lock()
_initialized = False

# Cached Redis client (lazy-loaded)
_redis_client: redis.Redis | None = None


async def _get_redis_client() -> redis.Redis | None:
    """Lazy-load Redis client for generation persistence."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        await _redis_client.ping()
        return _redis_client
    except Exception as e:
        logger.debug(f"Redis unavailable for generation persistence: {e}")
        _redis_client = None
        return None


def _init_from_config() -> int:
    """Initialize the process-local generation from cache.search_generation config.
    
    Only runs once per process. Returns the configured value if the Redis key
    doesn't exist yet, otherwise the Redis value takes precedence (via async_get_generation).
    """
    global _generation, _initialized
    if _initialized:
        return _generation
    
    try:
        from app.core.settings import settings
        config_gen = getattr(settings.cache, 'search_generation', 1)
    except Exception:
        config_gen = 1
    
    with _lock:
        _generation = config_gen
        _initialized = True
        return _generation


def _ensure_initialized() -> int:
    """Ensure the generation counter is initialized, return current value."""
    if not _initialized:
        _init_from_config()
    with _lock:
        return _generation


async def _ensure_initialized_async() -> int:
    """Ensure initialized, then check Redis for authoritative value."""
    _ensure_initialized()
    return await async_get_generation()


def get_generation() -> int:
    """Return the current cache generation (synchronous)."""
    return _ensure_initialized()


async def async_get_generation() -> int:
    """Return the current cache generation, checking Redis first."""
    r = await _get_redis_client()
    if r is not None:
        try:
            val = await r.get(_REDIS_GENERATION_KEY)
            if val is not None:
                gen = int(val)
                with _lock:
                    if _generation != gen:
                        _generation = gen
                return gen
        except Exception as e:
            logger.debug(f"Failed to read generation from Redis: {e}")
    
    return get_generation()


async def bump_generation() -> int:
    """Increment and return the new cache generation.
    
    Persists to Redis if available, otherwise updates process-local counter.
    This ensures all workers see the bump immediately when Redis is available.
    On the first bump, ensures the new generation is always strictly greater
    than the current value (whether from config or Redis).
    """
    global _generation
    
    # Ensure we're initialized from config
    _ensure_initialized()
    
    # Try Redis first for durability
    r = await _get_redis_client()
    if r is not None:
        try:
            new_val = int(
                await r.eval(
                    _BUMP_GENERATION_SCRIPT,
                    1,
                    _REDIS_GENERATION_KEY,
                    str(_ensure_initialized()),
                    str(_GENERATION_TTL),
                )
            )
            with _lock:
                _generation = new_val
            return new_val
        except Exception as e:
            logger.warning(f"Failed to bump generation in Redis; using local counter: {e}")
    
    # Fallback to process-local (less durable)
    with _lock:
        _generation += 1
        return _generation


def set_generation(value: int) -> int:
    """Set the generation to a specific value (for testing).
    
    This is synchronous-only and only updates the process-local counter.
    For async contexts, use async_set_generation().
    """
    global _generation
    with _lock:
        _generation = value
        return _generation


async def async_set_generation(value: int) -> int:
    """Set the generation to a specific value (for testing), persisting to Redis."""
    global _generation
    
    with _lock:
        _generation = value
    
    r = await _get_redis_client()
    if r is not None:
        try:
            await r.set(_REDIS_GENERATION_KEY, str(value))
            await r.expire(_REDIS_GENERATION_KEY, _GENERATION_TTL)
        except Exception as e:
            logger.debug(f"Failed to set generation in Redis: {e}")
    
    return value


@contextmanager
def generation_scope(new_value: int):
    """Context manager to temporarily set the generation (for testing).
    
    Note: This is synchronous-only and does not persist to Redis.
    Use async_async for testing in async contexts.
    """
    global _generation
    with _lock:
        old = _generation
        _generation = new_value
    try:
        yield
    finally:
        with _lock:
            _generation = old