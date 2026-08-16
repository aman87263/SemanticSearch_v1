from functools import lru_cache

from app.core.settings import settings
from app.services.reranking.reranker_factory import RerankerFactory
from app.services.reranking.reranker_service import RerankerService


@lru_cache
def get_reranker_service() -> RerankerService | None:
    """Return a process-wide reranker service, or None when disabled."""
    if not settings.reranking.enabled:
        return None

    provider = RerankerFactory.create(
        provider_name=settings.reranking.provider,
        model_name=settings.reranking.model_name,
    )

    return RerankerService(provider)

