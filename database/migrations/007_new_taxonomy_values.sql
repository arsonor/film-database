-- Migration 007: Add new taxonomy values

-- Character archetypes
INSERT INTO character_context (context_name) VALUES
    ('vehicle')
ON CONFLICT (context_name) DO NOTHING;

