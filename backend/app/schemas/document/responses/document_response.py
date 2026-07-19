from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.document.entities.document import DocumentStatus



class DocumentResponse(BaseModel):
    id: UUID
    name: str
    size: int
    status: DocumentStatus
    progress: int
    processing_progress: int
    uploadedAt: datetime