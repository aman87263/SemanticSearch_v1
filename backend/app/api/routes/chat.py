from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_current_user_optional, require_authenticated_user
from app.dependencies.questionanswer import get_question_answer_service
from app.schemas.chat.chat_request import QuestionRequest
from app.schemas.chat.chat_response import QuestionResponse
from app.services.question_answering.question_answering_service import (
    QuestionAnsweringService,
)
from app.services.chat.citation_service import CitationService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=QuestionResponse,
)
async def chat(
    request: QuestionRequest,
    user: Annotated[CurrentUser | None, Depends(get_current_user_optional)],
    question_answering_service: Annotated[
        QuestionAnsweringService,
        Depends(get_question_answer_service),
    ],
):
    is_admin = "ADMIN" in user.roles if user else False
    user_id = user.user_id if user else None
    result = await question_answering_service.answer(
        query=request.query,
        limit=request.limit,
        document_id=request.document_id,
        user_id=user_id,
        is_admin=is_admin,
    )

    return QuestionResponse(
        answer=result.answer,
        citations=CitationService().create(result.context.items),
    )
