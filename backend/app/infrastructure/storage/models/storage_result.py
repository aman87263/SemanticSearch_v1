from pydantic import BaseModel


class StorageResult(BaseModel):

    path: str

    size: int

    provider: str