-- Migration 007: Add new taxonomy values

-- Character archetypes
INSERT INTO character_context (context_name) VALUES
    ('ordinary'),
    ('poor/marginal'),
    ('wealthy'),
    ('star/celebrity'),
    ('genius')
ON CONFLICT (context_name) DO NOTHING;

