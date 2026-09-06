## Render deployment

The repository includes a `render.yaml` Blueprint for the free Render web service and frontend services. Render can deploy both services automatically from the repository's `main` branch; no separate GitHub Actions CD workflow is required.

### External services

Create a Supabase Free project and enable the `vector` extension. Use its connection string as `DATABASE_URL`. Set `GROQ_API_KEY` to a Groq API key.

### Blueprint setup

1. In Render, create a new Blueprint from this repository and select `render.yaml`.
2. Set `DATABASE_URL`, `GROQ_API_KEY`, and `CORS_ORIGINS` for `semanticsearch-backend`.
3. Set `VITE_API_BASE_URL` for `semanticsearch-frontend` to the backend URL followed by `/api`, for example `https://semanticsearch-backend.onrender.com/api`.
4. Set `CORS_ORIGINS` to the frontend URL, for example `https://semanticsearch-frontend.onrender.com`.
5. Enable auto-deploy from `main` for both services.

### Free-tier limitation

Uploaded documents currently use local filesystem storage. `/tmp/uploads` is ephemeral on Render, so uploaded files can be lost when the service restarts or redeploys. Use durable object storage before treating the deployment as production-ready.
