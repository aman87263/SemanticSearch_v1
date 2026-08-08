from pydantic import BaseModel

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk


class SearchResponse(BaseModel):
    results: list[RetrievedChunk]
