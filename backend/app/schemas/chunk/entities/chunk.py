from uuid import UUID
from typing import Any
from pydantic import BaseModel

class Chunk(BaseModel):

    id: UUID

    document_id: UUID

    index: int

    text: str

    token_count: int

    metadata: dict[str, Any] = {}