from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiMetadata(BaseModel):
    request_id: UUID
    timestamp: datetime