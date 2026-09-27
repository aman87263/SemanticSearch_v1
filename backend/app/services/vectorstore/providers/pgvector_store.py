import asyncio
import json

import psycopg
from uuid import UUID
from app.schemas.embedding.embedded_chunk import EmbeddedChunk
from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.vectorstore.i_vector_store import IVectorStore


class PgVectorStore(IVectorStore):
    def __init__(self, database_url: str):
        self._database_url = database_url

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        if not chunks:
            return

        await asyncio.to_thread(self._upsert_sync, chunks)

    def _upsert_sync(self, chunks: list[EmbeddedChunk]) -> None:
        query = """
            INSERT INTO document_chunks (
                id,
                document_id,
                chunk_index,
                text,
                token_count,
                metadata,
                embedding
            )
            VALUES (
                %(id)s,
                %(document_id)s,
                %(chunk_index)s,
                %(text)s,
                %(token_count)s,
                %(metadata)s::jsonb,
                %(embedding)s::vector
            )
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                token_count = EXCLUDED.token_count,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding;
        """

        rows = [
            {
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.index,
                "text": chunk.text,
                "token_count": chunk.metadata.get(
                    "token_count",
                    len(chunk.text.split()),
                ),
                "metadata": json.dumps(chunk.metadata),
                "embedding": self._vector_to_string(chunk.vector),
            }
            for chunk in chunks
        ]

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                # cursor.execute("SELECT current_database(), current_schema()")
                # print(cursor.fetchone())
                cursor.executemany(query, rows)

            connection.commit()

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[RetrievedChunk]:
        return await asyncio.to_thread(
            self._search_sync,
            query_vector,
            limit,
            document_id,
            user_id,
            is_admin,
        )

    def _search_sync(
        self,
        query_vector: list[float],
        limit: int,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[RetrievedChunk]:
        if is_admin:
            # Admin can see all documents
            where_clause = """
            WHERE (
                %(document_id)s::uuid IS NULL
                OR chunks.document_id = %(document_id)s::uuid
            )
            """
        elif user_id:
            # Authenticated users can see their own private documents AND public documents
            where_clause = """
            WHERE (
                (%(document_id)s::uuid IS NULL
                OR chunks.document_id = %(document_id)s::uuid)
                AND (
                    documents.owner_id = %(user_id)s
                    OR documents.visibility = 'PUBLIC'
                )
            )
            """
        else:
            # Anonymous users can only see public documents
            where_clause = """
            WHERE (
                (%(document_id)s::uuid IS NULL
                OR chunks.document_id = %(document_id)s::uuid)
                AND documents.visibility = 'PUBLIC'
            )
            """

        query = f"""
        SELECT
            chunks.id,
            chunks.document_id,
            documents.name AS document_name,
            chunks.chunk_index,
            chunks.text,
            chunks.token_count,
            chunks.metadata,
            1 - (chunks.embedding <=> %(query_vector)s::vector) AS similarity
        FROM document_chunks AS chunks
        LEFT JOIN documents
            ON documents.id = chunks.document_id
        {where_clause}
        ORDER BY chunks.embedding <=> %(query_vector)s::vector
        LIMIT %(limit)s;
        """

        params = {
            "query_vector": self._vector_to_string(query_vector),
            "limit": limit,
            "document_id": document_id,
            "user_id": user_id,
        }

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Vector search: user_id={user_id}, is_admin={is_admin}, document_id={document_id}")
        logger.info(f"Query: {query}")
        logger.info(f"Params: {params}")

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.info(f"Vector search returned {len(rows)} rows")

        return [
            RetrievedChunk(
                id=row["id"],
                document_id=row["document_id"],
                index=row["chunk_index"],
                text=row["text"],
                token_count=row["token_count"],
                metadata=row["metadata"],
                similarity=float(row["similarity"]),
                document_name=row["document_name"],
            )
            for row in rows
        ]

    @staticmethod
    def _vector_to_string(vector: list[float]) -> str:
        return "[" + ",".join(str(value) for value in vector) + "]"
