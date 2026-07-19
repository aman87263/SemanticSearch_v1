from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    id: UUID

    # File info
    name: str
    size: int
    file_hash: str
    storage_key: str

    # Lifecycle
    uploaded_at: datetime
    status: DocumentStatus

    # Progress tracking
    upload_progress: int = 0
    processing_progress: int = 0

    # AI processing
    chunk_count: int | None = None