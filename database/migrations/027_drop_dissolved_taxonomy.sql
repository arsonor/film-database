-- =============================================================================
-- Migration 027 — Taxonomy v2, step 22: drop the dissolved dimensions
-- =============================================================================
--
-- Migration 026 dissolved `motivation_relation` and `message_conveyed` into
-- Genre / Theme / Atmosphere, migrating every film↔tag association, and left
-- the four tables in place (empty) so the recommender, the stats dashboard and
-- the three game modes kept running unchanged.
--
-- Step 22 rewired all of those surfaces onto the 7 live dimensions, so the
-- tables are now unreferenced by any code path and can go.
--
-- Safety: the DO block below aborts the transaction if any of the four tables
-- still holds rows — that would mean 026 was not applied (or was partially
-- rolled back) and dropping would destroy real associations.
-- =============================================================================

BEGIN;

DO $$
DECLARE
    n_motivations INTEGER := 0;
    n_messages    INTEGER := 0;
    n_film_mot    INTEGER := 0;
    n_film_msg    INTEGER := 0;
BEGIN
    IF to_regclass('public.motivation_relation') IS NOT NULL THEN
        EXECUTE 'SELECT COUNT(*) FROM motivation_relation' INTO n_motivations;
    END IF;
    IF to_regclass('public.message_conveyed') IS NOT NULL THEN
        EXECUTE 'SELECT COUNT(*) FROM message_conveyed' INTO n_messages;
    END IF;
    IF to_regclass('public.film_motivation') IS NOT NULL THEN
        EXECUTE 'SELECT COUNT(*) FROM film_motivation' INTO n_film_mot;
    END IF;
    IF to_regclass('public.film_message') IS NOT NULL THEN
        EXECUTE 'SELECT COUNT(*) FROM film_message' INTO n_film_msg;
    END IF;

    IF n_motivations + n_messages + n_film_mot + n_film_msg > 0 THEN
        RAISE EXCEPTION
            'Refusing to drop: dissolved taxonomy tables are not empty '
            '(motivation_relation=%, message_conveyed=%, film_motivation=%, film_message=%). '
            'Run migration 026_taxonomy_v2.sql first.',
            n_motivations, n_messages, n_film_mot, n_film_msg;
    END IF;

    RAISE NOTICE 'All four dissolved taxonomy tables are empty — dropping.';
END $$;

-- Junctions first, then the lookups (CASCADE would do it, but be explicit).
DROP TABLE IF EXISTS film_motivation;
DROP TABLE IF EXISTS film_message;
DROP TABLE IF EXISTS motivation_relation;
DROP TABLE IF EXISTS message_conveyed;

-- tag_description rows for the dissolved dimensions were re-pointed or deleted
-- by 026; sweep any that were re-created since.
DELETE FROM tag_description WHERE dimension IN ('motivations', 'messages');

DO $$
BEGIN
    IF to_regclass('public.motivation_relation') IS NOT NULL
       OR to_regclass('public.message_conveyed') IS NOT NULL
       OR to_regclass('public.film_motivation') IS NOT NULL
       OR to_regclass('public.film_message') IS NOT NULL THEN
        RAISE EXCEPTION 'Drop did not take effect';
    END IF;
    RAISE NOTICE 'Migration 027 complete: 7 taxonomy dimensions remain.';
END $$;

COMMIT;
