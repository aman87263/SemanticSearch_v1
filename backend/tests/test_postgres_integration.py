import os

import psycopg
import pytest
from app.core.settings import settings


def _try_connect(database_url: str):
    """Return a live connection or None if the database is unreachable."""
    try:
        conn = psycopg.connect(database_url, connect_timeout=3)
        return conn
    except Exception:
        return None


def test_postgres_schema_and_pgvector():
    database_url = os.getenv("DATABASE_URL", settings.vector_store.database_url)
    conn = _try_connect(database_url)
    if conn is None:
        pytest.skip(
            f"No reachable Postgres at {database_url} — "
            "integration test requires a live database."
        )

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            assert cursor.fetchone() == ("vector",)

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('documents', 'document_chunks')
                ORDER BY table_name
                """
            )
            assert [row[0] for row in cursor.fetchall()] == [
                "document_chunks",
                "documents",
            ]
