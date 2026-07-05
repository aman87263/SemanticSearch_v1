from fastapi import FastAPI

app = FastAPI(
    title="RAG Backend",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the RAG Backend!"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }