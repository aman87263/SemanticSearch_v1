from app.db.repositories.document_repository import MemoryDocumentRepository
from app.db.repositories.interfaces.document_repository import IDocumentRepository
from backend.app.mappers.document_mapper import DocumentMapper


class DocumentService:

    def __init__(
        self,
        repository: IDocumentRepository,
    ):
        self._repository = repository

    def get_documents(self):
        documents = self._repository.get_all()
        return [DocumentMapper.to_response(doc) for doc in documents]

    def upload_document(self, request): ...

    def delete_document(self, document_id: str): ...

    def get_document(self, document_id: str):
        return DocumentMapper.to_response(self._repository.get_by_id(document_id))
