from typing_extensions import Annotated

from fastapi import Depends

from app.core.settings import settings
from app.services.chunking.strategies.i_chunking_strategy import IChunkingStrategy
from app.services.chunking.strategies.recursive_chunker import RecursiveChunkingStrategy
from app.services.chunking.chunking_service import ChunkingService


def get_chunking_strategy() -> IChunkingStrategy:

    if settings.chunking.strategy == "recursive":
        return RecursiveChunkingStrategy(
            chunk_size=settings.chunking.chunk_size,
            chunk_overlap=settings.chunking.chunk_overlap,
        )

    raise ValueError(f"Unsupported chunking strategy: {settings.chunking.strategy}")


def get_chunking_service(
    strategy: Annotated[
        IChunkingStrategy,
        Depends(get_chunking_strategy),
    ],
) -> ChunkingService:

    return ChunkingService(
        strategy=strategy,
    )
