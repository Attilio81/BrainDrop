-- Phase 2: add new source_type values to CHECK constraint
-- Run this in Supabase Dashboard → SQL Editor

ALTER TABLE ideas DROP CONSTRAINT IF EXISTS ideas_source_type_check;
ALTER TABLE ideas ADD CONSTRAINT ideas_source_type_check
    CHECK (source_type IN ('url', 'text', 'instagram', 'photo', 'voice', 'youtube'));
