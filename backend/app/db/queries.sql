--psql -U postgres
-- \conninfo
-- docker run -d `
--   --name semanticsearch-postgres `
--   -e POSTGRES_PASSWORD=choose-a-strong-password `
--   -e POSTGRES_DB=semanticsearch `
--   -p 5432:5432 `
--   -v semanticsearch_pgdata:/var/lib/postgresql/data `
--   pgvector/pgvector:pg16
------  database_url: postgresql://postgres:choose-a-strong-password@localhost:5432/semanticsearch
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (document_id, chunk_index)
);

CREATE INDEX document_chunks_embedding_hnsw_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

WITH query AS (
    SELECT embedding
    FROM document_chunks
    LIMIT 1
)
SELECT
    chunks.id,
    chunks.document_id,
    chunks.chunk_index,
    chunks.text,
    chunks.metadata,
    1 - (chunks.embedding <=> query.embedding) AS similarity
FROM document_chunks AS chunks
CROSS JOIN query
ORDER BY chunks.embedding <=> query.embedding
LIMIT 5;



CREATE TABLE documents (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    size BIGINT NOT NULL,
    file_hash TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER,
    CONSTRAINT uq_documents_file_hash UNIQUE (file_hash)
);

ALTER TABLE document_chunks
ADD CONSTRAINT fk_document_chunks_document
FOREIGN KEY (document_id)
REFERENCES documents(id)
ON DELETE CASCADE;