from typing import Annotated
from fastapi import Depends

from app.db.repositories.interfaces.idocument_repository import (
    IDocumentRepository,
)
from app.db.repositories.document_repository import (
    MemoryDocumentRepository,
)
from app.services.document.document_service import DocumentService


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
    return DocumentService(repository)