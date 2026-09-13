from enum import Enum
from pydantic import BaseModel


class RoleName(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Role(BaseModel):
    name: RoleName


class Permission(BaseModel):
    code: str
