from uuid import UUID

from app.schemas.embedding.embedded_chunk import EmbeddedChunk
from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.vectorstore.i_vector_store import IVectorStore


class VectorStoreService:
    def __init__(self, provider: IVectorStore):
        self._provider = provider

    async def store_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        await self._provider.upsert(chunks)

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        return await self._provider.search(query_vector, limit, document_id)
