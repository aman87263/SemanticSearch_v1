from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO

from app.core.settings import settings
from app.infrastructure.storage.models.storage_result import StorageResult
from app.infrastructure.storage.providers.storage_provider import (
    IStorageProvider,
)


class LocalStorageProvider(IStorageProvider):

    async def upload(
        self,
        stream: BinaryIO,
        storage_key: str,
    ) -> StorageResult:

        upload_directory = Path(settings.storage.upload_directory)

        destination = upload_directory / storage_key

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with destination.open("wb") as output:
            copyfileobj(stream, output)

        stream.seek(0)

        return StorageResult(
            storage_key=storage_key,
            size=destination.stat().st_size,
            provider="local",
        )
