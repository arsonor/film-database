-- Migration 031: remove contradictory 'no particular' place rows (Step 24.2)
--
-- 'no particular' means "no other place tag applies" — it is a derived value
-- (see DERIVED_TAGS in backend/app/services/taxonomy_config.py) and cannot
-- coexist with a real place tag. The Step 24.1 audit found 91 of the 287 films
-- carrying it also hold another film_place row; the old pipeline wrote both.
-- Union apply would preserve every one, so they are cleaned up here.
--
-- Films with ZERO place tags are reported but NOT given 'no particular' here —
-- that insert is Martin's separate decision (the re-tag apply derivation will
-- also handle it film-by-film as films are re-tagged).
--
-- NOTE: PROMPTS.md calls this "migration 030", but 030_tag_weight.sql already
-- existed — the numbering shifted by one, same as Step 24's migration.
--
-- Local DB only; Supabase is synced manually by Martin.

BEGIN;

-- Before counts
SELECT
    (SELECT count(*) FROM film_place fp
     JOIN place_context pc USING (place_context_id)
     WHERE pc.environment = 'no particular')                       AS no_particular_rows_before,
    (SELECT count(*) FROM film_place fp
     JOIN place_context pc USING (place_context_id)
     WHERE pc.environment = 'no particular'
       AND EXISTS (SELECT 1 FROM film_place fp2
                   WHERE fp2.film_id = fp.film_id
                     AND fp2.place_context_id <> fp.place_context_id)) AS contradictory_rows,
    (SELECT count(*) FROM film f
     WHERE NOT EXISTS (SELECT 1 FROM film_place fp WHERE fp.film_id = f.film_id)) AS films_with_zero_place_tags;

-- Delete 'no particular' from any film that has another film_place row.
DELETE FROM film_place fp
USING place_context pc
WHERE pc.place_context_id = fp.place_context_id
  AND pc.environment = 'no particular'
  AND EXISTS (SELECT 1 FROM film_place fp2
              WHERE fp2.film_id = fp.film_id
                AND fp2.place_context_id <> fp.place_context_id);

-- After counts
SELECT
    (SELECT count(*) FROM film_place fp
     JOIN place_context pc USING (place_context_id)
     WHERE pc.environment = 'no particular')                       AS no_particular_rows_after,
    (SELECT count(*) FROM film_place fp
     JOIN place_context pc USING (place_context_id)
     WHERE pc.environment = 'no particular'
       AND EXISTS (SELECT 1 FROM film_place fp2
                   WHERE fp2.film_id = fp.film_id
                     AND fp2.place_context_id <> fp.place_context_id)) AS contradictory_rows_after;

COMMIT;
