import os

import psycopg


def test_postgres_schema_and_pgvector():
    database_url = os.environ["DATABASE_URL"]

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
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
