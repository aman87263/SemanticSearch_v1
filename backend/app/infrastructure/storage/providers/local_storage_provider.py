from typing import BinaryIO

from backend.app.infrastructure.storage.models.storage_result import StorageResult
from backend.app.infrastructure.storage.providers.storage_provider import (
    IStorageProvider,
)


class LocalStorageProvider(IStorageProvider):

    async def upload(
        self,
        stream: BinaryIO,
        destination: str,
    ) -> StorageResult: ...
