from fastapi import FastAPI

from app.api.routes import router as api_router

app = FastAPI(  # You should only have one:app = FastAPI()
    title="RAG Backend",
    version="1.0.0",
)

app.include_router(api_router)  # Include the API router that contains all the routes from different modules.

"""
FastAPI Application
        │
        ├── Health Router
        ├── Documents Router
        ├── Chat Router
        ├── Auth Router
        └── Settings Router
router = APIRouter(
    prefix="/health",
    tags=["Health"],
)
@router.get("")
@router.get("/version")

Now inside documents.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


Frontend

DocumentsPage

↓

DocumentProvider

↓

DocumentService

↓

Backend

Documents Router

↓

Document Service

↓

Document Repository
"""
