"""Module-level singleton resilience policies for long-lived state.

Resilience state (circuit breaker counters, semaphore permits) must persist
across requests to be effective. FastAPI's @lru_cache on dependency functions
and request-scoped policies would reset this state on every request.

These singleton policies are created once at module load time and reused
across all requests and services.
"""

from app.core.settings import settings
from app.services.resilience.circuit_breaker import ResiliencePolicy
from app.services.resilience.factory import create_llm_resilience_policy


def get_embedding_resilience_policy() -> ResiliencePolicy:
    """Singleton embedding resilience policy with persistent circuit breaker state."""
    return _embedding_policy


def get_llm_resilience_policy() -> ResiliencePolicy:
    """Singleton LLM resilience policy with persistent circuit breaker state."""
    return _llm_policy


def get_reranker_resilience_policy() -> ResiliencePolicy:
    """Singleton reranker resilience policy with persistent circuit breaker state."""
    return _reranker_policy


# Create singletons at module load
_embedding_policy = create_llm_resilience_policy()
_llm_policy = create_llm_resilience_policy()
_reranker_policy = create_llm_resilience_policy()