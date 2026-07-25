from app.services.document.extraction.pdf_extractor import PdfExtractor
from app.services.document.extraction.docx_extractor import DocxExtractor
from app.services.document.extraction.txt_extractor import TxtExtractor
from app.services.document.extraction.markdown_extractor import MarkdownExtractor
from app.services.document.extraction.text_extractor_factory import TextExtractorFactory


def get_text_extractor_factory() -> TextExtractorFactory:
    return TextExtractorFactory(
        extractors={
            "pdf": PdfExtractor(),
            "docx": DocxExtractor(),
            "txt": TxtExtractor(),
            "md": MarkdownExtractor(),
        }
    )

