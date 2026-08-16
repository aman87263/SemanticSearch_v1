from pydantic import BaseModel
from uuid import UUID


class QuestionRequest(BaseModel):
    query: str
    limit: int = 5
    document_id: UUID | None = None
