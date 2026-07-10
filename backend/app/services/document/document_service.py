from app.db.repositories.document_repository import MemoryDocumentRepository
from app.db.repositories.interfaces.document_repository import IDocumentRepository


class DocumentService:

    def __init__(
        self,
        repository: IDocumentRepository,
    ):
        self._repository = repository

    def get_documents(self):
        return self._repository.get_all()

    def upload_document(self, request):
        ...

    def delete_document(self, document_id: str):
        ...

    def get_document(self, document_id: str):
        return self._repository.get_by_id(document_id)