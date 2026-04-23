-- Migration 016: Taxonomy tag updates
-- - Delete 'historical event' from cinema_type
-- - Delete 'charismatic' from character_context
-- - Add 'cityscape' and 'pastoral' to atmosphere (Group 5)
-- - Rename 'idiot' → 'simpleton/fool' in character_context
-- - Rename 'country-style' → 'country' in place_context
-- - Rename 'virtual reality' → 'virtual/parallel universe' in theme_context

BEGIN;

-- Deletes (cascade removes film associations)
DELETE FROM cinema_type WHERE technique_name = 'historical event';
DELETE FROM character_context WHERE context_name = 'charismatic';

-- Renumber cinema_type Group 5 after removing 'historical event' (was 501)
UPDATE cinema_type SET sort_order = sort_order - 1 WHERE sort_order > 501 AND sort_order < 600;

-- Renumber character_context Group 3 after removing 'charismatic' (was 305)
UPDATE character_context SET sort_order = sort_order - 1 WHERE sort_order > 305 AND sort_order < 400;

-- Shift existing atmosphere Group 5 sort_orders to make room for new tags
UPDATE atmosphere SET sort_order = 503 WHERE atmosphere_name = 'epic';
UPDATE atmosphere SET sort_order = 502 WHERE atmosphere_name = 'gritty/realistic';

-- Add new atmosphere tags (Group 5: Scale & Tone)
INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    ('cityscape', 500),
    ('pastoral', 501)
ON CONFLICT (atmosphere_name) DO NOTHING;

-- Renames (preserves all film associations)
UPDATE character_context SET context_name = 'simpleton/fool' WHERE context_name = 'idiot';
UPDATE place_context SET environment = 'country' WHERE environment = 'country-style';
UPDATE theme_context SET theme_name = 'virtual/parallel universe' WHERE theme_name = 'virtual reality';

COMMIT;
