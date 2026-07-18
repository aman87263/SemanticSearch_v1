from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from backend.app.infrastructure.storage.models.storage_result import StorageResult


class IStorageProvider(ABC):

    @abstractmethod
    async def upload(
        self,
        stream: BinaryIO,
        destination: str,
    ) -> StorageResult:
        """
        Uploads the stream.

        Returns the physical storage path/identifier.
        """
        pass
