from functools import lru_cache

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


class Settings(BaseModel):
    environment: str
    document: DocumentSettings
    storage: StorageSettings
    chunking: ChunkingSettings
    embedding: EmbeddingSettings


@lru_cache
def get_settings() -> Settings:
    loader = ConfigurationLoader()

    doc_cfg = loader.load_yaml("document.yaml") or {}
    storage_cfg = loader.load_yaml("storage.yaml") or {}
    chunk_cfg = loader.load_yaml("chunking.yaml") or {}
    embedding_cfg = loader.load_yaml("embedding.yaml") or {}

    # chunking.yaml uses a nested top-level key `chunking: {...}` in base files
    if "chunking" in chunk_cfg:
        chunk_cfg = chunk_cfg["chunking"]

    return Settings(
        environment=loader._environment,
        document=DocumentSettings(**doc_cfg),
        storage=StorageSettings(**storage_cfg),
        chunking=ChunkingSettings(**chunk_cfg),
        embedding=EmbeddingSettings(**embedding_cfg),
    )


settings = get_settings()