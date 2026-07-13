from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.document import get_document_service
from app.services.document.document_service import DocumentService
from backend.app.schemas.common.api_response import ApiResponse
from backend.app.schemas.document.responses.document_response import DocumentResponse
from backend.core.response_factory import success

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "/",
    response_model=ApiResponse[list[DocumentResponse]],
)
def get_documents(
    service: Annotated[#This is where dependency injection happens, we are injecting the DocumentService into the route handler
        DocumentService,
        Depends(get_document_service),
    ],
):
    documents = service.get_documents()
    return success(data=documents)