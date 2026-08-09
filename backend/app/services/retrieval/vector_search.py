from uuid import UUID

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.embedding.embedding_service import EmbeddingService
from app.services.vectorstore.vector_store_service import VectorStoreService


class VectorSearch:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store_service: VectorStoreService,
    ):
        self._embedding_service = embedding_service
        self._vector_store_service = vector_store_service

    async def search(
        self,
        query: str,
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:

        if not query or not query.strip():
            return []

        query_vector = await self._embedding_service.generate_query(query)

        return await self._vector_store_service.search(
            query_vector=query_vector,
            limit=limit,
            document_id=document_id,
        )
