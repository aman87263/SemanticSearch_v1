from app.schemas.document.entities.document import Document, DocumentStatus
from app.services.document.extraction.text_extractor_factory import (
    TextExtractorFactory,
)
from app.core.settings import settings
from pathlib import Path

from app.services.chunking.chunking_service import ChunkingService


class DocumentProcessingPipeline:
    """
    Coordinates the complete document processing workflow.

    Workflow:
        1. Extract text
        2. Chunk text
        3. Generate embeddings
        4. Store embeddings
        5. Update document status
    """

    def __init__(
        self,
        extractor_factory: TextExtractorFactory,
        chunking_service: ChunkingService,
    ):
        self._extractor_factory = extractor_factory
        self._chunking_service = chunking_service
    async def process(
        self,
        document: Document,
    ) -> None:
        """
        Process a document after it has been uploaded.

        NOTE:
        Currently only performs text extraction.
        Chunking, embeddings and vector storage will be
        added in subsequent milestones.
        """

        extension = document.name.rsplit(".", 1)[-1]

        extractor = self._extractor_factory.get_extractor(extension)

        extracted_text = extractor.extract(Path(settings.storage.upload_directory) / document.storage_key)

        # Temporary output until chunking is implemented.
        print("=" * 80)
        print(f"Extracted {len(extracted_text)} characters")
        print(extracted_text[:1000])
        print("=" * 80)

        # TODO:
        chunks = self._chunking_service.chunk(document.id, extracted_text)
        # embeddings = await self._embedding_service.generate(chunks)
        # await self._vector_store.store(document.id, embeddings)
        # await self._document_repository.mark_completed(document.id)
