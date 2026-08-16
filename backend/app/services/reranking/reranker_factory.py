from app.services.reranking.interfaces.i_reranker import IReranker
from app.services.reranking.providers.sentence_transformer_reranker import (
    SentenceTransformerReranker,
)


class RerankerFactory:
    @staticmethod
    def create(provider_name: str, model_name: str) -> IReranker:
        if provider_name == "sentence_transformer":
            return SentenceTransformerReranker(model_name=model_name)

        raise ValueError(f"Unsupported reranking provider: {provider_name}")
