from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.document.entities.document import DocumentStatus, DocumentVisibility


class DocumentResponse(BaseModel):
    id: UUID
    name: str
    size: int
    status: DocumentStatus
    progress: int
    processing_progress: int
    uploadedAt: datetime
    chunkCount: int | None = None
    owner_id: str | None = None
    visibility: DocumentVisibility = DocumentVisibility.PRIVATE