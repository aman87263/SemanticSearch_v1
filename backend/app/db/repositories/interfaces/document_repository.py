from abc import ABC, abstractmethod

from app.schemas.document import Document


class IDocumentRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[Document]:
        pass

    @abstractmethod
    def get_by_id(self, document_id: str) -> Document | None:
        pass

    @abstractmethod
    def get_by_hash(self, file_hash: str) -> Document | None:
        pass

    @abstractmethod
    def add(self, document: Document) -> None:
        pass

    @abstractmethod
    def update(self, document: Document) -> None:
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        pass