from uuid import UUID
from app.schemas.chunk.entities.chunk import Chunk
from app.services.chunking.strategies.i_chunking_strategy import IChunkingStrategy


class ChunkingService:

    def __init__(
        self,
        strategy: IChunkingStrategy,
    ):
        self._strategy = strategy

    def chunk(
        self,
        document_id: UUID,
        text: str,
    ) -> list[Chunk]:

        return self._strategy.chunk(
            document_id,
            text,
        )
