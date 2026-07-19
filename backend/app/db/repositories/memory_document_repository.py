from app.schemas.document.entities.document import Document
from app.db.repositories.interfaces.document_repository import IDocumentRepository
# from backend.app.schemas import document


class MemoryDocumentRepository(IDocumentRepository):

    def __init__(self):
        self._documents: list[Document] = []

    def get_all(self):
        return self._documents

    def get_by_id(self, document_id: str):
        return next(
            (document for document in self._documents if document.id == document_id),
            None,
        )

    def get_by_hash(self, file_hash: str):
        return next(
            (
                document
                for document in self._documents
                if document.file_hash == file_hash
            ),
            None,
        )

    def add(self, document):
        self._documents.append(document)

    def update(self, document):
        pass  # In a real implementation, you would update the document in the database.

    def delete(self, document_id: str):
        document = self.get_by_id(document_id)

        if document is None:
            return False

        self._documents.remove(document)

        return True
