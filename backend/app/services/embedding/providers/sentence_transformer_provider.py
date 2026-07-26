import asyncio

from sentence_transformers import SentenceTransformer

from app.services.embedding.providers.i_embedding_provider import (
    IEmbeddingProvider,
)


class SentenceTransformerProvider(IEmbeddingProvider):
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)

        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        def encode() -> list[list[float]]:
            vectors = self._get_model().encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return vectors.tolist()

        return await asyncio.to_thread(encode)
