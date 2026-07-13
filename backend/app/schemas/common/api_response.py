from typing import Generic, TypeVar

from pydantic import BaseModel

from app.schemas.common.api_error import ApiError
from app.schemas.common.api_metadata import ApiMetadata

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ApiError | None = None
    metadata: ApiMetadata | None = None