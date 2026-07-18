from pathlib import Path

from fastapi import UploadFile

from app.core.settings import settings


class FileValidationService:

    def validate(self, file: UploadFile) -> None:
        """
        Validates an uploaded file.

        Raises:
            ValueError: If validation fails.
        """

        if file is None:
            raise ValueError("No file was provided.")

        if not file.filename:
            raise ValueError("Filename is required.")

        extension = Path(file.filename).suffix.lower().lstrip(".")

        if extension not in settings.document.upload.allowed_extensions:
            raise ValueError(f"File type '{extension}' is not supported.")
