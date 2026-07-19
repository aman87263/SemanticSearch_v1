from pydantic import BaseModel

from app.schemas.document.responses.document_response import (
    DocumentResponse,
)
from app.schemas.document.upload_outcome import UploadOutcome


class UploadDocumentResponse(BaseModel):
    outcome: UploadOutcome
    document: DocumentResponse