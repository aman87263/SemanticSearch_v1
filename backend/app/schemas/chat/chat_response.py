from pydantic import BaseModel

from app.schemas.retrieval.retrieval_context import ContextItem
from app.schemas.chat.citation import Citation


class QuestionResponse(BaseModel):
    answer: str
    citations: list[Citation]
