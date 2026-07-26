from typing import Annotated

from fastapi import Depends

from app.dependencies.extraction import get_text_extractor_factory
from app.services.document.document_processing_pipeline import (
    DocumentProcessingPipeline,
)
from app.services.document.extraction.text_extractor_factory import (
    TextExtractorFactory,
)
from app.services.chunking.chunking_service import ChunkingService
from app.dependencies.chunking import get_chunking_service
from app.dependencies.embedding import get_embedding_service
from app.services.embedding.embedding_service import EmbeddingService


def get_document_processing_pipeline(
    extractor_factory: Annotated[
        TextExtractorFactory,
        Depends(get_text_extractor_factory),
    ],
    chunking_service: Annotated[
        ChunkingService,
        Depends(get_chunking_service),
    ],
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
) -> DocumentProcessingPipeline:

    return DocumentProcessingPipeline(
        extractor_factory=extractor_factory,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
    )
