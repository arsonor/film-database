-- Migration 006: Sort order columns, theme merges, category additions, motivation cleanup
-- Run: psql -U postgres -d film_database -f database/migrations/006_sort_order.sql

-- =============================================================================
-- 1. Add sort_order columns
-- =============================================================================

ALTER TABLE theme_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE time_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;

-- =============================================================================
-- 2. New categories: Documentary + Historical: event
-- =============================================================================

INSERT INTO category (category_name, historic_subcategory_name) VALUES
    ('Documentary', NULL),
    ('Historical', 'event')
ON CONFLICT (category_name, historic_subcategory_name) DO NOTHING;

-- =============================================================================
-- 3. Theme merges
-- =============================================================================

-- Merge: trauma + accident → trauma/accident
-- First move all film_theme rows from 'accident' to 'trauma'
UPDATE film_theme SET theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'trauma'
) WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'accident'
) AND NOT EXISTS (
    -- Avoid duplicate PK violations
    SELECT 1 FROM film_theme ft2
    WHERE ft2.film_id = film_theme.film_id
      AND ft2.theme_context_id = (SELECT theme_context_id FROM theme_context WHERE theme_name = 'trauma')
);
-- Delete any remaining duplicate rows that couldn't be moved
DELETE FROM film_theme WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'accident'
);
-- Rename trauma → trauma/accident
UPDATE theme_context SET theme_name = 'trauma/accident' WHERE theme_name = 'trauma';
-- Delete accident
DELETE FROM theme_context WHERE theme_name = 'accident';

-- Merge: technology + artificial_intelligence → AI/technology
UPDATE film_theme SET theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'technology'
) WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'artificial_intelligence'
) AND NOT EXISTS (
    SELECT 1 FROM film_theme ft2
    WHERE ft2.film_id = film_theme.film_id
      AND ft2.theme_context_id = (SELECT theme_context_id FROM theme_context WHERE theme_name = 'technology')
);
DELETE FROM film_theme WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'artificial_intelligence'
);
UPDATE theme_context SET theme_name = 'AI/technology' WHERE theme_name = 'technology';
DELETE FROM theme_context WHERE theme_name = 'artificial_intelligence';

-- =============================================================================
-- 4. Theme sort_order values (thematic groupings with gaps for separators)
-- =============================================================================

UPDATE theme_context SET sort_order = CASE theme_name
    -- Group 1: Society (100-199)
    WHEN 'social' THEN 100
    WHEN 'class_struggle' THEN 101
    WHEN 'societal' THEN 102
    WHEN 'immigration' THEN 103
    WHEN 'political' THEN 104
    WHEN 'religion' THEN 105
    WHEN 'business' THEN 106
    WHEN 'censorship' THEN 107
    WHEN 'trial' THEN 108
    WHEN 'prison' THEN 109
    WHEN 'war' THEN 110
    WHEN 'tragedy' THEN 111
    WHEN 'apocalypse' THEN 112
    -- Group 2: Personal / Psychological (200-299)
    WHEN 'trauma/accident' THEN 200
    WHEN 'psychological' THEN 201
    WHEN 'identity_crisis' THEN 202
    WHEN 'disease' THEN 203
    WHEN 'amnesia' THEN 204
    WHEN 'death' THEN 205
    WHEN 'mourning' THEN 206
    WHEN 'addiction/drugs' THEN 207
    WHEN 'time passing' THEN 208
    WHEN 'evolution' THEN 209
    -- Group 3: Crime / Thriller (300-399)
    WHEN 'investigation' THEN 300
    WHEN 'spy' THEN 301
    WHEN 'crime' THEN 302
    WHEN 'sex crime' THEN 303
    WHEN 'organized crime' THEN 304
    WHEN 'police_violence' THEN 305
    WHEN 'corruption' THEN 306
    WHEN 'delinquency' THEN 307
    WHEN 'organized fraud' THEN 308
    WHEN 'mafia' THEN 309
    WHEN 'gangster' THEN 310
    WHEN 'serial killer' THEN 311
    WHEN 'chase/escape' THEN 312
    WHEN 'terrorism' THEN 313
    WHEN 'sect' THEN 314
    WHEN 'survival' THEN 315
    WHEN 'slasher' THEN 316
    -- Group 4: Sci-fi / Fantasy (400-499)
    WHEN 'futuristic' THEN 400
    WHEN 'dystopia' THEN 401
    WHEN 'tales and legends' THEN 402
    WHEN 'supernatural' THEN 403
    WHEN 'sorcery' THEN 404
    WHEN 'alien contact' THEN 405
    WHEN 'paranormal' THEN 406
    WHEN 'time travel/loop' THEN 407
    WHEN 'virtual reality' THEN 408
    WHEN 'dream' THEN 409
    WHEN 'nonsense' THEN 410
    -- Group 5: Art & Sport (500-599)
    WHEN 'art' THEN 500
    WHEN 'art: music' THEN 501
    WHEN 'art: cinema' THEN 502
    WHEN 'art: literature' THEN 503
    WHEN 'art: fashion' THEN 504
    WHEN 'art: painting' THEN 505
    WHEN 'art: sculpture' THEN 506
    WHEN 'art: theatre' THEN 507
    WHEN 'art: radio' THEN 508
    WHEN 'martial arts' THEN 509
    WHEN 'sport' THEN 520
    WHEN 'sport: individual' THEN 521
    WHEN 'sport: collective' THEN 522
    WHEN 'sport: tournament' THEN 523
    WHEN 'sport: motor' THEN 524
    -- Group 6: Miscellaneous (600-699)
    WHEN 'nature' THEN 600
    WHEN 'AI/technology' THEN 601
    WHEN 'food/cooking' THEN 602
    WHEN 'party' THEN 603
    WHEN 'book' THEN 604
    ELSE 999
END;

-- =============================================================================
-- 5. Time period sort_order (chronological + seasons at end)
-- =============================================================================

UPDATE time_context SET sort_order = CASE time_period
    WHEN 'future' THEN 1
    WHEN 'contemporary' THEN 2
    WHEN 'end 20th' THEN 3
    WHEN '30-year post-war boom' THEN 4
    WHEN 'WW2' THEN 5
    WHEN 'interwar' THEN 6
    WHEN 'WW1' THEN 7
    WHEN 'early 20th' THEN 8
    WHEN '19th' THEN 9
    WHEN 'modern age' THEN 10
    WHEN 'medieval' THEN 11
    WHEN 'antiquity' THEN 12
    WHEN 'prehistoric' THEN 13
    WHEN 'undetermined' THEN 14
    -- Seasons
    WHEN 'spring' THEN 100
    WHEN 'summer' THEN 101
    WHEN 'autumn' THEN 102
    WHEN 'winter' THEN 103
    ELSE 999
END;

-- =============================================================================
-- 6. Remove survival from motivations
-- =============================================================================

DELETE FROM film_motivation WHERE motivation_id = (
    SELECT motivation_id FROM motivation_relation WHERE motivation_name = 'survival'
);
DELETE FROM motivation_relation WHERE motivation_name = 'survival';
