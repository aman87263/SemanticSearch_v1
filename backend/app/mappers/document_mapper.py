from app.schemas.document.responses.document_response import DocumentResponse
from app.schemas.document.entities.document import Document

class DocumentMapper:

    @staticmethod
    def to_response(document: Document) -> DocumentResponse:

        return DocumentResponse(
            id=document.id,
            file_name=document.file_name,
            size=document.size,
            status=document.status,
            upload_progress=document.upload_progress,
            processing_progress=document.processing_progress,
            uploaded_at=document.uploaded_at,
        )