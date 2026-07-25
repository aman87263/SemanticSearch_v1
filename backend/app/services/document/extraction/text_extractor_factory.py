from app.services.document.extraction.interfaces.i_text_extractor import ITextExtractor
from app.services.document.extraction.pdf_extractor import PdfExtractor
from app.services.document.extraction.docx_extractor import DocxExtractor
from app.services.document.extraction.txt_extractor import TxtExtractor
from app.services.document.extraction.markdown_extractor import MarkdownExtractor


class TextExtractorFactory:

    def __init__(
        self,
        extractors: dict[str, ITextExtractor],
    ):
        self._extractors = extractors

    def get_extractor(self, extension: str) -> ITextExtractor:
        extension = extension.lower().lstrip(".")

        extractor = self._extractors.get(extension)

        if extractor is None:
            raise ValueError(f"No extractor registered for '{extension}'")

        return extractor

    _extractors: dict[str, type[ITextExtractor]] = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
        "txt": TxtExtractor,
        "md": MarkdownExtractor,
    }
