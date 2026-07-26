from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.chunk.entities.chunk import Chunk


class IChunkingStrategy(ABC):

    @abstractmethod
    def chunk(
        self,
        document_id: UUID,
        text: str,
    ) -> list[Chunk]:
        pass
