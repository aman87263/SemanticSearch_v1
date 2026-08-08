from typing_extensions import Annotated
from fastapi import Depends
from app.core.settings import settings
from app.services.vectorstore.i_vector_store import IVectorStore
from app.services.vectorstore.vector_store_service import VectorStoreService
from app.services.vectorstore.vector_factory import VectorStoreFactory

def get_vector_store_provider() -> IVectorStore:
    return VectorStoreFactory.create(
        provider_name=settings.vector_store.provider,
        database_url=settings.vector_store.database_url,
    )

def get_vector_store_service(provider: Annotated[
        IVectorStore,
        Depends(get_vector_store_provider),
    ]) -> VectorStoreService:
    """
    Returns an instance of the vector store service.
    """
    return VectorStoreService(provider=provider)