from fastapi import File, Form, UploadFile
from pydantic import BaseModel

from app.schemas.document.entities.document import DocumentVisibility


class UploadDocumentRequest(BaseModel):
    file: UploadFile = File(...)
    visibility: DocumentVisibility = Form(DocumentVisibility.PRIVATE)
