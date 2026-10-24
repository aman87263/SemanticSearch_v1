"""Provider abstraction with resilience policy and fallback support.

Implements semanticAdditions.md §18 and §19:

  ProviderRouter
       ?
  +-----+--------+
  ?     ?        ?
OpenAI Groq  Local/Ollama

And:
  ProviderResiliencePolicy
   +-- timeout
   +-- semaphore
   +-- circuit breaker
   +-- retry
   +-- fallback

The provider implementation doesn't need to know about resilience logic —
it's separated cleanly into the router.
"""

import logging
from typing import Protocol, TypeVar

from app.services.resilience.circuit_breaker import ResiliencePolicy

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class IProvider(Protocol):
    """Provider protocol for embedding providers supported by this router."""

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class ProviderResiliencePolicy(ResiliencePolicy):
    """Resilience policy with fallback support for provider routing.

    Adds fallback capability on top of the base ResiliencePolicy:
      1. Try primary provider
      2. If circuit is OPEN or all retries fail, try fallback provider
    """

    def __init__(
        self,
        name: str,
        *,
        timeout_sec: float = 5.0,
        max_concurrent: int = 10,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        super().__init__(
            name=name,
            timeout_sec=timeout_sec,
            max_concurrent=max_concurrent,
            retry_attempts=retry_attempts,
            retry_base_delay=retry_base_delay,
            failure_threshold=failure_threshold,
            recovery_timeout_sec=recovery_timeout_sec,
            half_open_max_calls=half_open_max_calls,
        )
        self._fallback_policy: ProviderResiliencePolicy | None = None

    def set_fallback(self, fallback: "ProviderResiliencePolicy") -> None:
        """Set a fallback provider policy for when this one is unhealthy."""
        self._fallback_policy = fallback

    async def execute_with_fallback(
        self,
        primary_call,
        fallback_call,
        *args,
        **kwargs,
    ):
        """Execute with fallback: try primary, fall back on circuit open.

        Returns the result from whichever provider succeeds.
        Raises the last exception if both primary and fallback fail.
        """
        try:
            return await self.execute(primary_call, *args, **kwargs)
        except Exception as primary_exc:
            # If the circuit is open or all retries exhausted, try fallback
            if self._fallback_policy is not None:
                logger.info(
                    f"ProviderResiliencePolicy[{self._name}]: "
                    f"primary failed ({type(primary_exc).__name__}), "
                    f"attempting fallback"
                )
                try:
                    return await self._fallback_policy.execute(
                        fallback_call, *args, **kwargs
                    )
                except Exception as fallback_exc:
                    logger.error(
                        f"ProviderResiliencePolicy[{self._name}]: "
                        f"fallback also failed ({type(fallback_exc).__name__})"
                    )
                    raise fallback_exc
            raise primary_exc


class ProviderRouter:
    """Routes requests to the appropriate provider with resilience and fallback.

    Implements the ProviderRouter pattern from semanticAdditions.md §18:
      EmbeddingService → ProviderRouter → OpenAI / Groq / Local
    """

    def __init__(self, providers: list[IProvider], policies: list[ProviderResiliencePolicy]):
        if len(providers) != len(policies):
            raise ValueError("Providers and policies must be the same length")
        self._providers = list(zip(providers, policies))
        self._primary = self._providers[0] if self._providers else None

    @property
    def primary(self) -> IProvider:
        if self._primary is None:
            raise RuntimeError("No providers configured")
        return self._primary[0]

    def get_resilience_policy(self) -> ProviderResiliencePolicy:
        if self._primary is None:
            raise RuntimeError("No providers configured")
        return self._primary[1]

    def get_fallback(self) -> tuple[IProvider, ProviderResiliencePolicy] | None:
        """Return the fallback provider and its policy, if configured."""
        return self._providers[1] if len(self._providers) > 1 else None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed text with the primary provider and configured fallback."""
        if self._primary is None:
            raise RuntimeError("No providers configured")

        primary_provider, primary_policy = self._primary
        fallback = self.get_fallback()
        primary_call = lambda: primary_provider.embed(texts)

        if fallback is None:
            return await primary_policy.execute(primary_call)

        fallback_provider, _fallback_policy = fallback
        return await primary_policy.execute_with_fallback(
            primary_call,
            lambda: fallback_provider.embed(texts),
        )
