-- Migration 008: Replace underscores with spaces in taxonomy values

-- Themes
UPDATE theme_context SET theme_name = 'class struggle' WHERE theme_name = 'class_struggle';
UPDATE theme_context SET theme_name = 'identity crisis' WHERE theme_name = 'identity_crisis';
UPDATE theme_context SET theme_name = 'police violence' WHERE theme_name = 'police_violence';

-- Character contexts
UPDATE character_context SET context_name = 'unreliable narrator' WHERE context_name = 'unreliable_narrator';
UPDATE character_context SET context_name = 'femme fatale' WHERE context_name = 'femme_fatale';

-- Messages
UPDATE message_conveyed SET message_name = 'anti establishment' WHERE message_name = 'anti_establishment';

-- Cinema types
UPDATE cinema_type SET technique_name = 'black and white' WHERE technique_name = 'black_and_white';
UPDATE cinema_type SET technique_name = 'non linear narrative' WHERE technique_name = 'non_linear_narrative';
UPDATE cinema_type SET technique_name = 'slow cinema' WHERE technique_name = 'slow_cinema';