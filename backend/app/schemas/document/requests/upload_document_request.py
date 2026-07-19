from fastapi import UploadFile
from pydantic import BaseModel


class UploadDocumentRequest(BaseModel):
    file: UploadFile