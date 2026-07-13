from typing import TypeVar

from app.schemas.common.api_error import ApiError
from app.schemas.common.api_metadata import ApiMetadata
from app.schemas.common.api_response import ApiResponse

T = TypeVar("T")


def success(data: T) -> ApiResponse[T]:
    return ApiResponse(
        success=True,
        data=data,
        metadata=ApiMetadata.create(),
    )

def failure(error: ApiError) -> ApiResponse[None]:
    return ApiResponse(
        success=False,
        error=error,
        metadata=ApiMetadata.create(),
    )