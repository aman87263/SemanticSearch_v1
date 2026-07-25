from uuid import UUID

from app.schemas.document.entities.document import Document
from app.db.repositories.interfaces.document_repository import IDocumentRepository


class MemoryDocumentRepository(IDocumentRepository):

    def __init__(self):
        self._documents: list[Document] = []

    def get_all(self):
        return self._documents

    def get_by_id(self, document_id: UUID):
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

    def update(self, document: Document):
        for index, existing in enumerate(self._documents):
            if existing.id == document.id:
                self._documents[index] = document
                return

    def delete(self, document_id: UUID):
        document = self.get_by_id(document_id)

        if document is None:
            return False

        self._documents.remove(document)

        return True
