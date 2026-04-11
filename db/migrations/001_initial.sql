-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main ideas table
CREATE TABLE IF NOT EXISTS ideas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Content
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    original_content TEXT NOT NULL,
    enrichment_data JSONB DEFAULT '{}',

    -- Classification
    source_type TEXT NOT NULL CHECK (source_type IN ('url', 'youtube', 'instagram', 'photo', 'voice', 'text')),
    category TEXT NOT NULL DEFAULT 'other',
    tags TEXT[] DEFAULT '{}',

    -- Media
    media_url TEXT,
    source_url TEXT,
    thumbnail_url TEXT,

    -- Publishing
    published BOOLEAN DEFAULT false,
    published_at TIMESTAMPTZ,

    -- Admin (Phase 1+)
    deleted_at TIMESTAMPTZ,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,

    -- Search (Phase 5)
    embedding VECTOR(1536)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ideas_published ON ideas(published, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_tags ON ideas USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_ideas_created ON ideas(created_at DESC);

-- RLS
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- Public read for published, non-deleted items (Phase 4 frontend)
CREATE POLICY "Public can read published ideas"
    ON ideas FOR SELECT
    USING (published = true AND deleted_at IS NULL);

-- Service role full access (bot)
CREATE POLICY "Service role full access"
    ON ideas FOR ALL
    USING (auth.role() = 'service_role');
