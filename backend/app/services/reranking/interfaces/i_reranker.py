from abc import ABC, abstractmethod

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk


class IReranker(ABC):

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]: ...
