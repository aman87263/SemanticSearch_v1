from abc import ABC, abstractmethod
from typing import BinaryIO

from app.infrastructure.storage.models.storage_result import StorageResult


class IStorageProvider(ABC):

    @abstractmethod
    async def upload(
        self,
        stream: BinaryIO,
        storage_key: str,
    ) -> StorageResult:
        """
        Uploads a file stream to the configured storage.
        """
        pass