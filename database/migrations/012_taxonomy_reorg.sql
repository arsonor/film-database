-- Migration 012: Taxonomy reorganization
-- Renames, adds, deletes, moves, splits across all dimensions
-- Must be run BEFORE updating seed_taxonomy.sql

BEGIN;

-- =============================================================================
-- THEMES
-- =============================================================================

-- Renames
UPDATE theme_context SET theme_name = 'illness' WHERE theme_name = 'disease';
UPDATE theme_context SET theme_name = 'transformation' WHERE theme_name = 'evolution';
UPDATE theme_context SET theme_name = 'whimsical/zany' WHERE theme_name = 'nonsense';

-- New tags
INSERT INTO theme_context (theme_name, sort_order) VALUES
    ('journalism/media', 106),
    ('slavery', 114),
    ('colonialism', 115),
    ('heist', 305),
    ('kidnapping/hostage', 306),
    ('art: architecture', 509),
    ('gambling', 515)
ON CONFLICT (theme_name) DO NOTHING;

-- Delete: futuristic
-- Remove junction rows first, then the tag
DELETE FROM film_theme WHERE theme_context_id = (SELECT theme_context_id FROM theme_context WHERE theme_name = 'futuristic');
DELETE FROM theme_context WHERE theme_name = 'futuristic';

-- Move gangster from themes (Group 3) to characters (Group 5)
-- 1. Create character entry
INSERT INTO character_context (context_name, sort_order) VALUES ('gangster', 505)
ON CONFLICT (context_name) DO NOTHING;
-- 2. Migrate film associations
INSERT INTO film_character_context (film_id, character_context_id)
    SELECT ft.film_id, (SELECT character_context_id FROM character_context WHERE context_name = 'gangster')
    FROM film_theme ft
    JOIN theme_context tc ON ft.theme_context_id = tc.theme_context_id
    WHERE tc.theme_name = 'gangster'
ON CONFLICT DO NOTHING;
-- 3. Remove from themes
DELETE FROM film_theme WHERE theme_context_id = (SELECT theme_context_id FROM theme_context WHERE theme_name = 'gangster');
DELETE FROM theme_context WHERE theme_name = 'gangster';

-- Move party and game from Group 6 to Group 5 (sort_order update)
UPDATE theme_context SET sort_order = 513 WHERE theme_name = 'party';
UPDATE theme_context SET sort_order = 514 WHERE theme_name = 'game';

-- Update all theme sort_orders to match new grouping
-- Group 1: Society (100-199)
UPDATE theme_context SET sort_order = 100 WHERE theme_name = 'social';
UPDATE theme_context SET sort_order = 101 WHERE theme_name = 'class struggle';
UPDATE theme_context SET sort_order = 102 WHERE theme_name = 'societal';
UPDATE theme_context SET sort_order = 103 WHERE theme_name = 'political';
UPDATE theme_context SET sort_order = 104 WHERE theme_name = 'religion';
UPDATE theme_context SET sort_order = 105 WHERE theme_name = 'business';
UPDATE theme_context SET sort_order = 106 WHERE theme_name = 'journalism/media';
UPDATE theme_context SET sort_order = 107 WHERE theme_name = 'censorship';
UPDATE theme_context SET sort_order = 108 WHERE theme_name = 'trial/judicial chronicle';
UPDATE theme_context SET sort_order = 109 WHERE theme_name = 'prison';
UPDATE theme_context SET sort_order = 110 WHERE theme_name = 'war';
UPDATE theme_context SET sort_order = 111 WHERE theme_name = 'immigration';
UPDATE theme_context SET sort_order = 112 WHERE theme_name = 'slavery';
UPDATE theme_context SET sort_order = 113 WHERE theme_name = 'colonialism';
UPDATE theme_context SET sort_order = 114 WHERE theme_name = 'tragedy';
UPDATE theme_context SET sort_order = 115 WHERE theme_name = 'apocalypse';
UPDATE theme_context SET sort_order = 116 WHERE theme_name = 'disaster';
-- Group 2: Personal / Psychological (200-299)
UPDATE theme_context SET sort_order = 200 WHERE theme_name = 'trauma/accident';
UPDATE theme_context SET sort_order = 201 WHERE theme_name = 'psychological';
UPDATE theme_context SET sort_order = 202 WHERE theme_name = 'identity crisis';
UPDATE theme_context SET sort_order = 203 WHERE theme_name = 'illness';
UPDATE theme_context SET sort_order = 204 WHERE theme_name = 'amnesia';
UPDATE theme_context SET sort_order = 205 WHERE theme_name = 'death';
UPDATE theme_context SET sort_order = 206 WHERE theme_name = 'mourning';
UPDATE theme_context SET sort_order = 207 WHERE theme_name = 'addiction/drugs';
UPDATE theme_context SET sort_order = 208 WHERE theme_name = 'time passing';
UPDATE theme_context SET sort_order = 209 WHERE theme_name = 'transformation';
-- Group 3: Crime / Thriller (300-399)
UPDATE theme_context SET sort_order = 300 WHERE theme_name = 'investigation';
UPDATE theme_context SET sort_order = 301 WHERE theme_name = 'spy';
UPDATE theme_context SET sort_order = 302 WHERE theme_name = 'crime';
UPDATE theme_context SET sort_order = 303 WHERE theme_name = 'sex crime';
UPDATE theme_context SET sort_order = 304 WHERE theme_name = 'organized crime';
UPDATE theme_context SET sort_order = 305 WHERE theme_name = 'heist';
UPDATE theme_context SET sort_order = 306 WHERE theme_name = 'kidnapping/hostage';
UPDATE theme_context SET sort_order = 307 WHERE theme_name = 'police violence';
UPDATE theme_context SET sort_order = 308 WHERE theme_name = 'corruption';
UPDATE theme_context SET sort_order = 309 WHERE theme_name = 'delinquency';
UPDATE theme_context SET sort_order = 310 WHERE theme_name = 'organized fraud';
UPDATE theme_context SET sort_order = 311 WHERE theme_name = 'mafia';
UPDATE theme_context SET sort_order = 312 WHERE theme_name = 'serial killer';
UPDATE theme_context SET sort_order = 313 WHERE theme_name = 'chase/escape';
UPDATE theme_context SET sort_order = 314 WHERE theme_name = 'terrorism';
UPDATE theme_context SET sort_order = 315 WHERE theme_name = 'sect';
UPDATE theme_context SET sort_order = 316 WHERE theme_name = 'survival';
-- Group 4: Sci-fi / Fantasy (400-499)
UPDATE theme_context SET sort_order = 400 WHERE theme_name = 'dystopia';
UPDATE theme_context SET sort_order = 401 WHERE theme_name = 'tales and legends';
UPDATE theme_context SET sort_order = 402 WHERE theme_name = 'supernatural';
UPDATE theme_context SET sort_order = 403 WHERE theme_name = 'sorcery';
UPDATE theme_context SET sort_order = 404 WHERE theme_name = 'alien contact';
UPDATE theme_context SET sort_order = 405 WHERE theme_name = 'paranormal';
UPDATE theme_context SET sort_order = 406 WHERE theme_name = 'curse';
UPDATE theme_context SET sort_order = 407 WHERE theme_name = 'time travel/loop';
UPDATE theme_context SET sort_order = 408 WHERE theme_name = 'virtual reality';
UPDATE theme_context SET sort_order = 409 WHERE theme_name = 'dream';
UPDATE theme_context SET sort_order = 410 WHERE theme_name = 'whimsical/zany';
-- Group 5: Art, Sport & Entertainment (500-599)
UPDATE theme_context SET sort_order = 500 WHERE theme_name = 'art';
UPDATE theme_context SET sort_order = 501 WHERE theme_name = 'art: music';
UPDATE theme_context SET sort_order = 502 WHERE theme_name = 'art: cinema';
UPDATE theme_context SET sort_order = 503 WHERE theme_name = 'art: literature';
UPDATE theme_context SET sort_order = 504 WHERE theme_name = 'art: fashion';
UPDATE theme_context SET sort_order = 505 WHERE theme_name = 'art: painting';
UPDATE theme_context SET sort_order = 506 WHERE theme_name = 'art: sculpture';
UPDATE theme_context SET sort_order = 507 WHERE theme_name = 'art: theatre';
UPDATE theme_context SET sort_order = 508 WHERE theme_name = 'art: radio';
UPDATE theme_context SET sort_order = 509 WHERE theme_name = 'art: architecture';
UPDATE theme_context SET sort_order = 510 WHERE theme_name = 'martial arts';
UPDATE theme_context SET sort_order = 520 WHERE theme_name = 'sport';
UPDATE theme_context SET sort_order = 521 WHERE theme_name = 'sport: individual';
UPDATE theme_context SET sort_order = 522 WHERE theme_name = 'sport: collective';
UPDATE theme_context SET sort_order = 523 WHERE theme_name = 'sport: tournament';
UPDATE theme_context SET sort_order = 524 WHERE theme_name = 'sport: motor';
UPDATE theme_context SET sort_order = 513 WHERE theme_name = 'party';
UPDATE theme_context SET sort_order = 514 WHERE theme_name = 'game';
UPDATE theme_context SET sort_order = 515 WHERE theme_name = 'gambling';
-- Group 6: Miscellaneous (600-699)
UPDATE theme_context SET sort_order = 600 WHERE theme_name = 'nature';
UPDATE theme_context SET sort_order = 601 WHERE theme_name = 'AI/technology';
UPDATE theme_context SET sort_order = 602 WHERE theme_name = 'food/cooking';

-- =============================================================================
-- TIME PERIODS
-- =============================================================================

-- Rename
UPDATE time_context SET time_period = '20th post-war' WHERE time_period = '30-year post-war boom';

-- New tag
INSERT INTO time_context (time_period, sort_order) VALUES ('early 21st', 3)
ON CONFLICT (time_period) DO NOTHING;

-- Update sort_orders: future -> prehistoric, then undetermined, then seasons
UPDATE time_context SET sort_order = 1 WHERE time_period = 'future';
UPDATE time_context SET sort_order = 2 WHERE time_period = 'contemporary';
UPDATE time_context SET sort_order = 3 WHERE time_period = 'early 21st';
UPDATE time_context SET sort_order = 4 WHERE time_period = 'end 20th';
UPDATE time_context SET sort_order = 5 WHERE time_period = '20th post-war';
UPDATE time_context SET sort_order = 6 WHERE time_period = 'WW2';
UPDATE time_context SET sort_order = 7 WHERE time_period = 'interwar';
UPDATE time_context SET sort_order = 8 WHERE time_period = 'WW1';
UPDATE time_context SET sort_order = 9 WHERE time_period = 'early 20th';
UPDATE time_context SET sort_order = 10 WHERE time_period = '19th';
UPDATE time_context SET sort_order = 11 WHERE time_period = 'modern age';
UPDATE time_context SET sort_order = 12 WHERE time_period = 'medieval';
UPDATE time_context SET sort_order = 13 WHERE time_period = 'antiquity';
UPDATE time_context SET sort_order = 14 WHERE time_period = 'prehistoric';
UPDATE time_context SET sort_order = 15 WHERE time_period = 'undetermined';
UPDATE time_context SET sort_order = 100 WHERE time_period = 'spring';
UPDATE time_context SET sort_order = 101 WHERE time_period = 'summer';
UPDATE time_context SET sort_order = 102 WHERE time_period = 'autumn';
UPDATE time_context SET sort_order = 103 WHERE time_period = 'winter';

-- =============================================================================
-- PLACE CONTEXTS
-- =============================================================================

-- Rename
UPDATE place_context SET environment = 'huis clos/confined setting' WHERE environment = 'huis clos';

-- New tag
INSERT INTO place_context (environment, sort_order) VALUES ('underground', 109)
ON CONFLICT (environment) DO NOTHING;

-- Update sort_orders
-- Group 1: Natural environments
UPDATE place_context SET sort_order = 100 WHERE environment = 'urban';
UPDATE place_context SET sort_order = 101 WHERE environment = 'country-style';
UPDATE place_context SET sort_order = 102 WHERE environment = 'forest';
UPDATE place_context SET sort_order = 103 WHERE environment = 'mountains';
UPDATE place_context SET sort_order = 104 WHERE environment = 'desert';
UPDATE place_context SET sort_order = 105 WHERE environment = 'beach';
UPDATE place_context SET sort_order = 106 WHERE environment = 'maritime';
UPDATE place_context SET sort_order = 107 WHERE environment = 'island';
UPDATE place_context SET sort_order = 108 WHERE environment = 'underground';
UPDATE place_context SET sort_order = 109 WHERE environment = 'space';
-- Group 2: Buildings & institutions
UPDATE place_context SET sort_order = 200 WHERE environment = 'building';
UPDATE place_context SET sort_order = 201 WHERE environment = 'household/house/apartment';
UPDATE place_context SET sort_order = 202 WHERE environment = 'company/factory';
UPDATE place_context SET sort_order = 203 WHERE environment = 'school/university';
UPDATE place_context SET sort_order = 204 WHERE environment = 'hospital';
UPDATE place_context SET sort_order = 205 WHERE environment = 'jail';
UPDATE place_context SET sort_order = 206 WHERE environment = 'military';
UPDATE place_context SET sort_order = 207 WHERE environment = 'naval';
UPDATE place_context SET sort_order = 208 WHERE environment = 'ship';
-- Group 3: Narrative settings
UPDATE place_context SET sort_order = 300 WHERE environment = 'road movie';
UPDATE place_context SET sort_order = 301 WHERE environment = 'huis clos/confined setting';
-- Group 4: None
UPDATE place_context SET sort_order = 400 WHERE environment = 'no particular';

-- =============================================================================
-- ATMOSPHERES
-- =============================================================================

-- Renames
UPDATE atmosphere SET atmosphere_name = 'family-friendly' WHERE atmosphere_name = 'family';
UPDATE atmosphere SET atmosphere_name = 'contemplative/meditative' WHERE atmosphere_name = 'contemplative';
UPDATE atmosphere SET atmosphere_name = 'hypnotic/immersive' WHERE atmosphere_name = 'hypnotic';
UPDATE atmosphere SET atmosphere_name = 'sordid' WHERE atmosphere_name = 'awful/seedy/depraved';

-- New tags
INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    ('delicate/intimate', 103),
    ('meticulous', 302),
    ('gritty/realistic', 500),
    ('epic', 501)
ON CONFLICT (atmosphere_name) DO NOTHING;

-- Move depressive/sad from Group 1 to Group 4
-- Move contemplative/meditative from Group 3 to Group 1

-- Update all sort_orders
-- Group 1: Light/Joyful
UPDATE atmosphere SET sort_order = 100 WHERE atmosphere_name = 'family-friendly';
UPDATE atmosphere SET sort_order = 101 WHERE atmosphere_name = 'feel good';
UPDATE atmosphere SET sort_order = 102 WHERE atmosphere_name = 'crazy/nutty';
UPDATE atmosphere SET sort_order = 103 WHERE atmosphere_name = 'delicate/intimate';
UPDATE atmosphere SET sort_order = 104 WHERE atmosphere_name = 'contemplative/meditative';
-- Group 2: Tension
UPDATE atmosphere SET sort_order = 200 WHERE atmosphere_name = 'mysterious';
UPDATE atmosphere SET sort_order = 201 WHERE atmosphere_name = 'oppressive';
UPDATE atmosphere SET sort_order = 202 WHERE atmosphere_name = 'claustrophobic';
-- Group 3: Attention
UPDATE atmosphere SET sort_order = 300 WHERE atmosphere_name = 'meticulous';
UPDATE atmosphere SET sort_order = 301 WHERE atmosphere_name = 'ethereal';
UPDATE atmosphere SET sort_order = 302 WHERE atmosphere_name = 'hypnotic/immersive';
UPDATE atmosphere SET sort_order = 303 WHERE atmosphere_name = 'psychedelic';
-- Group 4: Dark/Extreme
UPDATE atmosphere SET sort_order = 400 WHERE atmosphere_name = 'depressive/sad';
UPDATE atmosphere SET sort_order = 401 WHERE atmosphere_name = 'violent';
UPDATE atmosphere SET sort_order = 402 WHERE atmosphere_name = 'disturbing';
UPDATE atmosphere SET sort_order = 403 WHERE atmosphere_name = 'steamy';
UPDATE atmosphere SET sort_order = 404 WHERE atmosphere_name = 'gore';
UPDATE atmosphere SET sort_order = 405 WHERE atmosphere_name = 'sordid';
-- Group 5: Scale & Tone
UPDATE atmosphere SET sort_order = 500 WHERE atmosphere_name = 'gritty/realistic';
UPDATE atmosphere SET sort_order = 501 WHERE atmosphere_name = 'epic';

-- =============================================================================
-- CHARACTERS
-- =============================================================================

-- Renames
UPDATE character_context SET context_name = 'loser' WHERE context_name = 'looser';
UPDATE character_context SET context_name = 'disturbed/madness' WHERE context_name = 'madness';
UPDATE character_context SET context_name = 'samurai' WHERE context_name = 'samourai';

-- Split: freak/disabled → disabled + outcast/misfit (tag films with both)
INSERT INTO character_context (context_name, sort_order) VALUES
    ('disabled', 311),
    ('outcast/misfit', 312)
ON CONFLICT (context_name) DO NOTHING;

-- Tag films that had freak/disabled with both new tags
INSERT INTO film_character_context (film_id, character_context_id)
    SELECT fcc.film_id, (SELECT character_context_id FROM character_context WHERE context_name = 'disabled')
    FROM film_character_context fcc
    JOIN character_context cc ON fcc.character_context_id = cc.character_context_id
    WHERE cc.context_name = 'freak/disabled'
ON CONFLICT DO NOTHING;

INSERT INTO film_character_context (film_id, character_context_id)
    SELECT fcc.film_id, (SELECT character_context_id FROM character_context WHERE context_name = 'outcast/misfit')
    FROM film_character_context fcc
    JOIN character_context cc ON fcc.character_context_id = cc.character_context_id
    WHERE cc.context_name = 'freak/disabled'
ON CONFLICT DO NOTHING;

-- Remove old freak/disabled
DELETE FROM film_character_context WHERE character_context_id = (SELECT character_context_id FROM character_context WHERE context_name = 'freak/disabled');
DELETE FROM character_context WHERE context_name = 'freak/disabled';

-- New tags
INSERT INTO character_context (context_name, sort_order) VALUES
    ('charismatic', 306),
    ('scientist/researcher', 511),
    ('mentor', 512)
ON CONFLICT (context_name) DO NOTHING;

-- Move interracial from Group 1 to Group 2
-- gangster already moved from themes above

-- Update all sort_orders
-- Group 1: Group structure
UPDATE character_context SET sort_order = 100 WHERE context_name = 'solitary';
UPDATE character_context SET sort_order = 101 WHERE context_name = 'tandem';
UPDATE character_context SET sort_order = 102 WHERE context_name = 'trio';
UPDATE character_context SET sort_order = 103 WHERE context_name = 'couple';
UPDATE character_context SET sort_order = 104 WHERE context_name = 'relatives';
UPDATE character_context SET sort_order = 105 WHERE context_name = 'generations';
UPDATE character_context SET sort_order = 106 WHERE context_name = 'buddies';
UPDATE character_context SET sort_order = 107 WHERE context_name = 'team/group/gang';
UPDATE character_context SET sort_order = 108 WHERE context_name = 'ensemble cast';
-- Group 2: Age & identity
UPDATE character_context SET sort_order = 200 WHERE context_name = 'childhood';
UPDATE character_context SET sort_order = 201 WHERE context_name = 'teenager';
UPDATE character_context SET sort_order = 202 WHERE context_name = 'elderly';
UPDATE character_context SET sort_order = 203 WHERE context_name = 'adult/child';
UPDATE character_context SET sort_order = 204 WHERE context_name = 'female';
UPDATE character_context SET sort_order = 205 WHERE context_name = 'LGBT';
UPDATE character_context SET sort_order = 206 WHERE context_name = 'interracial';
-- Group 3: Social status & traits
UPDATE character_context SET sort_order = 300 WHERE context_name = 'ordinary';
UPDATE character_context SET sort_order = 301 WHERE context_name = 'poor/marginal';
UPDATE character_context SET sort_order = 302 WHERE context_name = 'wealthy';
UPDATE character_context SET sort_order = 303 WHERE context_name = 'genius';
UPDATE character_context SET sort_order = 304 WHERE context_name = 'idiot';
UPDATE character_context SET sort_order = 305 WHERE context_name = 'charismatic';
UPDATE character_context SET sort_order = 306 WHERE context_name = 'loser';
UPDATE character_context SET sort_order = 307 WHERE context_name = 'star/celebrity';
UPDATE character_context SET sort_order = 308 WHERE context_name = 'disturbed/madness';
UPDATE character_context SET sort_order = 309 WHERE context_name = 'disabled';
UPDATE character_context SET sort_order = 310 WHERE context_name = 'outcast/misfit';
UPDATE character_context SET sort_order = 311 WHERE context_name = 'prostitute';
UPDATE character_context SET sort_order = 312 WHERE context_name = 'psychopath';
-- Group 4: Narrative devices
UPDATE character_context SET sort_order = 400 WHERE context_name = 'double';
UPDATE character_context SET sort_order = 401 WHERE context_name = 'cross-dressing';
UPDATE character_context SET sort_order = 402 WHERE context_name = 'unreliable narrator';
-- Group 5: Archetypes - human
UPDATE character_context SET sort_order = 500 WHERE context_name = 'super hero';
UPDATE character_context SET sort_order = 501 WHERE context_name = 'antihero';
UPDATE character_context SET sort_order = 502 WHERE context_name = 'cop';
UPDATE character_context SET sort_order = 503 WHERE context_name = 'detective';
UPDATE character_context SET sort_order = 504 WHERE context_name = 'vigilante';
UPDATE character_context SET sort_order = 505 WHERE context_name = 'gangster';
UPDATE character_context SET sort_order = 506 WHERE context_name = 'soldier';
UPDATE character_context SET sort_order = 507 WHERE context_name = 'femme fatale';
UPDATE character_context SET sort_order = 508 WHERE context_name = 'samurai';
UPDATE character_context SET sort_order = 509 WHERE context_name = 'pirate';
UPDATE character_context SET sort_order = 510 WHERE context_name = 'viking';
UPDATE character_context SET sort_order = 511 WHERE context_name = 'scientist/researcher';
UPDATE character_context SET sort_order = 512 WHERE context_name = 'mentor';
-- Group 6: Non-human & creatures
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

-- =============================================================================
-- MOTIVATIONS
-- =============================================================================

-- Renames
UPDATE motivation_relation SET motivation_name = 'love' WHERE motivation_name = 'feelings';
UPDATE motivation_relation SET motivation_name = 'world-saving' WHERE motivation_name = 'world saver';

-- New tags
INSERT INTO motivation_relation (motivation_name, sort_order) VALUES
    ('honor/duty', 106),
    ('sacrifice', 204),
    ('greed/ambition', 300)
ON CONFLICT (motivation_name) DO NOTHING;

-- Update all sort_orders
-- Group 1: Positive bonds
UPDATE motivation_relation SET sort_order = 100 WHERE motivation_name = 'love';
UPDATE motivation_relation SET sort_order = 101 WHERE motivation_name = 'friendship';
UPDATE motivation_relation SET sort_order = 102 WHERE motivation_name = 'solidarity';
UPDATE motivation_relation SET sort_order = 103 WHERE motivation_name = 'communication';
UPDATE motivation_relation SET sort_order = 104 WHERE motivation_name = 'emancipation';
UPDATE motivation_relation SET sort_order = 105 WHERE motivation_name = 'redemption';
UPDATE motivation_relation SET sort_order = 106 WHERE motivation_name = 'honor/duty';
-- Group 2: Inner conflict
UPDATE motivation_relation SET sort_order = 200 WHERE motivation_name = 'obsession';
UPDATE motivation_relation SET sort_order = 201 WHERE motivation_name = 'doubt/dilemma';
UPDATE motivation_relation SET sort_order = 202 WHERE motivation_name = 'lie';
UPDATE motivation_relation SET sort_order = 203 WHERE motivation_name = 'manipulation';
UPDATE motivation_relation SET sort_order = 204 WHERE motivation_name = 'sacrifice';
-- Group 3: Desire & transgression
UPDATE motivation_relation SET sort_order = 300 WHERE motivation_name = 'greed/ambition';
UPDATE motivation_relation SET sort_order = 301 WHERE motivation_name = 'sex';
UPDATE motivation_relation SET sort_order = 302 WHERE motivation_name = 'adultery';
UPDATE motivation_relation SET sort_order = 303 WHERE motivation_name = 'jealousy';
UPDATE motivation_relation SET sort_order = 304 WHERE motivation_name = 'harassment';
UPDATE motivation_relation SET sort_order = 305 WHERE motivation_name = 'perversion';
-- Group 4: Conflict & struggle
UPDATE motivation_relation SET sort_order = 400 WHERE motivation_name = 'power';
UPDATE motivation_relation SET sort_order = 401 WHERE motivation_name = 'rivalry';
UPDATE motivation_relation SET sort_order = 402 WHERE motivation_name = 'fight';
UPDATE motivation_relation SET sort_order = 403 WHERE motivation_name = 'rebellion/revolt';
UPDATE motivation_relation SET sort_order = 404 WHERE motivation_name = 'vengeance';
-- Group 5: Epic quests
UPDATE motivation_relation SET sort_order = 500 WHERE motivation_name = 'odyssey';
UPDATE motivation_relation SET sort_order = 501 WHERE motivation_name = 'quest';
UPDATE motivation_relation SET sort_order = 502 WHERE motivation_name = 'world-saving';
UPDATE motivation_relation SET sort_order = 503 WHERE motivation_name = 'invasion';

-- =============================================================================
-- MESSAGES
-- =============================================================================

-- Rename
UPDATE message_conveyed SET message_name = 'revisionist/alternate history' WHERE message_name = 'history revisited';

-- Move black comedy from messages to cinema_types
INSERT INTO cinema_type (technique_name, sort_order) VALUES ('black comedy', 509)
ON CONFLICT (technique_name) DO NOTHING;

INSERT INTO film_technique (film_id, cinema_type_id)
    SELECT fm.film_id, (SELECT cinema_type_id FROM cinema_type WHERE technique_name = 'black comedy')
    FROM film_message fm
    JOIN message_conveyed mc ON fm.message_id = mc.message_id
    WHERE mc.message_name = 'black comedy'
ON CONFLICT DO NOTHING;

DELETE FROM film_message WHERE message_id = (SELECT message_id FROM message_conveyed WHERE message_name = 'black comedy');
DELETE FROM message_conveyed WHERE message_name = 'black comedy';

-- New tag
INSERT INTO message_conveyed (message_name, sort_order) VALUES ('poetic', 403)
ON CONFLICT (message_name) DO NOTHING;

-- Update all sort_orders (new grouping)
-- Group 1: Values & ideology
UPDATE message_conveyed SET sort_order = 100 WHERE message_name = 'humanist';
UPDATE message_conveyed SET sort_order = 101 WHERE message_name = 'feminist';
UPDATE message_conveyed SET sort_order = 102 WHERE message_name = 'ecological';
UPDATE message_conveyed SET sort_order = 103 WHERE message_name = 'political';
UPDATE message_conveyed SET sort_order = 104 WHERE message_name = 'anti establishment';
UPDATE message_conveyed SET sort_order = 105 WHERE message_name = 'nostalgic';
UPDATE message_conveyed SET sort_order = 106 WHERE message_name = 'patriotic';
UPDATE message_conveyed SET sort_order = 107 WHERE message_name = 'traditionalist/way of life';
-- Group 2: Comedy & satire
UPDATE message_conveyed SET sort_order = 200 WHERE message_name = 'parodic';
UPDATE message_conveyed SET sort_order = 201 WHERE message_name = 'satirical';
UPDATE message_conveyed SET sort_order = 202 WHERE message_name = 'absurdist';
UPDATE message_conveyed SET sort_order = 203 WHERE message_name = 'revisionist/alternate history';
-- Group 3: Reflection
UPDATE message_conveyed SET sort_order = 300 WHERE message_name = 'philosophical';
UPDATE message_conveyed SET sort_order = 301 WHERE message_name = 'metaphysical';
-- Group 4: Artistic expression
UPDATE message_conveyed SET sort_order = 400 WHERE message_name = 'dreamlike';
UPDATE message_conveyed SET sort_order = 401 WHERE message_name = 'surreal';
UPDATE message_conveyed SET sort_order = 402 WHERE message_name = 'symbolic';
UPDATE message_conveyed SET sort_order = 403 WHERE message_name = 'poetic';

-- =============================================================================
-- CINEMA TYPES
-- =============================================================================

-- Renames
UPDATE cinema_type SET technique_name = 'franchise' WHERE technique_name = 'Collection';
UPDATE cinema_type SET technique_name = 'costume/period drama' WHERE technique_name = 'costume';

-- New tags
INSERT INTO cinema_type (technique_name, sort_order) VALUES
    ('few/no dialogs', 406),
    ('giallo', 510)
ON CONFLICT (technique_name) DO NOTHING;

-- Move dialogs, slang dialogs, voiceover from Group 5 to Group 4
-- Move black comedy already handled above (from messages)

-- Update all sort_orders
-- Group 1: Visual techniques & aesthetics
UPDATE cinema_type SET sort_order = 100 WHERE technique_name = 'animation';
UPDATE cinema_type SET sort_order = 101 WHERE technique_name = 'mixed animation';
UPDATE cinema_type SET sort_order = 102 WHERE technique_name = 'CGI';
UPDATE cinema_type SET sort_order = 103 WHERE technique_name = '3D';
UPDATE cinema_type SET sort_order = 104 WHERE technique_name = 'motion capture';
UPDATE cinema_type SET sort_order = 105 WHERE technique_name = 'black and white';
UPDATE cinema_type SET sort_order = 106 WHERE technique_name = 'aesthetics';
-- Group 2: Movements & eras
UPDATE cinema_type SET sort_order = 200 WHERE technique_name = 'silent';
UPDATE cinema_type SET sort_order = 201 WHERE technique_name = 'expressionism';
UPDATE cinema_type SET sort_order = 202 WHERE technique_name = 'realism';
UPDATE cinema_type SET sort_order = 203 WHERE technique_name = 'neo-realism';
UPDATE cinema_type SET sort_order = 204 WHERE technique_name = 'noir';
UPDATE cinema_type SET sort_order = 205 WHERE technique_name = 'hollywood golden age';
UPDATE cinema_type SET sort_order = 206 WHERE technique_name = 'new hollywood';
UPDATE cinema_type SET sort_order = 207 WHERE technique_name = 'new wave';
UPDATE cinema_type SET sort_order = 208 WHERE technique_name = 'neo-noir';
-- Group 3: Industry & culture
UPDATE cinema_type SET sort_order = 300 WHERE technique_name = 'blockbuster';
UPDATE cinema_type SET sort_order = 301 WHERE technique_name = 'art house';
UPDATE cinema_type SET sort_order = 302 WHERE technique_name = 'franchise';
UPDATE cinema_type SET sort_order = 303 WHERE technique_name = 'B';
UPDATE cinema_type SET sort_order = 304 WHERE technique_name = 'generational';
UPDATE cinema_type SET sort_order = 305 WHERE technique_name = 'popular culture';
-- Group 4: Narrative techniques
UPDATE cinema_type SET sort_order = 400 WHERE technique_name = 'sequence-shot';
UPDATE cinema_type SET sort_order = 401 WHERE technique_name = 'found footage';
UPDATE cinema_type SET sort_order = 402 WHERE technique_name = 'multi-sequence';
UPDATE cinema_type SET sort_order = 403 WHERE technique_name = 'slow cinema';
UPDATE cinema_type SET sort_order = 404 WHERE technique_name = 'non linear narrative';
UPDATE cinema_type SET sort_order = 405 WHERE technique_name = 'dogma';
UPDATE cinema_type SET sort_order = 406 WHERE technique_name = 'dialogs';
UPDATE cinema_type SET sort_order = 407 WHERE technique_name = 'slang dialogs';
UPDATE cinema_type SET sort_order = 408 WHERE technique_name = 'few/no dialogs';
UPDATE cinema_type SET sort_order = 409 WHERE technique_name = 'voiceover';
-- Group 5: Cinema archetypes
UPDATE cinema_type SET sort_order = 500 WHERE technique_name = 'western';
UPDATE cinema_type SET sort_order = 501 WHERE technique_name = 'peplum';
UPDATE cinema_type SET sort_order = 502 WHERE technique_name = 'swashbuckler';
UPDATE cinema_type SET sort_order = 503 WHERE technique_name = 'costume/period drama';
UPDATE cinema_type SET sort_order = 504 WHERE technique_name = 'wu xia pian';
UPDATE cinema_type SET sort_order = 505 WHERE technique_name = 'blaxploitation';
UPDATE cinema_type SET sort_order = 506 WHERE technique_name = 'giallo';
UPDATE cinema_type SET sort_order = 507 WHERE technique_name = 'slasher';
UPDATE cinema_type SET sort_order = 508 WHERE technique_name = 'black comedy';
UPDATE cinema_type SET sort_order = 509 WHERE technique_name = 'docufiction';

COMMIT;
