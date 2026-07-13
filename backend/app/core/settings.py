from functools import lru_cache
import os
from pathlib import Path

import yaml
from pydantic import BaseModel


# ---------------------------------------------------------------------
# Configuration Models
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Configuration Loader
# ---------------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:

    environment = os.getenv("APP_ENVIRONMENT", "development")

    root = Path(__file__).resolve().parents[2]

    base_path = root / "config" / "base"
    env_path = root / "config" / environment

    def load_yaml(file_name: str) -> dict:

        result = {}

        base_file = base_path / file_name
        if base_file.exists():
            with open(base_file, "r", encoding="utf-8") as f:
                result.update(yaml.safe_load(f) or {})

        env_file = env_path / file_name
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                result.update(yaml.safe_load(f) or {})

        return result

    document = load_yaml("document.yaml")
    storage = load_yaml("storage.yaml")

    return Settings(
        environment=environment,
        document=DocumentSettings(**document),
        storage=StorageSettings(**storage),
    )


settings = get_settings()