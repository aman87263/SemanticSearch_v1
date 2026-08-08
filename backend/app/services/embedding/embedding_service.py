from app.schemas.chunk.entities.chunk import Chunk
from app.schemas.embedding.embedded_chunk import EmbeddedChunk
from app.services.embedding.providers.i_embedding_provider import (
    IEmbeddingProvider,
)


class EmbeddingService:
    def __init__(self, provider: IEmbeddingProvider):
        self._provider = provider

    async def generate(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        if not chunks:
            return []

        vectors = await self._provider.embed([chunk.text for chunk in chunks])

        if len(vectors) != len(chunks):
            raise RuntimeError(
                "Embedding provider returned a different number of vectors."
            )

        return [
            EmbeddedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                index=chunk.index,
                text=chunk.text,
                vector=vector,
                metadata=chunk.metadata,
                token_count=chunk.token_count,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
