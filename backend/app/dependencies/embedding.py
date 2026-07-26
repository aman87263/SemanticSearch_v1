from typing_extensions import Annotated
from fastapi import Depends
from app.core.settings import settings
from app.services.embedding.providers.i_embedding_provider import IEmbeddingProvider

from app.services.embedding.embedding_service import EmbeddingService
from app.services.embedding.embedding_factory import EmbeddingFactory


def get_embedding_provider() -> IEmbeddingProvider:
    return EmbeddingFactory.create(
        provider_name=settings.embedding.provider,
        model_name=settings.embedding.model_name,
    )


def get_embedding_service(
    provider: Annotated[
        IEmbeddingProvider,
        Depends(get_embedding_provider),
    ],
) -> EmbeddingService:
    """
    Returns an instance of the embedding service.
    """
    return EmbeddingService(provider=provider)
