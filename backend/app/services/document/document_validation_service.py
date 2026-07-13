from fastapi import UploadFile


class DocumentValidationService:

    def validate(self, file: UploadFile) -> None:
        """
        Raises an exception if the file is invalid.
        """
        pass