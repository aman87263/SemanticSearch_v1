from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.retrieval.vector_search import VectorSearch
from app.core.settings import settings
from uuid import UUID


class RetrievalService:

    def __init__(
        self,
        vector_search: VectorSearch,
    ):
        self._vector_search = vector_search

    async def retrieve(
        self,
        query: str,
        limit: int | None = None,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:

        if not query or not query.strip():
            return []

        final_limit = limit if limit is not None else settings.retrieval.default_limit

        candidates = await self._vector_search.search(
            query=query,
            limit=settings.retrieval.candidate_limit,
            document_id=document_id,
        )

        results = [
            chunk
            for chunk in candidates
            if chunk.similarity >= settings.retrieval.similarity_threshold
        ]

        results = self._deduplicate_adjacent(results)

        return results[:final_limit]

    def _deduplicate_adjacent(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        # Higher-scoring chunks get priority.
        sorted_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.similarity,
            reverse=True,
        )

        selected: list[RetrievedChunk] = []
        seen_indices: dict[UUID, set[int]] = {}

        for chunk in sorted_chunks:
            doc_seen = seen_indices.setdefault(
                chunk.document_id,
                set(),
            )

            if any(
                index in doc_seen
                for index in (
                    chunk.index - 1,
                    chunk.index,
                    chunk.index + 1,
                )
            ):
                continue

            selected.append(chunk)
            doc_seen.add(chunk.index)

        return selected
