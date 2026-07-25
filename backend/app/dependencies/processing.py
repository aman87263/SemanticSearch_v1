from typing import Annotated

from fastapi import Depends

from app.dependencies.extraction import get_text_extractor_factory
from app.services.document.document_processing_pipeline import (
    DocumentProcessingPipeline,
)
from app.services.document.extraction.text_extractor_factory import (
    TextExtractorFactory,
)


def get_document_processing_pipeline(   
    extractor_factory: Annotated[
        TextExtractorFactory,
        Depends(get_text_extractor_factory),
    ],
) -> DocumentProcessingPipeline:

    return DocumentProcessingPipeline(
        extractor_factory=extractor_factory,
    )