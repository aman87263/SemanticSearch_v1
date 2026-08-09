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

        return results[:final_limit]
