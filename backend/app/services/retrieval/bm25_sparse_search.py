"""BM25 sparse search provider using PostgreSQL full-text search.

Implements the sparse/BM25 retrieval path described in semanticAdditions.md §10,
§11, and §12. Uses PostgreSQL's built-in tsvector/tsquery full-text search with
GIN indexing, avoiding the need for a separate Elasticsearch/OpenSearch cluster.

The search also respects document visibility/ownership, matching the same
authorization scopes used by the dense (pgvector) search.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

import psycopg

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk

logger = logging.getLogger(__name__)


class BM25SparseSearch:
    """Sparse retrieval using PostgreSQL FTS (tsvector/tsquery with BM25-style ranking).

    Requires a ``search_vector`` tsvector column on ``document_chunks`` and a
    GIN index on it. The ts_rank_cd function provides a BM25-like relevance
    score.
    """

    def __init__(self, database_url: str):
        self._database_url = database_url

    async def search(
        self,
        query: str,
        limit: int = 5,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[RetrievedChunk]:
        """Execute a BM25/tsvector search and return ranked chunks.

        Args:
            query: Raw user query text (will be converted to tsquery).
            limit: Maximum number of results.
            document_id: Optional filter to a specific document.
            user_id: Optional user ID for authorization scoping.
            is_admin: If True, bypass document visibility restrictions.
        """
        if not query or not query.strip():
            return []

        return await asyncio.to_thread(
            self._search_sync,
            query,
            limit,
            document_id,
            user_id,
            is_admin,
        )

    def _search_sync(
        self,
        query: str,
        limit: int,
        document_id: UUID | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[RetrievedChunk]:
        """Synchronous search implementation (runs in thread)."""

        if is_admin:
            where_clause = """
            WHERE (
                %(document_id)s::uuid IS NULL
                OR chunks.document_id = %(document_id)s::uuid
            )
            """
        elif user_id:
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
            where_clause = """
            WHERE (
                (%(document_id)s::uuid IS NULL
                OR chunks.document_id = %(document_id)s::uuid)
                AND documents.visibility = 'PUBLIC'
            )
            """

        query_sql = f"""
        WITH query_tsv AS (
            -- OR semantics over the query's lexemes, so a natural-language
            -- question ("why does payment tokenization work?") still matches
            -- a chunk containing only "payment tokenization". ts_rank_cd then
            -- ranks chunks matching more/rarer terms higher, which is the
            -- recall behaviour BM25 relies on. Stopword-only queries yield an
            -- empty tsquery and correctly match nothing.
            SELECT to_tsquery(
                'english',
                COALESCE(
                    (
                        SELECT string_agg(lexeme, ' | ')
                        FROM unnest(to_tsvector('english', %(query_text)s))
                    ),
                    ''
                )
            ) AS tsq
        )
        SELECT
            chunks.id,
            chunks.document_id,
            documents.name AS document_name,
            chunks.chunk_index,
            chunks.text,
            chunks.token_count,
            chunks.metadata,
            ts_rank_cd(
                chunks.search_vector,
                query_tsv.tsq
            ) AS bm25_score
        FROM document_chunks AS chunks
        LEFT JOIN documents
            ON documents.id = chunks.document_id
        CROSS JOIN query_tsv
        {where_clause}
          AND chunks.search_vector @@ query_tsv.tsq
        ORDER BY bm25_score DESC
        LIMIT %(limit)s;
        """

        params = {
            "query_text": query,
            "limit": limit,
            "document_id": document_id,
            "user_id": user_id,
        }

        with psycopg.connect(self._database_url) as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query_sql, params)
                rows = cursor.fetchall()

        logger.info(f"BM25 search: query='{query[:100]}', returned {len(rows)} rows")

        return [
            RetrievedChunk(
                id=row["id"],
                document_id=row["document_id"],
                index=row["chunk_index"],
                text=row["text"],
                token_count=row["token_count"],
                metadata=row["metadata"],
                similarity=float(row["bm25_score"]),
                document_name=row["document_name"],
            )
            for row in rows
        ]
