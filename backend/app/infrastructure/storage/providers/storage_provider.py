from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.infrastructure.storage.models.storage_result import StorageResult
from app.infrastructure.storage.providers.storage_provider import (
    IStorageProvider,
)


class DocumentStorageService:

    def __init__(
        self,
        storage_provider: IStorageProvider,
    ):
        self._storage_provider = storage_provider

    async def store(
        self,
        stream: BinaryIO,
        original_file_name: str,
    ) -> StorageResult:

        extension = Path(original_file_name).suffix.lower()

        storage_key = f"documents/{uuid4()}{extension}"

        return await self._storage_provider.upload(
            stream,
            storage_key,
        )
