from abc import ABC, abstractmethod

from app.schemas.embedding.embedded_chunk import EmbeddedChunk
from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from uuid import UUID

class IVectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        pass
