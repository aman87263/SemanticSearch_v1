from app.services.vectorstore.i_vector_store import IVectorStore
from app.services.vectorstore.providers.pgvector_store import PgVectorStore


class VectorStoreFactory:
    @staticmethod
    def create(
        provider_name: str,
        database_url: str,
    ) -> IVectorStore:
        if provider_name == "pgvector":
            return PgVectorStore(database_url=database_url)

        raise ValueError(f"Unsupported vector-store provider: {provider_name}")
