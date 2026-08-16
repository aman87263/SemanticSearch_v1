from typing_extensions import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.questionanswer import get_question_answer_service
from app.schemas.chat.chat_request import QuestionRequest
from app.schemas.chat.chat_response import QuestionResponse
from app.services.question_answering.question_answering_service import (
    QuestionAnsweringService,
)

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
    question_answering_service: Annotated[
        QuestionAnsweringService,
        Depends(get_question_answer_service),
    ],
):
    result = await question_answering_service.answer(
        query=request.query,
        limit=request.limit,
        document_id=request.document_id,
    )

    return QuestionResponse(
        answer=result.answer,
        sources=result.context.items,
    )
