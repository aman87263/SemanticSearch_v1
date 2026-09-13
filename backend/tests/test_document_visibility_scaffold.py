from datetime import datetime
from uuid import uuid4

from app.schemas.document.entities.document import Document, DocumentStatus, DocumentVisibility


def test_document_schema_can_carry_owner_and_visibility_fields():
    doc = Document(
        id=uuid4(),
        name="sample.pdf",
        size=100,
        file_hash="abc-123",
        storage_key="uploads/sample.pdf",
        uploaded_at=datetime.utcnow(),
        status=DocumentStatus.COMPLETED,
        upload_progress=100,
        processing_progress=100,
        chunk_count=1,
        owner_id="user-123",
        visibility=DocumentVisibility.PRIVATE,
    )

    assert doc.owner_id == "user-123"
    assert doc.visibility == DocumentVisibility.PRIVATE
