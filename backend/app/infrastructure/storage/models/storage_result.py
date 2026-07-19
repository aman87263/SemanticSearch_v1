from pydantic import BaseModel


class StorageResult(BaseModel):

    storage_key: str

    size: int

    provider: str