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


@lru_cache
def get_settings() -> Settings:

    loader = ConfigurationLoader()

    return Settings(
        environment=loader._environment,
        document=DocumentSettings(
            **loader.load_yaml(
                "document.yaml"
            )
        ),
        storage=StorageSettings(
            **loader.load_yaml(
                "storage.yaml"
            )
        ),
    )


settings = get_settings()