from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, require_authenticated_user
from app.dependencies.retrieval import get_retrieval_service
from app.services.retrieval.retrieval_service import RetrievalService
from app.schemas.search.search_request import SearchRequest
from app.schemas.search.search_response import SearchResponse

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "",
    response_model=SearchResponse,
)
async def search(
    request: SearchRequest,
    _user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    retrieval_service: Annotated[
        RetrievalService,
        Depends(get_retrieval_service),
    ],
) -> SearchResponse:

    results = await retrieval_service.retrieve(
        query=request.query,
        limit=request.limit,
        document_id=request.document_id,
    )

    return SearchResponse(
        results=results,
    )
