from uuid import UUID, uuid4

from app.db.repositories.memory_document_repository import MemoryDocumentRepository
from app.db.repositories.interfaces.document_repository import IDocumentRepository
from app.mappers.document_mapper import DocumentMapper
from app.services.document.document_storage_service import DocumentStorageService
from app.services.document.duplicate_detection_service import DuplicateDetectionService
from app.services.document.file_hash_service import FileHashService
from app.services.document.file_validation_service import FileValidationService
from app.schemas.document.requests.upload_document_request import UploadDocumentRequest
from app.schemas.document.responses.document_response import DocumentResponse
from app.schemas.document.entities.document import Document, DocumentStatus, DocumentVisibility
from datetime import datetime

from app.schemas.document.responses.upload_document_response import (
    UploadDocumentResponse,
)
from app.schemas.document.upload_outcome import UploadOutcome
from app.services.document.document_processing_pipeline import (
    DocumentProcessingPipeline,
)
from app.dependencies import document


class DocumentService:

    def __init__(
        self,
        repository: IDocumentRepository,
        validation_service: FileValidationService,
        hash_service: FileHashService,
        duplicate_service: DuplicateDetectionService,
        storage_service: DocumentStorageService,
        processing_pipeline: DocumentProcessingPipeline,
    ):
        self._repository = repository
        self._validation_service = validation_service
        self._hash_service = hash_service
        self._duplicate_service = duplicate_service
        self._storage_service = storage_service
        self._processing_pipeline = processing_pipeline

    def get_documents(self, user_id: str | None = None, is_admin: bool = False):
        if is_admin:
            documents = self._repository.get_all()
        elif user_id:
            # User sees their own documents + all public documents from other users
            own_docs = self._repository.get_by_owner(user_id)
            public_docs = self._repository.get_public()
            # Combine and deduplicate (in case user owns some public docs)
            doc_map = {doc.id: doc for doc in own_docs}
            for doc in public_docs:
                if doc.id not in doc_map:
                    doc_map[doc.id] = doc
            documents = list(doc_map.values())
        else:
            documents = self._repository.get_public()
        return [DocumentMapper.to_response(doc) for doc in documents]

    async def upload_document(
        self, request: UploadDocumentRequest, user_id: str, uploader_email: str | None = None, uploader_name: str | None = None, visibility: DocumentVisibility = DocumentVisibility.PRIVATE
    ) -> UploadDocumentResponse:
        print(f"DEBUG SERVICE START: visibility = {visibility}, type = {type(visibility)}")
        print(f"DEBUG SERVICE START: user_id = {user_id}")
        print(f"DEBUG SERVICE START: uploader_email = {uploader_email}")
        print(f"DEBUG SERVICE START: uploader_name = {uploader_name}")

        file = request.file

        # 1. Validate
        self._validation_service.validate(file)

        # 2. Calculate hash
        file_hash = self._hash_service.calculate_hash(file.file)

        # 3. Check duplicate (per-user)
        existing = self._duplicate_service.find_duplicate(file_hash, user_id)

        if existing:
            return UploadDocumentResponse(
                outcome=UploadOutcome.DUPLICATE,
                document=DocumentMapper.to_response(existing),
            )

        # 4. Store file
        storage_result = await self._storage_service.store(
            stream=file.file,
            original_file_name=file.filename,
        )

        # 5. Create domain entity
        document = Document(
            id=uuid4(),
            name=file.filename,
            size=storage_result.size,
            file_hash=file_hash,
            storage_key=storage_result.storage_key,
            uploaded_at=datetime.utcnow(),
            status=DocumentStatus.UPLOADING,
            upload_progress=100,
            processing_progress=0,
            chunk_count=None,
            visibility=visibility,
        )

        # 6. Persist
        document.owner_id = user_id
        document.uploader_email = uploader_email
        document.uploader_name = uploader_name
        self._repository.add(document)

        embedded_chunks_count = await self._processing_pipeline.process(document)

        document.chunk_count = embedded_chunks_count
        document.processing_progress = 100
        document.status = DocumentStatus.COMPLETED
        self._repository.update(document)

        # 7. Return DTO
        return UploadDocumentResponse(
            outcome=UploadOutcome.CREATED,
            document=DocumentMapper.to_response(document),
        )

    async def delete_document(
        self,
        document_id: UUID,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> bool:

        document = self._repository.get_by_id(document_id)

        if not document:
            return False

        # Check permissions: only uploader or admin can delete
        if not is_admin and document.owner_id != user_id:
            return False

        await self._storage_service.delete(document.storage_key)

        return self._repository.delete(document_id)

    def get_document(self, document_id: UUID):
        document = self._repository.get_by_id(document_id)
        if document is None:
            return None
        return DocumentMapper.to_response(document)

    async def update_document_visibility(
        self,
        document_id: UUID,
        visibility: DocumentVisibility,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> DocumentResponse | None:
        document = self._repository.get_by_id(document_id)

        if not document:
            return None

        # Check permissions: only uploader or admin can update visibility
        if not is_admin and document.owner_id != user_id:
            return None

        document.visibility = visibility
        self._repository.update(document)

        return DocumentMapper.to_response(document)
