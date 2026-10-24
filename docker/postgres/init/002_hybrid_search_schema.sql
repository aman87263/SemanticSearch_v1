-- 002_hybrid_search_schema.sql
--
-- Adds hybrid (BM25 + dense) search support on top of 001_schema.sql.
-- See semanticAdditions.md §10, §11, §12.
--
-- All statements are idempotent so this file is safe to re-run against an
-- existing database (the docker entrypoint only runs it on a fresh volume,
-- but the ALTER/CREATE ... IF NOT EXISTS guards make it re-runnable).

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    size BIGINT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    storage_key TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER,
    owner_id TEXT,
    uploader_email TEXT,
    uploader_name TEXT,
    visibility TEXT
);

-- Document chunks table with dense vector embedding
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

-- HNSW index for dense vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- --- Hybrid search support (semanticAdditions.md §10, §11) ---

-- tsvector column for BM25/sparse full-text search.
-- Populated automatically via trigger on INSERT/UPDATE of text.
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- GIN index for efficient token-based lookup on the tsvector column.
CREATE INDEX IF NOT EXISTS document_chunks_search_vector_gin_idx
ON document_chunks USING GIN (search_vector);

-- Trigger function to maintain the search_vector column.
-- Runs automatically whenever a row is inserted or updated.
CREATE OR REPLACE FUNCTION trigger_tsvector_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.text, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.metadata::text, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger fires before each insert or update on document_chunks.
DROP TRIGGER IF EXISTS tsvector_update_trigger ON document_chunks;
CREATE TRIGGER tsvector_update_trigger
BEFORE INSERT OR UPDATE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION trigger_tsvector_update();

-- Backfill search_vector for any existing rows that lack it.
-- This is safe to run idempotently.
UPDATE document_chunks
SET search_vector =
    setweight(to_tsvector('english', COALESCE(text, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(metadata::text, '')), 'B')
WHERE search_vector IS NULL;

-- A stored procedure for searching with ts_rank_cd (BM25-style ranking).
-- Can be called directly if needed for raw SQL-based searches.
-- Usage:
--   SELECT * FROM search_chunks('who is Admiral Whittaker?', 10);
CREATE OR REPLACE FUNCTION search_chunks(query_text TEXT, result_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    document_name TEXT,
    chunk_index INTEGER,
    text TEXT,
    token_count INTEGER,
    metadata JSONB,
    bm25_score REAL
) AS $$
BEGIN
    RETURN QUERY
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
            to_tsquery(
                'english',
                COALESCE(
                    (SELECT string_agg(lexeme, ' | ')
                     FROM unnest(to_tsvector('english', query_text))),
                    ''
                )
            )
        ) AS bm25_score
    FROM document_chunks AS chunks
    LEFT JOIN documents ON documents.id = chunks.document_id
    WHERE chunks.search_vector @@ to_tsquery(
        'english',
        COALESCE(
            (SELECT string_agg(lexeme, ' | ')
             FROM unnest(to_tsvector('english', query_text))),
            ''
        )
    )
    ORDER BY bm25_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;
