from pydantic import BaseModel

from app.schemas.retrieval.retrieval_context import ContextItem


class QuestionResponse(BaseModel):
    answer: str
    sources: list[ContextItem]
