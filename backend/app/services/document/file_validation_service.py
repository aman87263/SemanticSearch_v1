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

        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)

        max_size_bytes = settings.document.upload.max_size_mb * 1024 * 1024

        if size_bytes > max_size_bytes:
            raise ValueError(
                f"File exceeds maximum size of {settings.document.upload.max_size_mb} MB."
            )
