-- Migration 007: Add new taxonomy values
-- Character context: soldier
-- Place environment: military, ship
-- Motivations: communication, invasion
-- Message: patriotic, history revisited, traditionalist/way of life
-- Cinema type: costume

-- Character archetypes
INSERT INTO character_context (context_name) VALUES
    ('soldier')
ON CONFLICT (context_name) DO NOTHING;

-- Place environments
INSERT INTO place_context (environment) VALUES
    ('military'),
    ('ship')
ON CONFLICT (environment) DO NOTHING;

-- Motivations
INSERT INTO motivation_relation (motivation_name) VALUES
    ('communication'),
    ('invasion')
ON CONFLICT (motivation_name) DO NOTHING;

-- Messages
INSERT INTO message_conveyed (message_name) VALUES
    ('patriotic'),
    ('history revisited'),
    ('traditionalist/way of life')
ON CONFLICT (message_name) DO NOTHING;

-- Cinema type
INSERT INTO cinema_type (technique_name) VALUES
    ('costume')
ON CONFLICT (technique_name) DO NOTHING;
