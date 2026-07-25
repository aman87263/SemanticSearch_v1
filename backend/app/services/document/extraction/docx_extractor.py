from backend.app.services.document.extraction.interfaces.i_text_extractor import ITextExtractor
import docx

class DocxExtractor(ITextExtractor):

    def extract(self, file_path: str) -> str:
        document = docx.Document(file_path)
        full_text = []
        for para in document.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
