# Backend Architecture

This document describes the backend implementation and where to find major components in the codebase.

Overview
- Framework: FastAPI (application entrypoint: `backend/app/main.py`).
- App package: `backend/app` — contains API routes, business services, schemas, mappers, and provider implementations.
- Routers: `backend/app/api/routes` — primary API surface.
- Services: `backend/app/services` — business logic for chat, document ingestion, embedding, retrieval, and vector-store orchestration.
- Database & vector store: `backend/app/db` — connection, models, repositories; repository pattern is used to abstract storage.
- Background workers: `backend/app/workers` — indexing and long-running tasks.
- Configuration: `backend/app/core/settings.py` and `backend/app/config` — environment-driven configuration.

Notable implementation details
- CORS: `backend/app/main.py` configures allowed origins for local development (ports `5173`).
- Error handling: custom exception handler returns structured `ApiError` responses.
- Provider abstraction: LLMs, embeddings, and vector stores are wired via provider interfaces to keep the application vendor-agnostic.

Local development
1. From repository root, activate backend venv and install dependencies:

```powershell
cd backend
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the API (development mode):

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. API routes and documentation are available at `http://localhost:8000/docs` when the server is running.

Docker & deployment
- A `backend/Dockerfile` is included for containerized builds. Refer to [11-Deployment.md](11-Deployment.md) for deployment patterns.

Environment variables (recommended)
- `DATABASE_URL` — Postgres connection string.
- `VECTOR_PROVIDER` — selected vector database provider (e.g., pgvector, qdrant).
- `EMBEDDING_PROVIDER` — provider used for embeddings.
- `LLM_PROVIDER` — provider for language model calls.
- `STORAGE_URL` / `STORAGE_CONNECTION` — object storage connection string for uploaded files.
- `REDIS_URL` — for caching and background job coordination (if used).

If you want, I can extract the exact environment keys used by `backend/app/core/settings.py` and add an example `.env` here.
