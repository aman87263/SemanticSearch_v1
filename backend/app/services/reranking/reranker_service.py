from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.reranking.interfaces.i_reranker import IReranker
from app.services.resilience.circuit_breaker import ResiliencePolicy


class RerankerService:

    def __init__(
        self,
        provider: IReranker,
        resilience_policy: ResiliencePolicy | None = None,
    ):
        self._provider = provider
        self._resilience = resilience_policy

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:

        if not chunks:
            return []

        if self._resilience:
            return await self._resilience.execute(
                lambda: self._provider.rerank(query=query, chunks=chunks)
            )

        return await self._provider.rerank(
            query=query,
            chunks=chunks,
        )