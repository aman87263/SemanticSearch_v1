from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException

from app.dependencies.auth import CurrentUser, require_authenticated_user
from app.dependencies.document import get_document_service
from app.services.document.document_service import DocumentService
from app.schemas.common.api_response import ApiResponse
from app.schemas.document.responses.document_response import DocumentResponse
from app.core.response_factory import success
from app.schemas.document.requests.upload_document_request import (
    UploadDocumentRequest,
)
from app.schemas.document.entities.document import DocumentVisibility
from app.schemas.document.requests.update_document_request import (
    UpdateDocumentRequest,
)
from app.schemas.document.responses.upload_document_response import (
    UploadDocumentResponse,
)
from app.services.document.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "",
    response_model=ApiResponse[list[DocumentResponse]],
)
def get_documents(
    user: Annotated[
        CurrentUser,
        Depends(require_authenticated_user),
    ],
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    is_admin = "ADMIN" in user.roles
    documents = service.get_documents(user_id=user.user_id, is_admin=is_admin)
    return success(data=documents)


@router.get(
    "/public",
    response_model=ApiResponse[list[DocumentResponse]],
)
def get_public_documents(
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    """Get all public documents (accessible without authentication)"""
    documents = service.get_documents(user_id=None, is_admin=False)
    return success(data=documents)


@router.post(
    "",
    response_model=ApiResponse[UploadDocumentResponse],
)
async def upload_document(
    *,
    file: UploadFile = File(...),
    visibility: str = Form("PRIVATE"),
    user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    # Convert string to enum
    try:
        visibility_enum = DocumentVisibility(visibility.upper())
    except ValueError:
        visibility_enum = DocumentVisibility.PRIVATE
    request = UploadDocumentRequest(file=file)

    document = await service.upload_document(
        request, 
        user_id=user.user_id,
        uploader_email=user.email,
        uploader_name=user.name,
        visibility=visibility_enum,
    )

    return success(data=document)


@router.delete(
    "/{document_id}",
    response_model=ApiResponse[bool],
)
async def delete_document(
    document_id: UUID,
    user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    is_admin = "ADMIN" in user.roles
    deleted = await service.delete_document(document_id, user_id=user.user_id, is_admin=is_admin)

    if not deleted:
        # Check if document exists but user doesn't have permission
        existing_doc = service.get_document(document_id)
        if existing_doc:
            raise HTTPException(status_code=403, detail="Only owner or admin can delete this document")
        raise HTTPException(status_code=404, detail="Document not found")

    return ApiResponse[bool](
        success=deleted,
        data=deleted,
    )


@router.patch(
    "/{document_id}/visibility",
    response_model=ApiResponse[DocumentResponse],
)
async def update_document_visibility(
    document_id: UUID,
    request: UpdateDocumentRequest,
    user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    is_admin = "ADMIN" in user.roles
    document = await service.update_document_visibility(
        document_id, 
        request.visibility,
        user_id=user.user_id,
        is_admin=is_admin
    )
    if not document:
        # Check if document exists but user doesn't have permission
        existing_doc = service.get_document(document_id)
        if existing_doc:
            raise HTTPException(status_code=403, detail="Only owner or admin can update visibility")
        raise HTTPException(status_code=404, detail="Document not found")
    return success(data=document)
