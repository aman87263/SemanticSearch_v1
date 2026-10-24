from app.services.embedding.providers.i_embedding_provider import IEmbeddingProvider

from app.services.embedding.embedding_service import EmbeddingService
from app.services.embedding.embedding_factory import create_embedding_router_from_settings


def get_embedding_provider() -> IEmbeddingProvider:
    _, provider = create_embedding_router_from_settings()
    return provider


def get_embedding_service() -> EmbeddingService:
    """
    Returns an instance of the embedding service with resilience policy.
    """
    router, provider = create_embedding_router_from_settings()
    return EmbeddingService(provider=provider, provider_router=router)
