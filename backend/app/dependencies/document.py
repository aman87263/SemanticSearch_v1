from typing import Annotated
from fastapi import Depends

from app.db.repositories.interfaces.document_repository import (
    IDocumentRepository,
)
from app.db.repositories.memory_document_repository import (
    MemoryDocumentRepository,
)
from app.services.document.document_service import DocumentService
from app.infrastructure.storage.providers.local_storage_provider import (
    LocalStorageProvider,
)
from app.services.document.document_storage_service import DocumentStorageService
from app.services.document.duplicate_detection_service import DuplicateDetectionService
from app.services.document.file_hash_service import FileHashService
from app.services.document.file_validation_service import FileValidationService

# -------------------------------------------------------------------------
# Repository
# -------------------------------------------------------------------------

# Singleton instance (temporary until PostgreSQL is introduced)
_document_repository = MemoryDocumentRepository()


def get_document_repository() -> IDocumentRepository:
    """
    Returns the application's document repository.

    Currently this is an in-memory implementation.
    Later this can be replaced with PostgreSQL, MongoDB,
    CosmosDB, etc. without changing the service layer.
    """
    return _document_repository


# -------------------------------------------------------------------------
# Service
# -------------------------------------------------------------------------


def get_document_service(
    repository: Annotated[
        IDocumentRepository,
        Depends(get_document_repository),
    ],
) -> DocumentService:
    """
    Returns a DocumentService with its dependencies injected.
    """
    storage_provider = LocalStorageProvider()

    storage_service = DocumentStorageService(storage_provider)

    return DocumentService(
        repository=repository,
        validation_service=FileValidationService(),
        hash_service=FileHashService(),
        duplicate_service=DuplicateDetectionService(repository),
        storage_service=storage_service,
    )
