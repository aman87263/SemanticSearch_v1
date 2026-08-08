from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    id: UUID
    document_id: UUID
    index: int
    text: str
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity: float
