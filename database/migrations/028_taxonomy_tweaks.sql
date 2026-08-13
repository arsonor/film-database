-- =============================================================================
-- Migration 028 — Taxonomy v2 tweaks
-- =============================================================================
--
-- 1. Genre: rename 'trial/judicial chronicle' → 'courtroom' (sort_order 500
--    unchanged; the 179 existing film associations are preserved by the rename).
--
-- 2. Place / Vehicles: add 'submarine' (404) and 'spaceship' (405) after
--    'ship' (403). Until now `ship` was defined as covering "all types of boat,
--    and spaceship" — these two get their own tags.
--
-- 3. Place / Buildings & institutions: delete 'naval' (207). Every film tagged
--    'naval' must end up tagged 'military' (206) — 5 of the 38 already are, the
--    other 33 gain it here. Deleting the lookup row cascades the 38 junction
--    rows away. 'castle' and 'hotel' shift down to 207/208 to keep the block
--    contiguous.
--
-- Net tag counts: category 55 (unchanged), place_context 29 → 30.
--
-- Idempotent-ish: re-running is a no-op for steps 1 and 2 (guarded / ON
-- CONFLICT). Step 3 is naturally a no-op once 'naval' is gone.
-- =============================================================================

BEGIN;

-- ── Pre-flight snapshot ─────────────────────────────────────────────────────
DO $$
DECLARE
    n_trial    INTEGER;
    n_naval    INTEGER;
    n_military INTEGER;
BEGIN
    SELECT count(*) INTO n_trial
      FROM film_genre fg JOIN category c ON c.category_id = fg.category_id
     WHERE c.category_name IN ('trial/judicial chronicle', 'courtroom');
    SELECT count(*) INTO n_naval
      FROM film_place fp JOIN place_context p ON p.place_context_id = fp.place_context_id
     WHERE p.environment = 'naval';
    SELECT count(*) INTO n_military
      FROM film_place fp JOIN place_context p ON p.place_context_id = fp.place_context_id
     WHERE p.environment = 'military';
    RAISE NOTICE 'BEFORE: courtroom/trial films=%, naval films=%, military films=%',
                 n_trial, n_naval, n_military;
END $$;


-- ── 1. Genre rename ─────────────────────────────────────────────────────────
-- Straight UPDATE of the lookup row: film_genre references category_id, so
-- every association follows automatically.
UPDATE category
   SET category_name = 'courtroom'
 WHERE category_name = 'trial/judicial chronicle'
   AND historic_subcategory_name IS NULL;

UPDATE tag_description
   SET tag_name = 'courtroom'
 WHERE dimension = 'categories'
   AND tag_name = 'trial/judicial chronicle';


-- ── 2. New Vehicles tags ────────────────────────────────────────────────────
INSERT INTO place_context (environment, sort_order) VALUES
    ('submarine', 404),
    ('spaceship', 405)
ON CONFLICT (environment) DO UPDATE SET sort_order = EXCLUDED.sort_order;


-- ── 3. naval → military, then drop naval ────────────────────────────────────
-- 3a. Give 'military' to every film that currently has 'naval'.
INSERT INTO film_place (film_id, place_context_id)
SELECT fp.film_id,
       (SELECT place_context_id FROM place_context WHERE environment = 'military')
  FROM film_place fp
  JOIN place_context p ON p.place_context_id = fp.place_context_id
 WHERE p.environment = 'naval'
ON CONFLICT DO NOTHING;

-- 3b. Assert no film would lose coverage before we delete anything.
DO $$
DECLARE
    n_uncovered INTEGER;
BEGIN
    SELECT count(*) INTO n_uncovered
      FROM film_place fp
      JOIN place_context p ON p.place_context_id = fp.place_context_id
     WHERE p.environment = 'naval'
       AND NOT EXISTS (
           SELECT 1 FROM film_place fp2
             JOIN place_context p2 ON p2.place_context_id = fp2.place_context_id
            WHERE fp2.film_id = fp.film_id AND p2.environment = 'military'
       );
    IF n_uncovered > 0 THEN
        RAISE EXCEPTION
            'Refusing to delete ''naval'': % film(s) tagged naval did not receive ''military''',
            n_uncovered;
    END IF;
END $$;

-- 3c. Drop the lookup row — FK cascade removes the film_place rows.
DELETE FROM place_context WHERE environment = 'naval';
DELETE FROM tag_description WHERE dimension = 'place_contexts' AND tag_name = 'naval';

-- 3d. Close the gap left in the Buildings & institutions block.
UPDATE place_context SET sort_order = 207 WHERE environment = 'castle';
UPDATE place_context SET sort_order = 208 WHERE environment = 'hotel';


-- ── Post-flight assertions ──────────────────────────────────────────────────
DO $$
DECLARE
    n_cat      INTEGER;
    n_place    INTEGER;
    n_trial    INTEGER;
    n_military INTEGER;
    bad        INTEGER;
BEGIN
    SELECT count(*) INTO n_cat   FROM category;
    SELECT count(*) INTO n_place FROM place_context;

    IF n_cat <> 55 THEN
        RAISE EXCEPTION 'category should hold 55 tags, found %', n_cat;
    END IF;
    IF n_place <> 30 THEN
        RAISE EXCEPTION 'place_context should hold 30 tags, found %', n_place;
    END IF;

    IF EXISTS (SELECT 1 FROM category WHERE category_name = 'trial/judicial chronicle') THEN
        RAISE EXCEPTION 'old genre name still present';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM category WHERE category_name = 'courtroom') THEN
        RAISE EXCEPTION 'courtroom missing';
    END IF;
    IF EXISTS (SELECT 1 FROM place_context WHERE environment = 'naval') THEN
        RAISE EXCEPTION 'naval still present';
    END IF;

    -- Vehicles block must read car/bus, train, airplane, ship, submarine, spaceship
    SELECT count(*) INTO bad FROM (
        SELECT environment, sort_order,
               row_number() OVER (ORDER BY sort_order) AS rn
          FROM place_context WHERE sort_order BETWEEN 400 AND 499
    ) v
    WHERE (v.rn, v.environment) NOT IN (
        (1,'car/bus'),(2,'train'),(3,'airplane'),(4,'ship'),(5,'submarine'),(6,'spaceship')
    );
    IF bad > 0 THEN
        RAISE EXCEPTION 'Vehicles block is not in the expected order';
    END IF;

    -- No duplicate sort_order inside place_context
    IF EXISTS (SELECT 1 FROM place_context GROUP BY sort_order HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'duplicate sort_order in place_context';
    END IF;

    SELECT count(*) INTO n_trial
      FROM film_genre fg JOIN category c ON c.category_id = fg.category_id
     WHERE c.category_name = 'courtroom';
    SELECT count(*) INTO n_military
      FROM film_place fp JOIN place_context p ON p.place_context_id = fp.place_context_id
     WHERE p.environment = 'military';
    RAISE NOTICE 'AFTER: courtroom films=%, military films=%, place_context tags=%',
                 n_trial, n_military, n_place;
END $$;

COMMIT;
