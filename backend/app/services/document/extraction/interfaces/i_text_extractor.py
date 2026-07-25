from abc import ABC, abstractmethod


class ITextExtractor(ABC):

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """Extract plain text from a document."""
        pass