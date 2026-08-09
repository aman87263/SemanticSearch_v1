from pydantic import BaseModel, Field
from uuid import UUID

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=None, ge=1, le=50)
    document_id: UUID | None = None