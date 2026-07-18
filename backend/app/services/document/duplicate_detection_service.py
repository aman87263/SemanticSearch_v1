from backend.app.db.repositories.interfaces.document_repository import (
    IDocumentRepository,
)
from backend.app.schemas.document.entities.document import Document


class DuplicateDetectionService:

    def __init__(
        self,
        repository: IDocumentRepository,
    ):
        self._repository = repository

    def find_duplicate(
        self,
        file_hash: str,
    ) -> Document | None:
        return self._repository.get_by_hash(file_hash)
