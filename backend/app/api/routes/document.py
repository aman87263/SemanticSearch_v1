from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.document import get_document_service
from app.services.document.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get("/")
def get_documents(
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    return service.get_documents()