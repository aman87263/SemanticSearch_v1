"""Embedding provider factory with fallback routing support.

Implements semanticAdditions.md §18:
  EmbeddingService → ProviderRouter → Primary / Fallback providers
"""

import logging

from app.services.embedding.providers.i_embedding_provider import (
    IEmbeddingProvider,
)
from app.services.embedding.providers.sentence_transformer_provider import (
    SentenceTransformerProvider,
)
from app.services.llm.providers.provider_router import (
    ProviderResiliencePolicy,
    ProviderRouter,
)

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """Creates embedding providers and optional router with fallback."""

    @staticmethod
    def create(provider_name: str, model_name: str) -> IEmbeddingProvider:
        """Create a single embedding provider (backward compatible)."""
        return EmbeddingFactory._create_provider(provider_name, model_name)

    @staticmethod
    def _create_provider(provider_name: str, model_name: str) -> IEmbeddingProvider:
        """Internal provider creation."""
        if provider_name == "sentence_transformer":
            return SentenceTransformerProvider(model_name)
        # Future: add OpenAI, Cohere, etc.
        raise ValueError(f"Unsupported embedding provider: {provider_name}")

    @staticmethod
    def create_with_fallback(
        primary_name: str,
        primary_model: str,
        fallback_name: str | None = None,
        fallback_model: str | None = None,
    ) -> tuple[ProviderRouter, IEmbeddingProvider]:
        """Create a ProviderRouter with primary and optional fallback provider.

        Returns (router, primary_provider) so existing code using just the primary
        still works, while the router exposes fallback capability.

        Raises:
            ValueError: If fallback model produces a different vector dimension
                        than the primary model (both must match the index).
        """
        # Create primary provider
        primary_provider = EmbeddingFactory._create_provider(primary_name, primary_model)
        primary_dim = _get_model_dimension(primary_provider)
        if primary_dim is None:
            logger.warning(
                f"Could not determine vector dimension for primary model '{primary_model}'. "
                f"Fallback compatibility check will be skipped."
            )

        primary_policy = _create_provider_policy(f"embedding:{primary_name}")

        providers = [primary_provider]
        policies = [primary_policy]

        # Add fallback if specified
        if fallback_name and fallback_model:
            fallback_provider = EmbeddingFactory._create_provider(fallback_name, fallback_model)
            fallback_dim = _get_model_dimension(fallback_provider)

            # Validate dimension compatibility
            if primary_dim is not None and fallback_dim is not None:
                if primary_dim != fallback_dim:
                    raise ValueError(
                        f"Embedding fallback dimension mismatch: "
                        f"primary model '{primary_model}' produces {primary_dim} dimensions, "
                        f"but fallback model '{fallback_model}' produces {fallback_dim} dimensions. "
                        f"Both must match the index dimension."
                    )
                logger.info(
                    f"Embedding fallback validated: both primary and fallback produce "
                    f"{primary_dim}-dimensional vectors."
                )

            fallback_policy = _create_provider_policy(
                f"embedding:{fallback_name}:fallback"
            )
            providers.append(fallback_provider)
            policies.append(fallback_policy)

        router = ProviderRouter(providers=providers, policies=policies)

        # Link fallback policy if we have one
        if len(policies) > 1:
            policies[0].set_fallback(policies[1])

        return router, primary_provider


def create_embedding_router_from_settings() -> tuple[ProviderRouter, IEmbeddingProvider]:
    """Create embedding router from application settings.

    Reads from settings.embedding and optional settings.embedding.fallback
    """
    from app.core.settings import settings

    primary_name = settings.embedding.provider
    primary_model = settings.embedding.model_name

    # Check for fallback config (optional extension)
    fallback_name = getattr(settings.embedding, 'fallback_provider', None)
    fallback_model = getattr(settings.embedding, 'fallback_model', None)

    return EmbeddingFactory.create_with_fallback(
        primary_name=primary_name,
        primary_model=primary_model,
        fallback_name=fallback_name,
        fallback_model=fallback_model,
    )


def _create_provider_policy(name: str) -> ProviderResiliencePolicy:
    """Build a routed provider policy using configured resilience settings."""
    from app.core.settings import settings

    config = settings.resilience
    return ProviderResiliencePolicy(
        name=name,
        timeout_sec=config.timeout_sec,
        max_concurrent=config.max_concurrent,
        retry_attempts=config.retry_attempts,
        retry_base_delay=config.retry_base_delay,
        failure_threshold=config.failure_threshold,
        recovery_timeout_sec=config.recovery_timeout_sec,
        half_open_max_calls=config.half_open_max_calls,
    )


def _get_model_dimension(provider: IEmbeddingProvider) -> int | None:
    """Get the output vector dimension of an embedding provider.

    Returns None if the dimension cannot be determined.
    """
    # For sentence-transformer providers, inspect the model
    if hasattr(provider, '_model') and provider._model is not None:
        try:
            return provider._model.get_sentence_embedding_dimension()
        except Exception:
            pass
    # Could add dimension checks for other provider types here
    return None