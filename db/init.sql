CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    source VARCHAR(255),
    embedding VECTOR(1536)
);

-- Indexes for faster retrieval
CREATE INDEX IF NOT EXISTS documents_embedding_ivfflat_idx
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS documents_source_idx
    ON documents (source); 