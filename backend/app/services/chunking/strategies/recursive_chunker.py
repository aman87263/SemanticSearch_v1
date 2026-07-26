import re
from uuid import UUID, uuid4

from app.schemas.chunk.entities.chunk import Chunk
from app.services.chunking.strategies.i_chunking_strategy import (
    IChunkingStrategy,
)


class RecursiveChunkingStrategy(IChunkingStrategy):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be at least zero and smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document_id: UUID, text: str) -> list[Chunk]:
        text = text.strip()

        if not text:
            return []

        pieces = self._split_recursively(
            text,
            separators=[
                r"\n\s*\n",  # paragraphs
                r"\n",  # lines
                r"(?<=[.!?])\s+",  # sentences
                r"\s+",  # words
            ],
        )

        contents = self._merge_with_overlap(pieces)

        return [
            Chunk(
                id=uuid4(),
                document_id=document_id,
                index=index,
                text=content,
                token_count=self._estimate_token_count(content),
                metadata={
                    "chunking_strategy": "recursive",
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                },
            )
            for index, content in enumerate(contents)
        ]

    def _split_recursively(
        self,
        text: str,
        separators: list[str],
    ) -> list[str]:
        text = text.strip()

        if len(text) <= self.chunk_size:
            return [text] if text else []

        if not separators:
            # Last fallback: force fixed-size character chunks.
            return [
                text[index : index + self.chunk_size].strip()
                for index in range(0, len(text), self.chunk_size)
                if text[index : index + self.chunk_size].strip()
            ]

        separator = separators[0]
        parts = [part.strip() for part in re.split(separator, text) if part.strip()]

        # Separator did not split the text: try the next fallback.
        if len(parts) <= 1:
            return self._split_recursively(text, separators[1:])

        result: list[str] = []

        for part in parts:
            result.extend(self._split_recursively(part, separators[1:]))

        return result

    def _merge_with_overlap(self, pieces: list[str]) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_length = 0

        for piece in pieces:
            extra_length = len(piece) + (1 if current else 0)

            if current and current_length + extra_length > self.chunk_size:
                chunks.append(" ".join(current))

                # Keep the final pieces of the previous chunk as context.
                overlap: list[str] = []
                overlap_length = 0

                for previous_piece in reversed(current):
                    added_length = len(previous_piece) + (1 if overlap else 0)

                    if overlap_length + added_length > self.chunk_overlap:
                        break

                    overlap.insert(0, previous_piece)
                    overlap_length += added_length

                current = overlap
                current_length = len(" ".join(current))

                # Remove overlap pieces if the new piece would exceed the limit.
                while current and current_length + 1 + len(piece) > self.chunk_size:
                    current.pop(0)
                    current_length = len(" ".join(current))

            current.append(piece)
            current_length = len(" ".join(current))

        if current:
            chunks.append(" ".join(current))

        return chunks

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        # Free approximation. Replace with a model tokenizer later if needed.
        return len(text.split())
