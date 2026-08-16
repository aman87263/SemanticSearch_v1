import asyncio

from sentence_transformers import CrossEncoder

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.reranking.interfaces.i_reranker import IReranker


class SentenceTransformerReranker(IReranker):

    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model: CrossEncoder | None = None

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(self._model_name)

        return self._model

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:

        if not chunks:
            return []

        def rerank_sync() -> list[RetrievedChunk]:
            model = self._get_model()

            pairs = [(query, chunk.text) for chunk in chunks]

            scores = model.predict(
                pairs,
                show_progress_bar=False,
            )

            reranked = []

            for chunk, score in zip(
                chunks,
                scores,
                strict=True,
            ):
                reranked.append(chunk.model_copy(update={"rerank_score": float(score)}))

            return sorted(
                reranked,
                key=lambda chunk: (
                    chunk.rerank_score
                    if chunk.rerank_score is not None
                    else float("-inf")
                ),
                reverse=True,
            )


        return await asyncio.to_thread(rerank_sync)
