from app.services.embedding.providers.sentence_transformer_provider import (
    SentenceTransformerProvider,
)


class EmbeddingFactory:
    @staticmethod
    def create(provider_name: str, model_name: str):
        if provider_name == "sentence_transformer":
            return SentenceTransformerProvider(model_name)

        raise ValueError(f"Unsupported embedding provider: {provider_name}")
