# SemanticSearch_v1

## Run locally

Copy `.env.example` to `.env`, then start the local Ollama stack:

```powershell
docker compose up --build
```

The local stack uses the model configured in `backend/app/config/base/llm.yaml`.

## Run with Groq

Set `GROQ_API_KEY` in `.env` and start the production override:

```powershell
docker compose -f docker-compose.yml -f docker-compose.production.yml up --build
```

The production override selects `backend/app/config/production/llm.yaml` and does not start Ollama. Keep API keys out of source control; `.env` is ignored by Git.