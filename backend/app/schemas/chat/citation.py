from uuid import UUID

from pydantic import BaseModel


class Citation(BaseModel):
    document_id: UUID
    document_name: str | None = None
    chunk_id: UUID
    chunk_index: int
    similarity: float | None = None
    rerank_score: float | None = None