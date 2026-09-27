from pydantic import BaseModel

from app.schemas.document.entities.document import DocumentVisibility


class UpdateDocumentRequest(BaseModel):
    visibility: DocumentVisibility