-- Phase 5: Semantic search
-- embedding VECTOR(1536) and pgvector extension already exist from 001_initial.sql
-- Run migration 004_details_column.sql first if not done yet.

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_ideas_embedding_hnsw
  ON ideas USING hnsw (embedding vector_cosine_ops);

-- Semantic search RPC
CREATE OR REPLACE FUNCTION match_ideas(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.25,
  match_count int DEFAULT 20,
  filter_published boolean DEFAULT null,
  filter_deleted boolean DEFAULT false
)
RETURNS TABLE (
  id uuid,
  created_at timestamptz,
  updated_at timestamptz,
  title text,
  summary text,
  details text,
  original_content text,
  enrichment_data jsonb,
  source_type text,
  category text,
  tags text[],
  media_url text,
  source_url text,
  thumbnail_url text,
  published boolean,
  published_at timestamptz,
  deleted_at timestamptz,
  notes text,
  sort_order integer,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    i.id, i.created_at, i.updated_at,
    i.title, i.summary, i.details,
    i.original_content, i.enrichment_data,
    i.source_type, i.category, i.tags,
    i.media_url, i.source_url, i.thumbnail_url,
    i.published, i.published_at, i.deleted_at,
    i.notes, i.sort_order,
    1 - (i.embedding <=> query_embedding) AS similarity
  FROM ideas i
  WHERE
    i.embedding IS NOT NULL
    AND 1 - (i.embedding <=> query_embedding) > match_threshold
    AND CASE
      WHEN filter_deleted THEN i.deleted_at IS NOT NULL
      ELSE i.deleted_at IS NULL
           AND (filter_published IS NULL OR i.published = filter_published)
    END
  ORDER BY i.embedding <=> query_embedding
  LIMIT match_count;
$$;
