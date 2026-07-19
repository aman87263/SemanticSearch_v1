from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from app.dependencies.document import get_document_service
from app.services.document.document_service import DocumentService
from app.schemas.common.api_response import ApiResponse
from app.schemas.document.responses.document_response import DocumentResponse
from app.core.response_factory import success
from app.schemas.document.requests.upload_document_request import (
    UploadDocumentRequest,
)
from app.schemas.document.responses.upload_document_response import (
    UploadDocumentResponse,
)
from app.schemas.document.entities.document import DocumentStatus

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "",
    response_model=ApiResponse[list[DocumentResponse]],
)
def get_documents(
    service: Annotated[  # This is where dependency injection happens, we are injecting the DocumentService into the route handler
        DocumentService,
        Depends(get_document_service),
    ],
):
    documents = service.get_documents()
    return success(data=documents)


@router.post(
    "",
    response_model=ApiResponse[UploadDocumentResponse],
)
async def upload_document(
    file: UploadFile,
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    request = UploadDocumentRequest(file=file)

    document = await service.upload_document(request)
    document.document.status = DocumentStatus.COMPLETED
    document.document.processing_progress = 100

    return success(data=document)


@router.delete(
    "/{document_id}",
    response_model=ApiResponse[bool],
)
async def delete_document(
    document_id: UUID,
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    deleted = await service.delete_document(document_id)

    return ApiResponse[bool](
        success=deleted,
        data=deleted,
    )
