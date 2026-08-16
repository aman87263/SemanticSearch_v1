from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.reranking.interfaces.i_reranker import IReranker


class RerankerService:

    def __init__(self, provider: IReranker):
        self._provider = provider

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:

        if not chunks:
            return []

        return await self._provider.rerank(
            query=query,
            chunks=chunks,
        )