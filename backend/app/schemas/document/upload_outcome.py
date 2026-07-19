from enum import StrEnum


class UploadOutcome(StrEnum):
    CREATED = "created"
    DUPLICATE = "duplicate"