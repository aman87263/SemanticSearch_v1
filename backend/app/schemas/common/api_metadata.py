from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiMetadata(BaseModel):
    request_id: UUID
    timestamp: datetime

    @classmethod
    def create(cls) -> "ApiMetadata":
        return cls(
            request_id=UUID(int=0),  # Placeholder for request ID generation
            timestamp=datetime.utcnow(),
        )