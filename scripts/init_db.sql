-- BioInfo Sidecar — Database initialisation
-- Run once: psql postgres -f scripts/init_db.sql

-- Create user and database
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sidecar') THEN
    CREATE USER sidecar WITH PASSWORD 'changeme';
  END IF;
END $$;

CREATE DATABASE bioinfo_sidecar OWNER sidecar;

\c bioinfo_sidecar

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL ON SCHEMA public TO sidecar;

-- Papers table — one row per arXiv paper
CREATE TABLE IF NOT EXISTS papers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxiv_id    TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    authors     TEXT[],
    abstract    TEXT,
    categories  TEXT[],
    published   DATE,
    parser_used TEXT DEFAULT 'docling',  -- 'docling' | 'marker' | 'html'
    fetched_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks table — one row per text chunk, with embedding
CREATE TABLE IF NOT EXISTS chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id    UUID REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section     TEXT,           -- 'Abstract' | 'Introduction' | 'Methods' | 'Results' | 'Discussion' | 'References'
    content     TEXT NOT NULL,
    tokens      INTEGER,
    embedding   VECTOR(768),    -- nomic-embed-text output dimension
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast approximate nearest-neighbour search
-- m=16, ef_construction=64 is a good starting point for research workloads
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search index on chunk content (BM25-style keyword search)
CREATE INDEX IF NOT EXISTS chunks_content_fts
    ON chunks USING gin (to_tsvector('english', content));

-- Metadata indices
CREATE INDEX IF NOT EXISTS papers_arxiv_id_idx ON papers (arxiv_id);
CREATE INDEX IF NOT EXISTS chunks_paper_id_idx ON chunks (paper_id);
CREATE INDEX IF NOT EXISTS chunks_section_idx ON chunks (section);

GRANT ALL ON ALL TABLES IN SCHEMA public TO sidecar;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO sidecar;

-- Verify
SELECT 'pgvector version: ' || extversion FROM pg_extension WHERE extname = 'vector';
SELECT 'Tables created: papers, chunks';
