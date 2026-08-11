-- =============================================================================
-- Migration 026: Taxonomy v2 — 9 dimensions become 7
-- =============================================================================
-- Source of truth: "Taxonomy dimensions & tags.txt" (project root)
--
-- The `motivation_relation` and `message_conveyed` dimensions are dissolved:
-- their tags move into `category` (Genre), `theme_context` (Theme) and
-- `atmosphere`. Tags are also renamed, merged and added, and every dimension
-- receives a new sort_order layout (one block of 100 per named sub-dimension).
--
-- EVERY existing film<->tag association is preserved (except `world-saving`,
-- which is explicitly discarded). Merged tags deduplicate via ON CONFLICT.
--
-- The tables motivation_relation / message_conveyed / film_motivation /
-- film_message are NOT dropped — they are left empty so the recommender,
-- dashboard and games keep running until Step 22.
--
-- Structure:
--   Part 0  — pre-flight snapshot (for the reconciliation assertion)
--   Part 1  — same-dimension renames
--   Part 2  — cross-dimension moves + merges + discard
--   Part 3  — new tags
--   Part 4  — full sort_order rewrite (authoritative layout)
--   Part 4b — tag_description follow-up
--   Part 5  — assertions + post-flight report
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Pre-requisite: make flat Genre rows (historic_subcategory_name IS NULL)
-- properly unique.
--
-- The table-level UNIQUE (category_name, historic_subcategory_name) uses the
-- default NULLS DISTINCT semantics, so ('war', NULL) does NOT conflict with an
-- existing ('war', NULL) row — ON CONFLICT never fires and duplicates creep in.
-- Taxonomy v2 makes ALL genres flat rows, so we need a partial unique index to
-- get a real conflict target (and to keep seed_taxonomy.sql idempotent).
-- -----------------------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS uq_category_name_no_subcategory
    ON category (category_name)
    WHERE historic_subcategory_name IS NULL;

-- =============================================================================
-- PART 0 — Pre-flight snapshot
-- =============================================================================

CREATE TEMP TABLE tax_before ON COMMIT DROP AS
SELECT
    (SELECT count(*) FROM film_genre)
  + (SELECT count(*) FROM film_theme)
  + (SELECT count(*) FROM film_technique)
  + (SELECT count(*) FROM film_place)
  + (SELECT count(*) FROM film_period)
  + (SELECT count(*) FROM film_atmosphere)
  + (SELECT count(*) FROM film_character_context)
  + (SELECT count(*) FROM film_motivation)
  + (SELECT count(*) FROM film_message)                          AS pairs_before,
    (SELECT count(*) FROM film_motivation fm
       JOIN motivation_relation m USING (motivation_id)
      WHERE m.motivation_name = 'world-saving')                  AS n_world_saving,
    (SELECT count(*) FROM (
        SELECT film_id FROM film_theme JOIN theme_context USING (theme_context_id)
         WHERE theme_name = 'mafia'
        INTERSECT
        SELECT film_id FROM film_theme JOIN theme_context USING (theme_context_id)
         WHERE theme_name = 'organized crime') x)                AS ov_mafia,
    (SELECT count(*) FROM (
        SELECT film_id FROM film_motivation JOIN motivation_relation USING (motivation_id)
         WHERE motivation_name = 'odyssey'
        INTERSECT
        SELECT film_id FROM film_motivation JOIN motivation_relation USING (motivation_id)
         WHERE motivation_name = 'quest') x)                     AS ov_odyssey,
    (SELECT count(*) FROM (
        SELECT film_id FROM film_message JOIN message_conveyed USING (message_id)
         WHERE message_name = 'dreamlike'
        INTERSECT
        SELECT film_id FROM film_message JOIN message_conveyed USING (message_id)
         WHERE message_name = 'surreal') x)                      AS ov_dreamlike,
    (SELECT count(*) FROM (
        SELECT film_id FROM film_message JOIN message_conveyed USING (message_id)
         WHERE message_name = 'political'
        INTERSECT
        SELECT film_id FROM film_theme JOIN theme_context USING (theme_context_id)
         WHERE theme_name = 'political') x)                      AS ov_political;

DO $$
DECLARE b record;
BEGIN
    SELECT * INTO b FROM tax_before;
    RAISE NOTICE '--- BEFORE -------------------------------------------------';
    RAISE NOTICE 'film<->tag pairs across 9 dimensions : %', b.pairs_before;
    RAISE NOTICE 'world-saving associations (discarded): %', b.n_world_saving;
    RAISE NOTICE 'merge overlaps (deduplicated)        : mafia=% odyssey=% dreamlike=% political=%',
                 b.ov_mafia, b.ov_odyssey, b.ov_dreamlike, b.ov_political;
END $$;

-- =============================================================================
-- PART 1 — Same-dimension renames (lookup UPDATE, associations preserved)
-- =============================================================================

-- theme_context
UPDATE theme_context SET theme_name = 'class/culture clash' WHERE theme_name = 'class struggle';
UPDATE theme_context SET theme_name = 'trafficking/fraud'   WHERE theme_name = 'organized fraud';
UPDATE theme_context SET theme_name = 'grief/mourning'      WHERE theme_name = 'mourning';
UPDATE theme_context SET theme_name = 'nature/wildlife'     WHERE theme_name = 'nature';
UPDATE theme_context SET theme_name = 'art: music/dance'    WHERE theme_name = 'art: music';

-- place_context
UPDATE place_context SET environment = 'rural' WHERE environment = 'country';

-- character_context
UPDATE character_context SET context_name = 'female lead'    WHERE context_name = 'female';
UPDATE character_context SET context_name = 'sex worker'     WHERE context_name = 'prostitute';
UPDATE character_context SET context_name = 'witch/wizard'   WHERE context_name = 'witch';
UPDATE character_context SET context_name = 'animal'         WHERE context_name = 'animal/wildlife';
UPDATE character_context SET context_name = 'devil'          WHERE context_name = 'evil';
UPDATE character_context SET context_name = 'android/robot'  WHERE context_name = 'android';

-- cinema_type
UPDATE cinema_type SET technique_name = 'chapters/multi-sequence' WHERE technique_name = 'multi-sequence';
UPDATE cinema_type SET technique_name = 'flashback/non linear'    WHERE technique_name = 'non linear narrative';
UPDATE cinema_type SET technique_name = 'dialogs/punchline'       WHERE technique_name = 'dialogs';

-- time_context
UPDATE time_context SET time_period = '2000-2010''s'  WHERE time_period = 'early 21st';
UPDATE time_context SET time_period = '1980-90''s'    WHERE time_period = 'end 20th';
UPDATE time_context SET time_period = '1950-60-70''s' WHERE time_period = '20th post-war';
UPDATE time_context SET time_period = '1920-30''s'    WHERE time_period = 'interwar';
UPDATE time_context SET time_period = '1900-1910''s'  WHERE time_period = 'early 20th';

-- Mirror of the list above, keyed by tag_description.dimension (see Part 4b)
CREATE TEMP TABLE tax_rename (dim text, old_name text, new_name text) ON COMMIT DROP;
INSERT INTO tax_rename (dim, old_name, new_name) VALUES
    ('themes',         'class struggle',       'class/culture clash'),
    ('themes',         'organized fraud',      'trafficking/fraud'),
    ('themes',         'mourning',             'grief/mourning'),
    ('themes',         'nature',               'nature/wildlife'),
    ('themes',         'art: music',           'art: music/dance'),
    ('place_contexts', 'country',              'rural'),
    ('characters',     'female',               'female lead'),
    ('characters',     'prostitute',           'sex worker'),
    ('characters',     'witch',                'witch/wizard'),
    ('characters',     'animal/wildlife',      'animal'),
    ('characters',     'evil',                 'devil'),
    ('characters',     'android',              'android/robot'),
    ('cinema_types',   'multi-sequence',       'chapters/multi-sequence'),
    ('cinema_types',   'non linear narrative', 'flashback/non linear'),
    ('cinema_types',   'dialogs',              'dialogs/punchline'),
    ('time_periods',   'early 21st',           '2000-2010''s'),
    ('time_periods',   'end 20th',             '1980-90''s'),
    ('time_periods',   '20th post-war',        '1950-60-70''s'),
    ('time_periods',   'interwar',             '1920-30''s'),
    ('time_periods',   'early 20th',           '1900-1910''s');

-- =============================================================================
-- PART 2 — Cross-dimension moves (junction data migrated), merges, discard
-- =============================================================================

-- Registry of the dimensions involved in a move, so the migration loop below
-- can be written once instead of ten times.
CREATE TEMP TABLE tax_dim (
    dim       text PRIMARY KEY,   -- tag_description / API dimension key
    lookup    text NOT NULL,      -- lookup table
    name_col  text NOT NULL,      -- tag-name column of the lookup table
    id_col    text NOT NULL,      -- PK of the lookup table
    junction  text NOT NULL,      -- film<->tag junction table
    fk_col    text NOT NULL       -- lookup FK column in the junction table
) ON COMMIT DROP;

INSERT INTO tax_dim (dim, lookup, name_col, id_col, junction, fk_col) VALUES
    ('categories',   'category',            'category_name',   'category_id',        'film_genre',      'category_id'),
    ('themes',       'theme_context',       'theme_name',      'theme_context_id',   'film_theme',      'theme_context_id'),
    ('atmospheres',  'atmosphere',          'atmosphere_name', 'atmosphere_id',      'film_atmosphere', 'atmosphere_id'),
    ('cinema_types', 'cinema_type',         'technique_name',  'cinema_type_id',     'film_technique',  'cinema_type_id'),
    ('motivations',  'motivation_relation', 'motivation_name', 'motivation_id',      'film_motivation', 'motivation_id'),
    ('messages',     'message_conveyed',    'message_name',    'message_id',         'film_message',    'message_id');

-- The move map. `sort_order` is the FINAL sort_order from Part 4 (Part 4 rewrites
-- everything anyway, but seeding it here keeps intermediate states sane).
-- Two source rows sharing a target_tag = a merge; the second one finds the row
-- created by the first and its junction rows deduplicate via ON CONFLICT.
CREATE TEMP TABLE tax_move (
    source_dim text NOT NULL,
    source_tag text NOT NULL,
    target_dim text NOT NULL,
    target_tag text NOT NULL,
    sort_order integer NOT NULL,
    PRIMARY KEY (source_dim, source_tag)
) ON COMMIT DROP;

INSERT INTO tax_move (source_dim, source_tag, target_dim, target_tag, sort_order) VALUES
    -- themes -> categories (19 moves + the mafia/organized crime merge)
    ('themes', 'tragedy',                  'categories', 'tragedy',                  203),
    ('themes', 'psychological',            'categories', 'psychological',            400),
    ('themes', 'war',                      'categories', 'war',                      401),
    ('themes', 'crime',                    'categories', 'crime',                    402),
    ('themes', 'investigation',            'categories', 'investigation',            403),
    ('themes', 'spy',                      'categories', 'spy',                      404),
    ('themes', 'heist',                    'categories', 'heist',                    405),
    ('themes', 'mafia',                    'categories', 'mafia/organized crime',    406),
    ('themes', 'organized crime',          'categories', 'mafia/organized crime',    406),
    ('themes', 'serial killer',            'categories', 'serial killer',            407),
    ('themes', 'survival',                 'categories', 'survival',                 408),
    ('themes', 'chase/escape',             'categories', 'chase/escape',             409),
    ('themes', 'disaster',                 'categories', 'disaster',                 411),
    ('themes', 'apocalypse',               'categories', 'apocalypse',               412),
    ('themes', 'trial/judicial chronicle', 'categories', 'trial/judicial chronicle', 500),
    ('themes', 'prison',                   'categories', 'prison',                   501),
    ('themes', 'supernatural',             'categories', 'supernatural',             600),
    ('themes', 'whimsical/zany',           'categories', 'whimsical/zany',           601),
    ('themes', 'dystopia',                 'categories', 'dystopia',                 602),
    ('themes', 'tales and legends',        'categories', 'tales and legends',        603),
    ('themes', 'martial arts',             'categories', 'martial arts',             801),

    -- messages -> categories
    ('messages', 'parodic',                       'categories', 'parodic',                       300),
    ('messages', 'satirical',                     'categories', 'satirical',                     301),
    ('messages', 'absurdist',                     'categories', 'absurdist',                     302),
    ('messages', 'revisionist/alternate history', 'categories', 'revisionist/alternate history', 509),

    -- messages -> themes ('political' fuses into the existing theme of the same name)
    ('messages', 'political',                   'themes', 'political',                   103),
    ('messages', 'humanist',                    'themes', 'humanist',                    200),
    ('messages', 'feminist',                    'themes', 'feminist',                    201),
    ('messages', 'nostalgic',                   'themes', 'nostalgic',                   202),
    ('messages', 'ecological',                  'themes', 'ecological',                  203),
    ('messages', 'patriotic',                   'themes', 'patriotic',                   204),
    ('messages', 'anti establishment',          'themes', 'anti establishment',          205),
    ('messages', 'traditionalist/way of life',  'themes', 'traditionalist/way of life',  206),
    ('messages', 'philosophical',               'themes', 'philosophical',               207),
    ('messages', 'metaphysical',                'themes', 'metaphysical',                208),

    -- messages -> atmospheres (dreamlike + surreal merge)
    ('messages', 'symbolic',  'atmospheres', 'symbolic',          407),
    ('messages', 'dreamlike', 'atmospheres', 'dreamlike/surreal', 408),
    ('messages', 'surreal',   'atmospheres', 'dreamlike/surreal', 408),
    ('messages', 'poetic',    'atmospheres', 'poetic',            409),

    -- cinema_types -> categories
    ('cinema_types', 'black comedy',              'categories', 'black comedy',              303),
    ('cinema_types', 'biopic',                    'categories', 'biopic',                    502),
    ('cinema_types', 'fait divers/true incident', 'categories', 'fait divers/true incident', 503),
    ('cinema_types', 'western',                   'categories', 'western',                   504),
    ('cinema_types', 'peplum',                    'categories', 'peplum',                    505),
    ('cinema_types', 'swashbuckler',              'categories', 'swashbuckler',              506),
    ('cinema_types', 'costume drama',             'categories', 'costume drama',             507),
    ('cinema_types', 'wu xia pian',               'categories', 'wu xia pian',               508),
    ('cinema_types', 'slasher',                   'categories', 'slasher',                   701),
    ('cinema_types', 'docufiction',               'categories', 'docufiction',               800),

    -- cinema_types -> themes
    ('cinema_types', 'generational', 'themes', 'generational', 102),

    -- motivations -> categories (odyssey + quest merge)
    ('motivations', 'odyssey', 'categories', 'odyssey/quest', 410),
    ('motivations', 'quest',   'categories', 'odyssey/quest', 410),

    -- motivations -> themes
    ('motivations', 'love',            'themes', 'love',            300),
    ('motivations', 'friendship',      'themes', 'friendship',      301),
    ('motivations', 'solidarity',      'themes', 'solidarity',      302),
    ('motivations', 'communication',   'themes', 'communication',   303),
    ('motivations', 'power',           'themes', 'power',           400),
    ('motivations', 'manipulation',    'themes', 'manipulation',    401),
    ('motivations', 'sex',             'themes', 'sex',             402),
    ('motivations', 'adultery',        'themes', 'adultery',        403),
    ('motivations', 'jealousy',        'themes', 'jealousy',        404),
    ('motivations', 'perversion',      'themes', 'perversion',      405),
    ('motivations', 'rivalry',         'themes', 'rivalry',         501),
    ('motivations', 'fight',           'themes', 'fight',           502),
    ('motivations', 'rebellion/revolt','themes', 'rebellion/revolt',503),
    ('motivations', 'vengeance',       'themes', 'vengeance',       504),
    ('motivations', 'harassment',      'themes', 'harassment',      505),
    ('motivations', 'obsession',       'themes', 'obsession',       800),
    ('motivations', 'greed/ambition',  'themes', 'greed/ambition',  801),
    ('motivations', 'doubt/dilemma',   'themes', 'doubt/dilemma',   802),
    ('motivations', 'lie',             'themes', 'lie',             803),
    ('motivations', 'sacrifice',       'themes', 'sacrifice',       804),
    ('motivations', 'honor/duty',      'themes', 'honor/duty',      805),
    ('motivations', 'emancipation',    'themes', 'emancipation',    806),
    ('motivations', 'redemption',      'themes', 'redemption',      807),
    ('motivations', 'invasion',        'themes', 'invasion',        1206),

    -- atmospheres -> categories
    ('atmospheres', 'gore', 'categories', 'gore', 702);

-- Execute the moves: ensure target row -> migrate junction rows -> drop source
-- row (the FK cascade removes the source junction rows).
DO $$
DECLARE
    m      record;
    s      record;
    t      record;
    new_id integer;
    n_src  integer;
BEGIN
    FOR m IN SELECT * FROM tax_move ORDER BY source_dim, source_tag LOOP
        SELECT * INTO s FROM tax_dim WHERE dim = m.source_dim;
        SELECT * INTO t FROM tax_dim WHERE dim = m.target_dim;

        -- The source tag must exist, otherwise the map is out of date.
        EXECUTE format('SELECT count(*) FROM %I WHERE %I = $1', s.lookup, s.name_col)
            INTO n_src USING m.source_tag;
        IF n_src = 0 THEN
            RAISE EXCEPTION 'Move source not found: %.%', m.source_dim, m.source_tag;
        END IF;

        -- 1. Ensure the target lookup row exists.
        IF m.target_dim = 'categories' THEN
            -- Flat Genre row: historic_subcategory_name stays NULL.
            INSERT INTO category (category_name, historic_subcategory_name, sort_order)
            VALUES (m.target_tag, NULL, m.sort_order)
            ON CONFLICT (category_name) WHERE historic_subcategory_name IS NULL DO NOTHING;

            SELECT category_id INTO new_id
              FROM category
             WHERE category_name = m.target_tag AND historic_subcategory_name IS NULL;
        ELSE
            EXECUTE format(
                'INSERT INTO %I (%I, sort_order) VALUES ($1, $2) ON CONFLICT (%I) DO NOTHING',
                t.lookup, t.name_col, t.name_col
            ) USING m.target_tag, m.sort_order;

            EXECUTE format('SELECT %I FROM %I WHERE %I = $1', t.id_col, t.lookup, t.name_col)
                INTO new_id USING m.target_tag;
        END IF;

        -- 2. Migrate the film associations.
        EXECUTE format(
            'INSERT INTO %I (film_id, %I) '
            'SELECT j.film_id, $1 FROM %I j JOIN %I l ON l.%I = j.%I WHERE l.%I = $2 '
            'ON CONFLICT DO NOTHING',
            t.junction, t.fk_col,
            s.junction, s.lookup, s.id_col, s.fk_col, s.name_col
        ) USING new_id, m.source_tag;

        -- 3. Drop the source lookup row (cascade cleans the source junction).
        EXECUTE format('DELETE FROM %I WHERE %I = $1', s.lookup, s.name_col)
            USING m.source_tag;
    END LOOP;
END $$;

-- Discarded tag: associations are intentionally dropped.
DELETE FROM motivation_relation WHERE motivation_name = 'world-saving';

-- =============================================================================
-- PART 3 — New tags (no film associations yet)
-- =============================================================================

INSERT INTO category (category_name, historic_subcategory_name, sort_order) VALUES
    ('melodrama',     NULL, 200),
    ('coming of age', NULL, 201),
    ('slice of life', NULL, 202),
    ('jumpscare',     NULL, 700),
    ('body horror',   NULL, 703),
    ('gothic horror', NULL, 704),
    ('folk horror',   NULL, 705)
ON CONFLICT (category_name) WHERE historic_subcategory_name IS NULL DO NOTHING;

INSERT INTO theme_context (theme_name, sort_order) VALUES
    ('conspiracy',        108),
    ('family/parenthood', 304),
    ('loneliness',        707),
    ('guilt',             708),
    ('contest',           1104),
    ('exploration',       1207)
ON CONFLICT (theme_name) DO NOTHING;

INSERT INTO time_context (time_period, sort_order) VALUES
    ('single day',       100),
    ('several years',    101),
    ('decades-spanning', 102)
ON CONFLICT (time_period) DO NOTHING;

INSERT INTO place_context (environment, sort_order) VALUES
    ('small town', 101),
    ('planet',     111),
    ('castle',     208),
    ('hotel',      209),
    ('car/bus',    400),
    ('train',      401),
    ('airplane',   402)
ON CONFLICT (environment) DO NOTHING;

INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    ('edge of your seat', 301)
ON CONFLICT (atmosphere_name) DO NOTHING;

INSERT INTO character_context (context_name, sort_order) VALUES
    ('male ensemble', 205),
    ('chosen one',    501),
    ('secret agent',  507),
    ('warrior',       511),
    ('knight',        512)
ON CONFLICT (context_name) DO NOTHING;

INSERT INTO cinema_type (technique_name, sort_order) VALUES
    ('real time',        302),
    ('timelapse',        303),
    ('slow-motion',      304),
    ('split screen',     306),
    ('musical montage',  307),
    ('monologue',        404),
    ('fourth wall break',405)
ON CONFLICT (technique_name) DO NOTHING;

-- =============================================================================
-- PART 4 — Authoritative sort_order layout (rewrites every tag)
-- Blocks of 100 = one named sub-dimension; order inside a block is the
-- document order and drives the sidebar rendering.
-- =============================================================================

-- ---- category (Genre) — 55 tags -------------------------------------------
UPDATE category c SET sort_order = v.so
FROM (VALUES
    -- 100s Main
    ('Drama',100),('Comedy',101),('Romance',102),('Historical',103),('Action',104),
    ('Adventure',105),('Thriller',106),('Science-Fiction',107),('Fantasy',108),
    ('Horror',109),('Musical',110),('Documentary',111),
    -- 200s Drama / Romance
    ('melodrama',200),('coming of age',201),('slice of life',202),('tragedy',203),
    -- 300s Comedy
    ('parodic',300),('satirical',301),('absurdist',302),('black comedy',303),
    -- 400s Thriller / Adventure
    ('psychological',400),('war',401),('crime',402),('investigation',403),('spy',404),
    ('heist',405),('mafia/organized crime',406),('serial killer',407),('survival',408),
    ('chase/escape',409),('odyssey/quest',410),('disaster',411),('apocalypse',412),
    -- 500s Historical / Justice
    ('trial/judicial chronicle',500),('prison',501),('biopic',502),
    ('fait divers/true incident',503),('western',504),('peplum',505),('swashbuckler',506),
    ('costume drama',507),('wu xia pian',508),('revisionist/alternate history',509),
    -- 600s Sci-fi / Fantasy
    ('supernatural',600),('whimsical/zany',601),('dystopia',602),('tales and legends',603),
    -- 700s Horror
    ('jumpscare',700),('slasher',701),('gore',702),('body horror',703),
    ('gothic horror',704),('folk horror',705),
    -- 800s Miscellaneous
    ('docufiction',800),('martial arts',801)
) AS v(name, so)
WHERE c.category_name = v.name AND c.historic_subcategory_name IS NULL;

-- ---- theme_context (Theme) — 96 tags ---------------------------------------
UPDATE theme_context t SET sort_order = v.so
FROM (VALUES
    -- 100s Society & World
    ('social',100),('societal',101),('generational',102),('political',103),('religion',104),
    ('business',105),('journalism/media',106),('censorship',107),('conspiracy',108),
    ('sect',109),('immigration',110),('colonialism',111),('slavery',112),
    ('nature/wildlife',113),('AI/technology',114),
    -- 200s Values & Reflection
    ('humanist',200),('feminist',201),('nostalgic',202),('ecological',203),('patriotic',204),
    ('anti establishment',205),('traditionalist/way of life',206),('philosophical',207),
    ('metaphysical',208),
    -- 300s Bonds & attachments
    ('love',300),('friendship',301),('solidarity',302),('communication',303),
    ('family/parenthood',304),
    -- 400s Desire & transgression
    ('power',400),('manipulation',401),('sex',402),('adultery',403),('jealousy',404),
    ('perversion',405),
    -- 500s Interpersonal conflict
    ('class/culture clash',500),('rivalry',501),('fight',502),('rebellion/revolt',503),
    ('vengeance',504),('harassment',505),
    -- 600s Crime & abuse of power
    ('delinquency',600),('police violence',601),('sex crime',602),('kidnapping/hostage',603),
    ('trafficking/fraud',604),('corruption',605),('terrorism',606),
    -- 700s Wounds & burdens
    ('trauma/accident',700),('identity crisis',701),('illness',702),('amnesia',703),
    ('death',704),('grief/mourning',705),('addiction/drugs',706),('loneliness',707),
    ('guilt',708),
    -- 800s Drives & arcs
    ('obsession',800),('greed/ambition',801),('doubt/dilemma',802),('lie',803),
    ('sacrifice',804),('honor/duty',805),('emancipation',806),('redemption',807),
    ('transformation',808),('time passing',809),('dream',810),
    -- 900s Art
    ('art',900),('art: music/dance',901),('art: cinema',902),('art: literature',903),
    ('art: fashion',904),('art: painting',905),('art: sculpture',906),('art: theatre',907),
    ('art: radio',908),('art: architecture',909),
    -- 1000s Sport
    ('sport',1000),('sport: individual',1001),('sport: collective',1002),
    ('sport: tournament',1003),('sport: motor',1004),
    -- 1100s Entertainment
    ('food/cooking',1100),('party',1101),('game',1102),('gambling',1103),('contest',1104),
    -- 1200s Face to the unknown
    ('sorcery',1200),('alien contact',1201),('paranormal',1202),('curse',1203),
    ('time travel/loop',1204),('virtual/parallel universe',1205),('invasion',1206),
    ('exploration',1207)
) AS v(name, so)
WHERE t.theme_name = v.name;

-- ---- time_context (Time Period) — 22 tags ----------------------------------
UPDATE time_context tc SET sort_order = v.so
FROM (VALUES
    -- 1-15 Chronological
    ('future',1),('contemporary',2),('2000-2010''s',3),('1980-90''s',4),('1950-60-70''s',5),
    ('WW2',6),('1920-30''s',7),('WW1',8),('1900-1910''s',9),('19th',10),('modern age',11),
    ('medieval',12),('antiquity',13),('prehistoric',14),('undetermined',15),
    -- 100s Time span
    ('single day',100),('several years',101),('decades-spanning',102),
    -- 200s Seasons
    ('spring',200),('summer',201),('autumn',202),('winter',203)
) AS v(name, so)
WHERE tc.time_period = v.name;

-- ---- place_context (Place) — 29 tags ---------------------------------------
UPDATE place_context p SET sort_order = v.so
FROM (VALUES
    -- 100s Environments
    ('urban',100),('small town',101),('rural',102),('forest',103),('mountains',104),
    ('desert',105),('beach',106),('maritime',107),('island',108),('underground',109),
    ('space',110),('planet',111),
    -- 200s Buildings & institutions
    ('building',200),('household/house/apartment',201),('company/factory',202),
    ('school/university',203),('hospital',204),('jail',205),('military',206),('naval',207),
    ('castle',208),('hotel',209),
    -- 300s Narrative settings
    ('road movie',300),('huis clos/confined setting',301),
    -- 400s Vehicles
    ('car/bus',400),('train',401),('airplane',402),('ship',403),
    -- 500 None
    ('no particular',500)
) AS v(name, so)
WHERE p.environment = v.name;

-- ---- atmosphere (Atmosphere) — 25 tags -------------------------------------
UPDATE atmosphere a SET sort_order = v.so
FROM (VALUES
    -- 100s Light / Joyful
    ('family-friendly',100),('feel good',101),('crazy/nutty',102),('delicate/intimate',103),
    -- 200s Dark / Extreme
    ('depressive/sad',200),('violent',201),('disturbing',202),('steamy',203),('sordid',204),
    -- 300s Pace, Tension & Scale
    ('epic',300),('edge of your seat',301),('mysterious',302),('oppressive',303),
    ('claustrophobic',304),('contemplative/meditative',305),
    -- 400s Artistic Directing
    ('cityscape',400),('pastoral',401),('gritty/realistic',402),('meticulous',403),
    ('hypnotic/immersive',404),('psychedelic',405),('ethereal',406),('symbolic',407),
    ('dreamlike/surreal',408),('poetic',409)
) AS v(name, so)
WHERE a.atmosphere_name = v.name;

-- ---- character_context (Character) — 59 tags -------------------------------
UPDATE character_context cc SET sort_order = v.so
FROM (VALUES
    -- 100s Group structure
    ('solitary',100),('tandem',101),('trio',102),('couple',103),('relatives',104),
    ('generations',105),('buddies',106),('team/group/gang',107),('ensemble cast',108),
    -- 200s Age & identity
    ('childhood',200),('teenager',201),('elderly',202),('adult/child',203),('female lead',204),
    ('male ensemble',205),('LGBT',206),('interracial',207),
    -- 300s Social status & traits
    ('ordinary',300),('poor/marginal',301),('wealthy',302),('genius',303),
    ('simpleton/fool',304),('loser',305),('star/celebrity',306),('disturbed/madness',307),
    ('disabled',308),('outcast/misfit',309),('sex worker',310),('psychopath',311),
    -- 400s Narrative devices
    ('double',400),('cross-dressing',401),('unreliable narrator',402),
    -- 500s Archetypes - human
    ('super hero',500),('chosen one',501),('antihero',502),('scientist/researcher',503),
    ('mentor',504),('cop',505),('detective',506),('secret agent',507),('vigilante',508),
    ('gangster',509),('soldier',510),('warrior',511),('knight',512),('samurai',513),
    ('pirate',514),('viking',515),('witch/wizard',516),('femme fatale',517),
    -- 600s Non-human & creatures
    ('animal',600),('monster/terrestrial creature',601),('devil',602),('ghost/spirit',603),
    ('vampire',604),('zombie',605),('alien',606),('android/robot',607),('vehicle',608)
) AS v(name, so)
WHERE cc.context_name = v.name;

-- ---- cinema_type (Cinema Type) — 40 tags -----------------------------------
UPDATE cinema_type ct SET sort_order = v.so
FROM (VALUES
    -- 100s Visual techniques
    ('animation',100),('mixed animation',101),('CGI',102),('3D',103),('motion capture',104),
    ('black and white',105),('aesthetics',106),('found footage',107),('dogma',108),
    -- 200s Industry & culture
    ('blockbuster',200),('art house',201),('B',202),('franchise',203),('popular culture',204),
    -- 300s Sequencing
    ('chapters/multi-sequence',300),('flashback/non linear',301),('real time',302),
    ('timelapse',303),('slow-motion',304),('sequence-shot',305),('split screen',306),
    ('musical montage',307),
    -- 400s Voice & Dialogue
    ('dialogs/punchline',400),('slang dialogs',401),('few/no dialogs',402),('voiceover',403),
    ('monologue',404),('fourth wall break',405),
    -- 500s Movements & eras
    ('silent',500),('expressionism',501),('realism',502),('neo-realism',503),('noir',504),
    ('hollywood golden age',505),('new hollywood',506),('new wave',507),('slow cinema',508),
    ('neo-noir',509),('blaxploitation',510),('giallo',511)
) AS v(name, so)
WHERE ct.technique_name = v.name;

-- =============================================================================
-- PART 4b — tag_description follow-up
-- =============================================================================

-- Merge sources first: two rows would collide on the (dimension, tag_name) PK.
DELETE FROM tag_description WHERE (dimension, tag_name) IN (
    ('motivations', 'world-saving'),
    ('motivations', 'odyssey'),
    ('motivations', 'quest'),
    ('themes',      'mafia'),
    ('themes',      'organized crime'),
    ('messages',    'dreamlike'),
    ('messages',    'surreal')
);

-- Keep a description for the merged atmosphere tag (built from the two old ones).
INSERT INTO tag_description (dimension, tag_name, description) VALUES
    ('atmospheres', 'dreamlike/surreal',
     'Floating, oneiric texture and/or deliberate juxtapositions of impossible or irrational elements - dream-like regardless of whether actual dreams appear')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- Renames (Part 1) and moves (Part 2), applied to the description rows.
UPDATE tag_description td SET tag_name = r.new_name
FROM tax_rename r
WHERE td.dimension = r.dim AND td.tag_name = r.old_name;

UPDATE tag_description td SET dimension = m.target_dim, tag_name = m.target_tag
FROM tax_move m
WHERE td.dimension = m.source_dim AND td.tag_name = m.source_tag;

-- Nothing may remain under the dissolved dimensions.
DELETE FROM tag_description WHERE dimension IN ('motivations', 'messages');

-- =============================================================================
-- PART 5 — Assertions + post-flight report
-- =============================================================================

DO $$
DECLARE
    b              record;
    n              integer;
    pairs_after    bigint;
    pairs_expected bigint;
BEGIN
    SELECT * INTO b FROM tax_before;

    -- 1. The dissolved dimensions must be empty (but still present).
    SELECT count(*) INTO n FROM motivation_relation;
    IF n <> 0 THEN RAISE EXCEPTION 'motivation_relation still has % row(s)', n; END IF;
    SELECT count(*) INTO n FROM message_conveyed;
    IF n <> 0 THEN RAISE EXCEPTION 'message_conveyed still has % row(s)', n; END IF;
    SELECT count(*) INTO n FROM film_motivation;
    IF n <> 0 THEN RAISE EXCEPTION 'film_motivation still has % row(s)', n; END IF;
    SELECT count(*) INTO n FROM film_message;
    IF n <> 0 THEN RAISE EXCEPTION 'film_message still has % row(s)', n; END IF;

    -- 2. Per-dimension tag counts.
    SELECT count(*) INTO n FROM category;
    IF n <> 55 THEN RAISE EXCEPTION 'category: expected 55 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM theme_context;
    IF n <> 96 THEN RAISE EXCEPTION 'theme_context: expected 96 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM time_context;
    IF n <> 22 THEN RAISE EXCEPTION 'time_context: expected 22 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM place_context;
    IF n <> 29 THEN RAISE EXCEPTION 'place_context: expected 29 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM atmosphere;
    IF n <> 25 THEN RAISE EXCEPTION 'atmosphere: expected 25 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM character_context;
    IF n <> 59 THEN RAISE EXCEPTION 'character_context: expected 59 tags, found %', n; END IF;
    SELECT count(*) INTO n FROM cinema_type;
    IF n <> 40 THEN RAISE EXCEPTION 'cinema_type: expected 40 tags, found %', n; END IF;

    -- 3. Every tag got an explicit sort_order from Part 4 (no leftover default).
    SELECT (SELECT count(*) FROM category           WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM theme_context      WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM time_context       WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM place_context      WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM atmosphere         WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM character_context  WHERE sort_order IS NULL OR sort_order = 999)
         + (SELECT count(*) FROM cinema_type        WHERE sort_order IS NULL OR sort_order = 999)
      INTO n;
    IF n <> 0 THEN RAISE EXCEPTION '% tag(s) left without an explicit sort_order', n; END IF;

    -- 4. Association reconciliation.
    pairs_after :=
        (SELECT count(*) FROM film_genre)
      + (SELECT count(*) FROM film_theme)
      + (SELECT count(*) FROM film_technique)
      + (SELECT count(*) FROM film_place)
      + (SELECT count(*) FROM film_period)
      + (SELECT count(*) FROM film_atmosphere)
      + (SELECT count(*) FROM film_character_context);

    pairs_expected := b.pairs_before - b.n_world_saving
                    - b.ov_mafia - b.ov_odyssey - b.ov_dreamlike - b.ov_political;

    RAISE NOTICE '--- AFTER --------------------------------------------------';
    RAISE NOTICE 'film<->tag pairs across 7 dimensions : % (expected %)',
                 pairs_after, pairs_expected;
    RAISE NOTICE 'tags: category=55 theme=96 time=22 place=29 atmosphere=25 character=59 cinema_type=40';

    IF pairs_after <> pairs_expected THEN
        RAISE EXCEPTION 'Association count mismatch: got %, expected %',
                        pairs_after, pairs_expected;
    END IF;

    RAISE NOTICE 'Migration 026 OK — all assertions passed.';
END $$;

COMMIT;
