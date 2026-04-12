-- Add details column: schematic/structured breakdown of idea content
-- Complements summary (narrative prose) with a bullet-list breakdown
-- of every specific item, repo, URL, tool, or step in the content.
ALTER TABLE ideas ADD COLUMN IF NOT EXISTS details text NOT NULL DEFAULT '';
