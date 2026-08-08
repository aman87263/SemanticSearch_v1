from fastapi import Depends

from app.services.embedding.embedding_service import EmbeddingService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.retrieval.vector_search import VectorSearch

from app.dependencies.embedding import get_embedding_service
from app.dependencies.vector import get_vector_store_service
from app.services.vectorstore.vector_store_service import VectorStoreService


def get_vector_search(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
) -> VectorSearch:

    return VectorSearch(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
    )


def get_retrieval_service(
    vector_search: VectorSearch = Depends(get_vector_search),
) -> RetrievalService:

    return RetrievalService(
        vector_search=vector_search,
    )
