from uuid import UUID

from pydantic import BaseModel


class ContextItem(BaseModel):
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    text: str
    score: float | None = None
    rerank_score: float | None = None


class RetrievalContext(BaseModel):
    items: list[ContextItem]
    text: str
