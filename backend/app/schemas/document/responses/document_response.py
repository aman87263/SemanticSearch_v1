from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.app.schemas.document.entities.document import DocumentStatus



class DocumentResponse(BaseModel):
    id: UUID
    file_name: str
    size: int
    status: DocumentStatus
    upload_progress: int
    processing_progress: int
    uploaded_at: datetime