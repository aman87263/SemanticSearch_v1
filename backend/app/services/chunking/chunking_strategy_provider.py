
from app.api.routes import settings
from app.services.chunking.strategies.i_chunking_strategy import IChunkingStrategy
from app.services.chunking.strategies.recursive_chunker import RecursiveChunkingStrategy


class ChunkingStrategyProvider:

    def get_strategy(self) -> IChunkingStrategy:
        if settings.chunking.strategy == "recursive":
            return RecursiveChunkingStrategy()

        raise ValueError(...)