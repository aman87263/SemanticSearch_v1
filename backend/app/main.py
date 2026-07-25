from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from app.api.routes import router as api_router
except ModuleNotFoundError:  # pragma: no cover
    from .api.routes import router as api_router

from app.core.response_factory import failure
from app.schemas.common.api_error import ApiError
from app.schemas.common.error_codes import ErrorCode

app = FastAPI(
    title="RAG Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    message = str(exc)
    code = ErrorCode.INVALID_FILE_TYPE

    if "maximum size" in message.lower():
        code = ErrorCode.INVALID_FILE_TYPE

    return JSONResponse(
        status_code=400,
        content=failure(
            error=ApiError(
                code=code,
                message=message,
            )
        ).model_dump(),
    )
