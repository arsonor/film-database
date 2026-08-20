-- Migration 030: Tag weighting foundation (Step 24)
--
-- Adds a `weight` column to the seven taxonomy junction tables.
-- Convention: 100 = defining, 50 = secondary, NULL = unscored legacy row.
-- NULL rows are NOT backfilled — everything written before the re-tag is
-- genuinely unscored, and a fake 50 would be indistinguishable from a real
-- secondary later. The CHECK range is wider than the two values in use so a
-- third level or true percentages need no further migration.
--
-- NOTE: PLAN.md refers to this as "migration 029", but 029_character_subdimensions.sql
-- already existed when this was written — the numbering shifted by one.

BEGIN;

-- film_genre ------------------------------------------------------------------
ALTER TABLE film_genre
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_genre.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_genre_defining ON film_genre (category_id) WHERE weight = 100;

-- film_theme ------------------------------------------------------------------
ALTER TABLE film_theme
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_theme.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_theme_defining ON film_theme (theme_context_id) WHERE weight = 100;

-- film_technique --------------------------------------------------------------
ALTER TABLE film_technique
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_technique.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_technique_defining ON film_technique (cinema_type_id) WHERE weight = 100;

-- film_character_context ------------------------------------------------------
ALTER TABLE film_character_context
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_character_context.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_character_context_defining ON film_character_context (character_context_id) WHERE weight = 100;

-- film_atmosphere -------------------------------------------------------------
ALTER TABLE film_atmosphere
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_atmosphere.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_atmosphere_defining ON film_atmosphere (atmosphere_id) WHERE weight = 100;

-- film_period -----------------------------------------------------------------
ALTER TABLE film_period
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_period.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_period_defining ON film_period (time_context_id) WHERE weight = 100;

-- film_place ------------------------------------------------------------------
ALTER TABLE film_place
    ADD COLUMN weight smallint CHECK (weight IS NULL OR weight BETWEEN 1 AND 100);
COMMENT ON COLUMN film_place.weight IS
    '100 = defining, 50 = secondary, NULL = unscored legacy row (pre-retag)';
CREATE INDEX idx_film_place_defining ON film_place (place_context_id) WHERE weight = 100;

COMMIT;
