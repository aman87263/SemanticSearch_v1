from app.services.document.extraction.interfaces.i_text_extractor import ITextExtractor


class TxtExtractor(ITextExtractor):

    def extract(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
