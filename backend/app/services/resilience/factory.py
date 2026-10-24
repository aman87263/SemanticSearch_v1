"""Resilience factory for creating configured resilience policies from settings.

This module bridges the gap between the resilience configuration in settings
and the actual provider calls. It creates ResiliencePolicy instances for
each external provider type (embedding, LLM, reranker).
"""

from app.core.settings import settings
from app.services.resilience.circuit_breaker import ResiliencePolicy


def create_embedding_resilience_policy() -> ResiliencePolicy:
    """Create a resilience policy for embedding providers from settings."""
    r = settings.resilience
    return ResiliencePolicy(
        name="embedding",
        timeout_sec=r.timeout_sec,
        max_concurrent=r.max_concurrent,
        retry_attempts=r.retry_attempts,
        retry_base_delay=r.retry_base_delay,
        failure_threshold=r.failure_threshold,
        recovery_timeout_sec=r.recovery_timeout_sec,
        half_open_max_calls=r.half_open_max_calls,
    )


def create_llm_resilience_policy() -> ResiliencePolicy:
    """Create a resilience policy for LLM providers from settings."""
    r = settings.resilience
    return ResiliencePolicy(
        name="llm",
        timeout_sec=r.timeout_sec,
        max_concurrent=r.max_concurrent,
        retry_attempts=r.retry_attempts,
        retry_base_delay=r.retry_base_delay,
        failure_threshold=r.failure_threshold,
        recovery_timeout_sec=r.recovery_timeout_sec,
        half_open_max_calls=r.half_open_max_calls,
    )


def create_reranker_resilience_policy() -> ResiliencePolicy:
    """Create a resilience policy for reranker providers from settings."""
    r = settings.resilience
    return ResiliencePolicy(
        name="reranker",
        timeout_sec=r.timeout_sec,
        max_concurrent=r.max_concurrent,
        retry_attempts=r.retry_attempts,
        retry_base_delay=r.retry_base_delay,
        failure_threshold=r.failure_threshold,
        recovery_timeout_sec=r.recovery_timeout_sec,
        half_open_max_calls=r.half_open_max_calls,
    )