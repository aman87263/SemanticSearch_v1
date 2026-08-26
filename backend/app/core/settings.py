from functools import lru_cache
import os

from pydantic import BaseModel

from app.core.configuration.configuration_loader import (
    ConfigurationLoader,
)


class UploadSettings(BaseModel):
    max_size_mb: int
    allowed_extensions: list[str]


class DuplicateSettings(BaseModel):
    allow_duplicates: bool

class ChunkingSettings(BaseModel):
    strategy: str
    chunk_size: int
    chunk_overlap: int

class EmbeddingSettings(BaseModel):
    provider: str
    model_name: str
    
class DocumentSettings(BaseModel):
    upload: UploadSettings
    duplicate: DuplicateSettings

class StorageSettings(BaseModel):
    provider: str
    upload_directory: str

class VectorStoreSettings(BaseModel):
    provider: str
    database_url: str

class RetrievalSettings(BaseModel):
    default_limit: int
    candidate_limit: int
    similarity_threshold: float

class RerankingSettings(BaseModel):
    enabled: bool = True
    provider: str
    model_name: str
    top_k: int | None = None

class LLMSettings(BaseModel):
    provider: str
    model: str
    temperature: float
    max_tokens: int


class Settings(BaseModel):
    environment: str
    document: DocumentSettings
    llm: LLMSettings
    vector_store: VectorStoreSettings
    retrieval: RetrievalSettings
    storage: StorageSettings
    chunking: ChunkingSettings
    embedding: EmbeddingSettings
    reranking: RerankingSettings


@lru_cache
def get_settings() -> Settings:
    loader = ConfigurationLoader()

    doc_cfg = loader.load_yaml("document.yaml") or {}
    storage_cfg = loader.load_yaml("storage.yaml") or {}
    chunk_cfg = loader.load_yaml("chunking.yaml") or {}
    embedding_cfg = loader.load_yaml("embedding.yaml") or {}
    vector_store_cfg = loader.load_yaml("vector_store.yaml") or {}
    retrieval_cfg = loader.load_yaml("retrieval.yaml") or {}
    reranking_cfg = loader.load_yaml("reranking.yaml") or {}
    llm_cfg = loader.load_yaml("llm.yaml") or {}

    # chunking.yaml uses a nested top-level key `chunking: {...}` in base files
    if "chunking" in chunk_cfg:
        chunk_cfg = chunk_cfg["chunking"]

    # retrieval.yaml uses a nested top-level key `retrieval: {...}` in base files
    if "retrieval" in retrieval_cfg:
        retrieval_cfg = retrieval_cfg["retrieval"]
    if "reranking" in reranking_cfg:
        reranking_cfg = reranking_cfg["reranking"]
    if "llm" in llm_cfg:
        llm_cfg = llm_cfg["llm"]

    vector_store_cfg["database_url"] = os.getenv(
        "DATABASE_URL",
        vector_store_cfg.get("database_url"),
    )
    storage_cfg["upload_directory"] = os.getenv(
        "UPLOAD_DIRECTORY",
        storage_cfg.get("upload_directory"),
    )
    llm_cfg["model"] = os.getenv("OLLAMA_MODEL", llm_cfg.get("model"))

    return Settings(
        environment=loader._environment,
        document=DocumentSettings(**doc_cfg),
        storage=StorageSettings(**storage_cfg),
        chunking=ChunkingSettings(**chunk_cfg),
        embedding=EmbeddingSettings(**embedding_cfg),
        vector_store=VectorStoreSettings(**vector_store_cfg),
        retrieval=RetrievalSettings(**retrieval_cfg),
        reranking=RerankingSettings(**reranking_cfg),
        llm=LLMSettings(**llm_cfg),
    )


settings = get_settings()