from fastapi import APIRouter

from .health import router as health_router
from .document import router as document_router
from .search import router as search_router

router = APIRouter(prefix="/api", tags=["API"])

router.include_router(health_router)
router.include_router(document_router)
router.include_router(search_router)