from app.services.document.extraction.interfaces.i_text_extractor import ITextExtractor
from app.services.document.extraction.markdown_extractor import MarkdownExtractor
from app.services.document.extraction.pdf_extractor import PdfExtractor
from app.services.document.extraction.docx_extractor import DocxExtractor
from app.services.document.extraction.txt_extractor import TxtExtractor

class TextExtractorFactory:
    def get_extractor(self, file_extension: str) -> ITextExtractor:
        if file_extension == "md":
            return MarkdownExtractor()
        elif file_extension == "pdf":
            return PdfExtractor()
        elif file_extension == "docx":
            return DocxExtractor()
        elif file_extension == "txt":
            return TxtExtractor()
        else:
            raise ValueError(f"No extractor available for file type: {file_extension}")