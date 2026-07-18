from typing import BinaryIO

from backend.app.infrastructure.storage.models.storage_result import StorageResult


class DocumentStorageService:

    async def store(
        self,
        stream: BinaryIO,
        file_name: str,
    ) -> StorageResult: ...
