from backend.app.services.document.extraction.interfaces.i_text_extractor import ITextExtractor
import pypdf

class PdfExtractor(ITextExtractor):

    def extract(self, file_path: str) -> str:
        text = ""
        with open(file_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
