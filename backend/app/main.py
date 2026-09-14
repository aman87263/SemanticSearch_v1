import os
from typing import Set

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

# Security middleware for session cookie validation
from starlette.middleware.base import BaseHTTPMiddleware

# Paths that don't require session validation
PUBLIC_PATHS: Set[str] = {
    "/auth/",
    "/auth/me",
    "/auth/keycloak/config",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# State-changing endpoints that require CSRF protection
CSRF_PROTECTED_PATHS: Set[str] = {
    "/api/auth/session",  # POST - create session
    "/api/auth/refresh",  # POST - refresh token
    "/api/auth/logout",   # POST - logout
}

# Allowed origins for CSRF validation
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
}

from app.dependencies.auth import get_session_from_cookie

class SessionValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip session validation for preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip session validation for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Validate session cookie for protected routes
        session = get_session_from_cookie(request)
        if not session:
            return JSONResponse(
                status_code=401,
                content=failure(
                    error=ApiError(
                        code="SESSION_INVALID",
                        message="Invalid or missing session",
                    )
                ).model_dump(),
            )
        
        # Add session info to request state for downstream use
        request.state.session = session
        
        response = await call_next(request)
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for cookie-authenticated state-changing endpoints.
    
    Validates Origin and Referer headers against allowed origins for POST/PUT/PATCH/DELETE
    requests to protected paths. This complements SameSite=Lax cookie protection.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only check CSRF for state-changing methods
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)
        
        # Only check CSRF for protected paths
        path = request.url.path
        if path not in CSRF_PROTECTED_PATHS: #not any(path.startswith(p) for p in CSRF_PROTECTED_PATHS):
            return await call_next(request)
        
        # Validate Origin header
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        
        # Check Origin header first (preferred)
        if origin:
            if not self._is_allowed_origin(origin):
                return JSONResponse(
                    status_code=403,
                    content=failure(
                        error=ApiError(
                            code="CSRF_INVALID_ORIGIN",
                            message="Invalid Origin header",
                        )
                    ).model_dump(),
                )
        # Fall back to Referer header
        elif referer:
            if not self._is_allowed_origin(referer):
                return JSONResponse(
                    status_code=403,
                    content=failure(
                        error=ApiError(
                            code="CSRF_INVALID_REFERER",
                            message="Invalid Referer header",
                        )
                    ).model_dump(),
                )
        # No Origin or Referer - reject for security
        else:
            return JSONResponse(
                status_code=403,
                content=failure(
                    error=ApiError(
                        code="CSRF_MISSING_ORIGIN",
                        message="Missing Origin or Referer header",
                    )
                ).model_dump(),
            )
        
        return await call_next(request)
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is in allowed list."""
        try:
            # Parse origin to get scheme + host
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            origin_base = f"{parsed.scheme}://{parsed.netloc}"
            return origin_base in ALLOWED_ORIGINS
        except Exception:
            return False



app.add_middleware(
    SessionValidationMiddleware,
)
app.add_middleware(
    CSRFProtectionMiddleware,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
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
