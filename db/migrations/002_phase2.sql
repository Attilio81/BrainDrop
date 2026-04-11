-- Phase 2: update source_type CHECK constraint to include new media types.
-- NOTE: 001_initial.sql was written to anticipate Phase 2 and already includes
-- all these values. This migration is a no-op on databases that ran 001,
-- but is kept for an explicit record that instagram/photo/voice/youtube were
-- introduced in Phase 2.

ALTER TABLE ideas DROP CONSTRAINT IF EXISTS ideas_source_type_check;
ALTER TABLE ideas ADD CONSTRAINT ideas_source_type_check
    CHECK (source_type IN ('url', 'text', 'instagram', 'photo', 'voice', 'youtube'));
