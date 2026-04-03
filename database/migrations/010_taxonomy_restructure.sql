-- Migration 010: Taxonomy restructure
-- Merges: characters_type + character_context → character_context ("characters" dimension)
-- Merges: cinema_type + cultural_movement → cinema_type ("cinema_types" dimension)
-- Moves: Disaster from categories → themes
-- Moves: dialogs, slang dialogs from messages → cinema_types
-- Adds: sort_order to 7 tables, new values (curse, game), rename gang → team/group/gang

BEGIN;

-- =============================================================================
-- 1. ADD sort_order COLUMNS to tables that lack them
-- =============================================================================

ALTER TABLE character_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE cinema_type ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE atmosphere ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE motivation_relation ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE place_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE message_conveyed ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;
ALTER TABLE category ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 999;

-- =============================================================================
-- 2. ADD NEW THEME VALUES
-- =============================================================================

INSERT INTO theme_context (theme_name, sort_order) VALUES
    ('curse', 411),
    ('game', 605)
ON CONFLICT (theme_name) DO NOTHING;

-- =============================================================================
-- 3. MOVE 'Disaster' FROM categories TO themes
-- =============================================================================

-- Insert 'disaster' into themes (sort_order 113, after apocalypse=112)
INSERT INTO theme_context (theme_name, sort_order) VALUES ('disaster', 113)
ON CONFLICT (theme_name) DO NOTHING;

-- Migrate film associations: film_genre → film_theme
INSERT INTO film_theme (film_id, theme_context_id)
SELECT fg.film_id, tc.theme_context_id
FROM film_genre fg
JOIN category c ON fg.category_id = c.category_id
CROSS JOIN theme_context tc
WHERE c.category_name = 'Disaster' AND c.historic_subcategory_name IS NULL
  AND tc.theme_name = 'disaster'
ON CONFLICT DO NOTHING;

-- Remove film_genre rows for Disaster
DELETE FROM film_genre
WHERE category_id IN (
    SELECT category_id FROM category
    WHERE category_name = 'Disaster' AND historic_subcategory_name IS NULL
);

-- Remove Disaster from categories
DELETE FROM category WHERE category_name = 'Disaster' AND historic_subcategory_name IS NULL;

-- =============================================================================
-- 4. MERGE characters_type INTO character_context
-- =============================================================================

-- 4a. Rename 'gang' in characters_type before migration
UPDATE characters_type SET type_name = 'team/group/gang' WHERE type_name = 'gang';

-- 4b. Insert all characters_type values into character_context (no overlap exists)
INSERT INTO character_context (context_name)
SELECT type_name FROM characters_type
ON CONFLICT (context_name) DO NOTHING;

-- 4c. Migrate film_characters → film_character_context
INSERT INTO film_character_context (film_id, character_context_id)
SELECT fc.film_id, cc.character_context_id
FROM film_characters fc
JOIN characters_type ct ON fc.character_type_id = ct.character_type_id
JOIN character_context cc ON cc.context_name = ct.type_name
ON CONFLICT DO NOTHING;

-- 4d. Drop old tables
DROP TABLE IF EXISTS film_characters CASCADE;
DROP TABLE IF EXISTS characters_type CASCADE;

-- =============================================================================
-- 5. MERGE cultural_movement INTO cinema_type
-- =============================================================================

-- 5a. Insert all cultural_movement values into cinema_type (no overlap exists)
INSERT INTO cinema_type (technique_name)
SELECT movement_name FROM cultural_movement
ON CONFLICT (technique_name) DO NOTHING;

-- 5b. Migrate film_movement → film_technique
INSERT INTO film_technique (film_id, cinema_type_id)
SELECT fm.film_id, ct.cinema_type_id
FROM film_movement fm
JOIN cultural_movement cm ON fm.movement_id = cm.movement_id
JOIN cinema_type ct ON ct.technique_name = cm.movement_name
ON CONFLICT DO NOTHING;

-- 5c. Drop old tables
DROP TABLE IF EXISTS film_movement CASCADE;
DROP TABLE IF EXISTS cultural_movement CASCADE;

-- =============================================================================
-- 6. MOVE 'dialogs' AND 'slang dialogs' FROM messages TO cinema_type
-- =============================================================================

-- 6a. Insert into cinema_type
INSERT INTO cinema_type (technique_name) VALUES ('dialogs'), ('slang dialogs')
ON CONFLICT (technique_name) DO NOTHING;

-- 6b. Migrate film_message rows → film_technique
INSERT INTO film_technique (film_id, cinema_type_id)
SELECT fmsg.film_id, ct.cinema_type_id
FROM film_message fmsg
JOIN message_conveyed mc ON fmsg.message_id = mc.message_id
JOIN cinema_type ct ON ct.technique_name = mc.message_name
WHERE mc.message_name IN ('dialogs', 'slang dialogs')
ON CONFLICT DO NOTHING;

-- 6c. Remove from film_message
DELETE FROM film_message
WHERE message_id IN (
    SELECT message_id FROM message_conveyed WHERE message_name IN ('dialogs', 'slang dialogs')
);

-- 6d. Remove from message_conveyed
DELETE FROM message_conveyed WHERE message_name IN ('dialogs', 'slang dialogs');

-- =============================================================================
-- 7. SET SORT ORDERS FOR ALL DIMENSIONS
-- =============================================================================

-- 7a. Categories
UPDATE category SET sort_order = 100 WHERE category_name = 'Comedy' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 101 WHERE category_name = 'Drama' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 102 WHERE category_name = 'Romance' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 103 WHERE category_name = 'Action' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 104 WHERE category_name = 'Adventure' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 105 WHERE category_name = 'Thriller' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 106 WHERE category_name = 'Science-Fiction' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 107 WHERE category_name = 'Fantasy' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 108 WHERE category_name = 'Horror' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 109 WHERE category_name = 'Musical' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 110 WHERE category_name = 'Documentary' AND historic_subcategory_name IS NULL;
UPDATE category SET sort_order = 111 WHERE category_name = 'Historical' AND historic_subcategory_name IS NULL;
-- Historical subcategories: sort under parent
UPDATE category SET sort_order = 112 WHERE category_name = 'Historical' AND historic_subcategory_name = 'biopic';
UPDATE category SET sort_order = 113 WHERE category_name = 'Historical' AND historic_subcategory_name = 'human interest story';
UPDATE category SET sort_order = 114 WHERE category_name = 'Historical' AND historic_subcategory_name = 'judicial chronicle';
UPDATE category SET sort_order = 115 WHERE category_name = 'Historical' AND historic_subcategory_name = 'western';
UPDATE category SET sort_order = 116 WHERE category_name = 'Historical' AND historic_subcategory_name = 'peplum';
UPDATE category SET sort_order = 117 WHERE category_name = 'Historical' AND historic_subcategory_name = 'swashbuckler';
UPDATE category SET sort_order = 118 WHERE category_name = 'Historical' AND historic_subcategory_name = 'event';

-- 7b. Cinema types (merged with cultural movements + dialogs)
-- Group 1: Visual techniques & aesthetics (100s)
UPDATE cinema_type SET sort_order = 100 WHERE technique_name = 'animation';
UPDATE cinema_type SET sort_order = 101 WHERE technique_name = 'mixed animation';
UPDATE cinema_type SET sort_order = 102 WHERE technique_name = 'CGI';
UPDATE cinema_type SET sort_order = 103 WHERE technique_name = '3D';
UPDATE cinema_type SET sort_order = 104 WHERE technique_name = 'motion capture';
UPDATE cinema_type SET sort_order = 105 WHERE technique_name = 'black and white';
UPDATE cinema_type SET sort_order = 106 WHERE technique_name = 'aesthetics';
-- Group 2: Movements & eras (200s)
UPDATE cinema_type SET sort_order = 200 WHERE technique_name = 'silent';
UPDATE cinema_type SET sort_order = 201 WHERE technique_name = 'expressionism';
UPDATE cinema_type SET sort_order = 202 WHERE technique_name = 'neo-realism';
UPDATE cinema_type SET sort_order = 203 WHERE technique_name = 'noir';
UPDATE cinema_type SET sort_order = 204 WHERE technique_name = 'hollywood golden age';
UPDATE cinema_type SET sort_order = 205 WHERE technique_name = 'new hollywood';
UPDATE cinema_type SET sort_order = 206 WHERE technique_name = 'new wave';
UPDATE cinema_type SET sort_order = 207 WHERE technique_name = 'realism';
UPDATE cinema_type SET sort_order = 208 WHERE technique_name = 'neo-noir';
UPDATE cinema_type SET sort_order = 209 WHERE technique_name = 'costume';
UPDATE cinema_type SET sort_order = 210 WHERE technique_name = 'dogma';
UPDATE cinema_type SET sort_order = 211 WHERE technique_name = 'blaxploitation';
UPDATE cinema_type SET sort_order = 212 WHERE technique_name = 'wu xia pian';
-- Group 3: Industry & culture (300s)
UPDATE cinema_type SET sort_order = 300 WHERE technique_name = 'blockbuster';
UPDATE cinema_type SET sort_order = 301 WHERE technique_name = 'art house';
UPDATE cinema_type SET sort_order = 302 WHERE technique_name = 'B';
UPDATE cinema_type SET sort_order = 303 WHERE technique_name = 'Z';
UPDATE cinema_type SET sort_order = 304 WHERE technique_name = 'Collection';
UPDATE cinema_type SET sort_order = 305 WHERE technique_name = 'generational';
UPDATE cinema_type SET sort_order = 306 WHERE technique_name = 'popular culture';
-- Group 4: Narrative techniques (400s)
UPDATE cinema_type SET sort_order = 400 WHERE technique_name = 'sequence-shot';
UPDATE cinema_type SET sort_order = 401 WHERE technique_name = 'found footage';
UPDATE cinema_type SET sort_order = 402 WHERE technique_name = 'multi-sequence';
UPDATE cinema_type SET sort_order = 403 WHERE technique_name = 'slow cinema';
UPDATE cinema_type SET sort_order = 404 WHERE technique_name = 'non linear narrative';
-- Group 5: Dialog style (500s)
UPDATE cinema_type SET sort_order = 500 WHERE technique_name = 'dialogs';
UPDATE cinema_type SET sort_order = 501 WHERE technique_name = 'slang dialogs';

-- 7c. Characters (merged character_context)
-- Group 1: Group structure (100s)
UPDATE character_context SET sort_order = 100 WHERE context_name = 'solitary';
UPDATE character_context SET sort_order = 101 WHERE context_name = 'tandem';
UPDATE character_context SET sort_order = 102 WHERE context_name = 'trio';
UPDATE character_context SET sort_order = 103 WHERE context_name = 'couple';
UPDATE character_context SET sort_order = 104 WHERE context_name = 'relatives';
UPDATE character_context SET sort_order = 105 WHERE context_name = 'generations';
UPDATE character_context SET sort_order = 106 WHERE context_name = 'buddies';
UPDATE character_context SET sort_order = 107 WHERE context_name = 'team/group/gang';
UPDATE character_context SET sort_order = 108 WHERE context_name = 'interracial';
UPDATE character_context SET sort_order = 109 WHERE context_name = 'ensemble cast';
-- Group 2: Age & identity (200s)
UPDATE character_context SET sort_order = 200 WHERE context_name = 'childhood';
UPDATE character_context SET sort_order = 201 WHERE context_name = 'teenager';
UPDATE character_context SET sort_order = 202 WHERE context_name = 'elderly';
UPDATE character_context SET sort_order = 203 WHERE context_name = 'adult/child';
UPDATE character_context SET sort_order = 204 WHERE context_name = 'female';
UPDATE character_context SET sort_order = 205 WHERE context_name = 'LGBT';
-- Group 3: Social status & traits (300s)
UPDATE character_context SET sort_order = 300 WHERE context_name = 'ordinary';
UPDATE character_context SET sort_order = 301 WHERE context_name = 'poor/marginal';
UPDATE character_context SET sort_order = 302 WHERE context_name = 'wealthy';
UPDATE character_context SET sort_order = 303 WHERE context_name = 'genius';
UPDATE character_context SET sort_order = 304 WHERE context_name = 'idiot';
UPDATE character_context SET sort_order = 305 WHERE context_name = 'looser';
UPDATE character_context SET sort_order = 306 WHERE context_name = 'star/celebrity';
UPDATE character_context SET sort_order = 307 WHERE context_name = 'madness';
UPDATE character_context SET sort_order = 308 WHERE context_name = 'freak/disabled';
UPDATE character_context SET sort_order = 309 WHERE context_name = 'prostitute';
UPDATE character_context SET sort_order = 310 WHERE context_name = 'psychopath';
-- Group 4: Narrative devices (400s)
UPDATE character_context SET sort_order = 400 WHERE context_name = 'double';
UPDATE character_context SET sort_order = 401 WHERE context_name = 'cross-dressing';
UPDATE character_context SET sort_order = 402 WHERE context_name = 'unreliable narrator';
-- Group 5: Archetypes — human (500s)
UPDATE character_context SET sort_order = 500 WHERE context_name = 'super hero';
UPDATE character_context SET sort_order = 501 WHERE context_name = 'antihero';
UPDATE character_context SET sort_order = 502 WHERE context_name = 'cop';
UPDATE character_context SET sort_order = 503 WHERE context_name = 'detective';
UPDATE character_context SET sort_order = 504 WHERE context_name = 'vigilante';
UPDATE character_context SET sort_order = 505 WHERE context_name = 'soldier';
UPDATE character_context SET sort_order = 506 WHERE context_name = 'femme fatale';
UPDATE character_context SET sort_order = 507 WHERE context_name = 'samourai';
UPDATE character_context SET sort_order = 508 WHERE context_name = 'pirate';
UPDATE character_context SET sort_order = 509 WHERE context_name = 'viking';
UPDATE character_context SET sort_order = 510 WHERE context_name = 'barbarian';
-- Group 6: Non-human & creatures (600s)
UPDATE character_context SET sort_order = 600 WHERE context_name = 'animal/wildlife';
UPDATE character_context SET sort_order = 601 WHERE context_name = 'monster/terrestrial creature';
UPDATE character_context SET sort_order = 602 WHERE context_name = 'evil';
UPDATE character_context SET sort_order = 603 WHERE context_name = 'witch';
UPDATE character_context SET sort_order = 604 WHERE context_name = 'ghost/spirit';
UPDATE character_context SET sort_order = 605 WHERE context_name = 'vampire';
UPDATE character_context SET sort_order = 606 WHERE context_name = 'zombie';
UPDATE character_context SET sort_order = 607 WHERE context_name = 'alien';
UPDATE character_context SET sort_order = 608 WHERE context_name = 'android';
UPDATE character_context SET sort_order = 609 WHERE context_name = 'vehicle';

-- 7d. Atmospheres
-- Group 1: Light (100s)
UPDATE atmosphere SET sort_order = 100 WHERE atmosphere_name = 'family';
UPDATE atmosphere SET sort_order = 101 WHERE atmosphere_name = 'feel good';
UPDATE atmosphere SET sort_order = 102 WHERE atmosphere_name = 'crazy/nutty';
UPDATE atmosphere SET sort_order = 103 WHERE atmosphere_name = 'depressive/sad';
-- Group 2: Tension (200s)
UPDATE atmosphere SET sort_order = 200 WHERE atmosphere_name = 'mysterious';
UPDATE atmosphere SET sort_order = 201 WHERE atmosphere_name = 'oppressive';
UPDATE atmosphere SET sort_order = 202 WHERE atmosphere_name = 'claustrophobic';
-- Group 3: Contemplative (300s)
UPDATE atmosphere SET sort_order = 300 WHERE atmosphere_name = 'contemplative';
UPDATE atmosphere SET sort_order = 301 WHERE atmosphere_name = 'ethereal';
UPDATE atmosphere SET sort_order = 302 WHERE atmosphere_name = 'hypnotic';
UPDATE atmosphere SET sort_order = 303 WHERE atmosphere_name = 'psychedelic';
-- Group 4: Dark (400s)
UPDATE atmosphere SET sort_order = 400 WHERE atmosphere_name = 'violent';
UPDATE atmosphere SET sort_order = 401 WHERE atmosphere_name = 'disturbing';
UPDATE atmosphere SET sort_order = 402 WHERE atmosphere_name = 'sulfurous';
UPDATE atmosphere SET sort_order = 403 WHERE atmosphere_name = 'trash';
UPDATE atmosphere SET sort_order = 404 WHERE atmosphere_name = 'gore';
UPDATE atmosphere SET sort_order = 405 WHERE atmosphere_name = 'awful/seedy/depraved';

-- 7e. Motivations
-- Group 1: Positive bonds (100s)
UPDATE motivation_relation SET sort_order = 100 WHERE motivation_name = 'feelings';
UPDATE motivation_relation SET sort_order = 101 WHERE motivation_name = 'friendship';
UPDATE motivation_relation SET sort_order = 102 WHERE motivation_name = 'solidarity';
UPDATE motivation_relation SET sort_order = 103 WHERE motivation_name = 'communication';
UPDATE motivation_relation SET sort_order = 104 WHERE motivation_name = 'emancipation';
UPDATE motivation_relation SET sort_order = 105 WHERE motivation_name = 'redemption';
-- Group 2: Inner conflict (200s)
UPDATE motivation_relation SET sort_order = 200 WHERE motivation_name = 'obsession';
UPDATE motivation_relation SET sort_order = 201 WHERE motivation_name = 'doubt/dilemma';
UPDATE motivation_relation SET sort_order = 202 WHERE motivation_name = 'lie';
UPDATE motivation_relation SET sort_order = 203 WHERE motivation_name = 'manipulation';
-- Group 3: Desire & transgression (300s)
UPDATE motivation_relation SET sort_order = 300 WHERE motivation_name = 'sex';
UPDATE motivation_relation SET sort_order = 301 WHERE motivation_name = 'adultery';
UPDATE motivation_relation SET sort_order = 302 WHERE motivation_name = 'jealousy';
UPDATE motivation_relation SET sort_order = 303 WHERE motivation_name = 'harassment';
UPDATE motivation_relation SET sort_order = 304 WHERE motivation_name = 'perversion';
-- Group 4: Conflict & struggle (400s)
UPDATE motivation_relation SET sort_order = 400 WHERE motivation_name = 'power';
UPDATE motivation_relation SET sort_order = 401 WHERE motivation_name = 'rivalry';
UPDATE motivation_relation SET sort_order = 402 WHERE motivation_name = 'fight';
UPDATE motivation_relation SET sort_order = 403 WHERE motivation_name = 'rebellion/revolt';
UPDATE motivation_relation SET sort_order = 404 WHERE motivation_name = 'vengeance';
-- Group 5: Epic quests (500s)
UPDATE motivation_relation SET sort_order = 500 WHERE motivation_name = 'odyssey';
UPDATE motivation_relation SET sort_order = 501 WHERE motivation_name = 'quest';
UPDATE motivation_relation SET sort_order = 502 WHERE motivation_name = 'world saver';
UPDATE motivation_relation SET sort_order = 503 WHERE motivation_name = 'invasion';

-- 7f. Place contexts
-- Group 1: Natural environments (100s)
UPDATE place_context SET sort_order = 100 WHERE environment = 'urban';
UPDATE place_context SET sort_order = 101 WHERE environment = 'country-style';
UPDATE place_context SET sort_order = 102 WHERE environment = 'forest';
UPDATE place_context SET sort_order = 103 WHERE environment = 'mountains';
UPDATE place_context SET sort_order = 104 WHERE environment = 'desert';
UPDATE place_context SET sort_order = 105 WHERE environment = 'beach';
UPDATE place_context SET sort_order = 106 WHERE environment = 'maritime';
UPDATE place_context SET sort_order = 107 WHERE environment = 'island';
UPDATE place_context SET sort_order = 108 WHERE environment = 'space';
-- Group 2: Buildings & institutions (200s)
UPDATE place_context SET sort_order = 200 WHERE environment = 'building';
UPDATE place_context SET sort_order = 201 WHERE environment = 'household/house/apartment';
UPDATE place_context SET sort_order = 202 WHERE environment = 'company/factory';
UPDATE place_context SET sort_order = 203 WHERE environment = 'school/university';
UPDATE place_context SET sort_order = 204 WHERE environment = 'hospital';
UPDATE place_context SET sort_order = 205 WHERE environment = 'jail';
UPDATE place_context SET sort_order = 206 WHERE environment = 'military';
UPDATE place_context SET sort_order = 207 WHERE environment = 'naval';
UPDATE place_context SET sort_order = 208 WHERE environment = 'ship';
-- Group 3: Narrative settings (300s)
UPDATE place_context SET sort_order = 300 WHERE environment = 'road movie';
UPDATE place_context SET sort_order = 301 WHERE environment = 'huis clos';
-- Group 4: None
UPDATE place_context SET sort_order = 400 WHERE environment = 'no particular';

-- 7g. Messages (without dialogs/slang dialogs, moved to cinema_types)
-- Group 1: Values & ideology (100s)
UPDATE message_conveyed SET sort_order = 100 WHERE message_name = 'humanist';
UPDATE message_conveyed SET sort_order = 101 WHERE message_name = 'philosophical';
UPDATE message_conveyed SET sort_order = 102 WHERE message_name = 'feminist';
UPDATE message_conveyed SET sort_order = 103 WHERE message_name = 'ecological';
UPDATE message_conveyed SET sort_order = 104 WHERE message_name = 'political';
-- Group 2: Comedy & satire (200s)
UPDATE message_conveyed SET sort_order = 200 WHERE message_name = 'parodic';
UPDATE message_conveyed SET sort_order = 201 WHERE message_name = 'satirical';
UPDATE message_conveyed SET sort_order = 202 WHERE message_name = 'black comedy';
UPDATE message_conveyed SET sort_order = 203 WHERE message_name = 'absurdist';
-- Group 3: Cultural perspective (300s)
UPDATE message_conveyed SET sort_order = 300 WHERE message_name = 'anti establishment';
UPDATE message_conveyed SET sort_order = 301 WHERE message_name = 'nostalgic';
UPDATE message_conveyed SET sort_order = 302 WHERE message_name = 'patriotic';
UPDATE message_conveyed SET sort_order = 303 WHERE message_name = 'traditionalist/way of life';
UPDATE message_conveyed SET sort_order = 304 WHERE message_name = 'history revisited';
-- Group 4: Artistic expression (400s)
UPDATE message_conveyed SET sort_order = 400 WHERE message_name = 'dreamlike';
UPDATE message_conveyed SET sort_order = 401 WHERE message_name = 'surreal';
UPDATE message_conveyed SET sort_order = 402 WHERE message_name = 'symbolic';
UPDATE message_conveyed SET sort_order = 403 WHERE message_name = 'metaphysical';

COMMIT;
