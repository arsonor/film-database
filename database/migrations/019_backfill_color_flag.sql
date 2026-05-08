-- Backfill film.color = FALSE for every film tagged with the
-- 'black and white' cinema_type. This corrects the bulk-import default of
-- color = TRUE for films that the Claude enrichment correctly identified as
-- B&W via taxonomy but didn't propagate to the canonical film.color column.
--
-- Run once. Safe to re-run (idempotent).

UPDATE film f
SET color = FALSE
WHERE f.color = TRUE
  AND EXISTS (
    SELECT 1
    FROM film_technique ft
    JOIN cinema_type ct ON ft.cinema_type_id = ct.cinema_type_id
    WHERE ft.film_id = f.film_id
      AND ct.technique_name = 'black and white'
  );
