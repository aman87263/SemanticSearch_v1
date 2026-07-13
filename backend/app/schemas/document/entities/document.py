from datetime import datetime
from typing import Literal

from pydantic import BaseModel


DocumentStatus = Literal[
    "queued",
    "uploading",
    "processing",
    "ready",
    "failed",
]


class Document(BaseModel):
    id: str
    name: str
    size: int
    uploaded_at: datetime
    status: DocumentStatus
    progress: int = 0
    chunk_count: int | None = None
    file_hash: str