from uuid import uuid4

from app.db.repositories.memory_document_repository import MemoryDocumentRepository
from app.db.repositories.interfaces.document_repository import IDocumentRepository
from app.mappers.document_mapper import DocumentMapper
from app.services.document.document_storage_service import DocumentStorageService
from app.services.document.duplicate_detection_service import DuplicateDetectionService
from app.services.document.file_hash_service import FileHashService
from app.services.document.file_validation_service import FileValidationService
from app.schemas.document.requests.upload_document_request import UploadDocumentRequest
from app.schemas.document.responses.document_response import DocumentResponse
from app.schemas.document.entities.document import Document, DocumentStatus
from datetime import datetime


class DocumentService:

    def __init__(
        self,
        repository: IDocumentRepository,
        validation_service: FileValidationService,
        hash_service: FileHashService,
        duplicate_service: DuplicateDetectionService,
        storage_service: DocumentStorageService,
    ):
        self._repository = repository
        self._validation_service = validation_service
        self._hash_service = hash_service
        self._duplicate_service = duplicate_service
        self._storage_service = storage_service

    def get_documents(self):
        documents = self._repository.get_all()
        return [DocumentMapper.to_response(doc) for doc in documents]

    async def upload_document(self, request: UploadDocumentRequest) -> DocumentResponse:

        file = request.file

        # 1. Validate
        self._validation_service.validate(file)

        # 2. Calculate hash
        file_hash = self._hash_service.calculate_hash(file.file)

        # 3. Check duplicate
        existing = self._duplicate_service.find_duplicate(file_hash)

        if existing:
            return DocumentMapper.to_response(existing)

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
        )

        # 6. Persist
        self._repository.add(document)

        # 7. Return DTO
        return DocumentMapper.to_response(document)

    def delete_document(self, document_id: str): ...

    def get_document(self, document_id: str):
        return DocumentMapper.to_response(self._repository.get_by_id(document_id))
