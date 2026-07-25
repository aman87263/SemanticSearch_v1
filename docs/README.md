# Project Documentation — SemanticSearch_v1

This folder contains the project documentation for the Enterprise AI Knowledge Platform (SemanticSearch_v1). The docs describe the architecture, design decisions, operational guidance, and roadmap for the code in this repository.

Quick summary
- **Frontend:** React + Vite (see `frontend/`) using Material UI and React Router.
- **Backend:** FastAPI (see `backend/app`) providing REST and websocket endpoints.
- **Vector Store / DB:** PostgreSQL + pgvector is the intended vector backend (provider-agnostic design).
- **Processing:** Background workers handle ingestion, chunking, and indexing (see `backend/app/workers`).
- **Providers:** LLM and embedding providers are abstracted behind provider interfaces.

Run locally (quick start)
- Backend (from repository root):

```powershell
cd backend
# activate virtualenv (example for PowerShell)
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Frontend:

```bash
cd frontend
npm install
npm run dev
```

Where to start in the docs
- [01-Vision.md](01-Vision.md) — project vision and guiding principles.
- [02-High-Level-Architecture.md](02-High-Level-Architecture.md) — system overview and logical layers.
- [04-Backend-Architecture.md](04-Backend-Architecture.md) — backend structure and run details.
- [05-Database-Architecture.md](05-Database-Architecture.md) — database design and vector store notes.
- [11-Deployment.md](11-Deployment.md) — deployment and Docker notes.

Notes
- The codebase is intentionally provider-agnostic; configuration controls which LLM, embedding, and vector database implementations are used. Review `backend/app/core/settings.py` and `backend/app/dependencies` for current environment variables and provider wiring.
- If you want, I can extend these docs with extracted environment variables, example `.env`, and a checklist for running end-to-end locally.
