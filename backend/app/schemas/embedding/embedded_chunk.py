from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EmbeddedChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    index: int
    text: str
    vector: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
