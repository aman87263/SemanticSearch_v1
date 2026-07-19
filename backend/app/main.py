from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.api.routes import router as api_router
except (
    ModuleNotFoundError
):  # pragma: no cover - supports running as a package from repo root
    from .api.routes import router as api_router

app = FastAPI(  # You should only have one:app = FastAPI()
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

app.include_router(
    api_router
)  # Include the API router that contains all the routes from different modules.

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


"""
