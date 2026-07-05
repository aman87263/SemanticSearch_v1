from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],  # Swagger groups endpoints by tags.
)


@router.get("") # becomes GET /health because of the prefix defined in the router and @router.get("/version") becomes GET /health/version
def health_check():
    return {"status": "healthy"}
