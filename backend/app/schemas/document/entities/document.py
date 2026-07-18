from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


DocumentStatus = Literal[
    "queued",
    "uploading",
    "processing",
    "ready",
    "failed",
]


class Document(BaseModel):
    id: UUID
    name: str
    size: int
    file_hash: str
    storage_key: str
    uploaded_at: datetime
    status: DocumentStatus
    progress: int = 0
    chunk_count: int | None = None