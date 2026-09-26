from uuid import UUID

import psycopg
from app.schemas.document.entities.document import Document, DocumentStatus
from app.db.repositories.interfaces.document_repository import IDocumentRepository


class PostgresDocumentRepository(IDocumentRepository):

    def __init__(self, database_url: str):
        self._database_url = database_url

    def add(self, document: Document) -> None:
        query = """
            INSERT INTO documents (
                id,
                name,
                size,
                file_hash,
                storage_key,
                uploaded_at,
                status,
                progress,
                chunk_count,
                owner_id,
                uploader_email,
                uploader_name,
                visibility
            )
            VALUES (
                %(id)s,
                %(name)s,
                %(size)s,
                %(file_hash)s,
                %(storage_key)s,
                %(uploaded_at)s,
                %(status)s,
                %(progress)s,
                %(chunk_count)s,
                %(owner_id)s,
                %(uploader_email)s,
                %(uploader_name)s,
                %(visibility)s
            );
        """

        params = {
            "id": document.id,
            "name": document.name,
            "size": document.size,
            "file_hash": document.file_hash,
            "storage_key": document.storage_key,
            "uploaded_at": document.uploaded_at,
            "status": document.status.value,
            "progress": document.upload_progress,
            "chunk_count": document.chunk_count,
            "owner_id": document.owner_id,
            "uploader_email": document.uploader_email,
            "uploader_name": document.uploader_name,
            "visibility": document.visibility.value,
        }

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
            connection.commit()

    def get_all(self) -> list[Document]:
        query = """
            SELECT
                id,
                name,
                size,
                file_hash,
                storage_key,
                uploaded_at,
                status,
                progress,
                chunk_count,
                owner_id
            FROM documents
            ORDER BY uploaded_at DESC;
        """

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

        return [self._to_document(row) for row in rows]

    def get_by_owner(self, owner_id: str) -> list[Document]:
        query = """
            SELECT
                id,
                name,
                size,
                file_hash,
                storage_key,
                uploaded_at,
                status,
                progress,
                chunk_count,
                owner_id
            FROM documents
            WHERE owner_id = %(owner_id)s
            ORDER BY uploaded_at DESC;
        """

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, {"owner_id": owner_id})
                rows = cursor.fetchall()

        return [self._to_document(row) for row in rows]

    def get_by_id(self, document_id: UUID) -> Document | None:
        query = """
            SELECT
                id,
                name,
                size,
                file_hash,
                storage_key,
                uploaded_at,
                status,
                progress,
                chunk_count
            FROM documents
            WHERE id = %(id)s;
        """

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, {"id": document_id})
                row = cursor.fetchone()

        if row is None:
            return None

        return self._to_document(row)

    def delete(self, document_id: UUID) -> bool:
        query = """
            DELETE FROM documents
            WHERE id = %(id)s;
        """

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"id": document_id})
                deleted = cursor.rowcount > 0

            connection.commit()

        return deleted

    def get_by_hash_and_owner(self, file_hash: str, owner_id: str) -> Document | None:
        query = """
            SELECT
                id,
                name,
                size,
                file_hash,
                storage_key,
                uploaded_at,
                status,
                progress,
                chunk_count,
                owner_id
            FROM documents
            WHERE file_hash = %(file_hash)s AND owner_id = %(owner_id)s
            LIMIT 1;
        """

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(
                    query,
                    {"file_hash": file_hash, "owner_id": owner_id},
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return self._to_document(row)

    def update(self, document: Document) -> None:
        query = """
            UPDATE documents
            SET
                name = %(name)s,
                size = %(size)s,
                file_hash = %(file_hash)s,
                storage_key = %(storage_key)s,
                uploaded_at = %(uploaded_at)s,
                status = %(status)s,
                progress = %(progress)s,
                chunk_count = %(chunk_count)s,
                owner_id = %(owner_id)s,
                uploader_email = %(uploader_email)s,
                uploader_name = %(uploader_name)s,
                visibility = %(visibility)s
            WHERE id = %(id)s;
        """

        params = {
            "id": document.id,
            "name": document.name,
            "size": document.size,
            "file_hash": document.file_hash,
            "storage_key": document.storage_key,
            "uploaded_at": document.uploaded_at,
            "status": document.status.value,
            "progress": document.upload_progress,
            "chunk_count": document.chunk_count,
            "owner_id": document.owner_id,
            "uploader_email": document.uploader_email,
            "uploader_name": document.uploader_name,
            "visibility": document.visibility.value,
        }

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)

            connection.commit()

    @staticmethod
    def _to_document(row) -> Document:
        return Document(
            id=row["id"],
            name=row["name"],
            size=row["size"],
            file_hash=row["file_hash"],
            storage_key=row["storage_key"],
            uploaded_at=row["uploaded_at"],
            status=DocumentStatus(row["status"]),
            upload_progress=row["progress"],
            chunk_count=row["chunk_count"],
            owner_id=row.get("owner_id"),
            uploader_email=row.get("uploader_email"),
            uploader_name=row.get("uploader_name"),
        )
