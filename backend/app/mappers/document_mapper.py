from app.schemas.document.responses.document_response import DocumentResponse
from app.schemas.document.entities.document import Document

class DocumentMapper:

    @staticmethod
    def to_response(document: Document) -> DocumentResponse:

        return DocumentResponse(
            id=document.id,
            name=document.name,
            size=document.size,
            status=document.status,
            progress=document.upload_progress,
            processing_progress=document.processing_progress,
            uploadedAt=document.uploaded_at,
        )