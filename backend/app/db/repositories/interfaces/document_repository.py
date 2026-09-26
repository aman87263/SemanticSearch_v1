from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.document.entities.document import Document


class IDocumentRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[Document]:
        pass

    @abstractmethod
    def get_by_id(self, document_id: UUID) -> Document | None:
        pass

    @abstractmethod
    def get_by_hash_and_owner(self, file_hash: str, owner_id: str) -> Document | None:
        pass

    @abstractmethod
    def get_by_owner(self, owner_id: str) -> list[Document]:
        pass

    @abstractmethod
    def add(self, document: Document) -> None:
        pass

    @abstractmethod
    def update(self, document: Document) -> None:
        pass

    @abstractmethod
    def delete(self, document_id: UUID) -> bool:
        pass