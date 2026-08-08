from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.retrieval.vector_search import VectorSearch


class RetrievalService:

    def __init__(
        self,
        vector_search: VectorSearch,
    ):
        self._vector_search = vector_search

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedChunk]:

        if not query or not query.strip():
            return []

        return await self._vector_search.search(
            query=query,
            limit=limit,
        )
