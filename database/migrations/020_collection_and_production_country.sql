-- Migration 020: TMDB collection names + production countries (junction)
--
-- Prep work for Step 17a "Top 20 franchises" widget (uses tmdb_collection.name)
-- and Step 17b Geography tab (uses film_production_country to plot the world map).
--
-- Run once. Backfill scripts:
--   python scripts/backfill_tmdb_collections.py
--   python scripts/backfill_production_countries.py

-- =============================================================================
-- tmdb_collection — lookup of franchise names keyed by TMDB collection id
-- =============================================================================

CREATE TABLE IF NOT EXISTS tmdb_collection (
    collection_id INTEGER PRIMARY KEY,           -- matches film.tmdb_collection_id
    collection_name TEXT NOT NULL,
    poster_path TEXT,
    backdrop_path TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE tmdb_collection IS 'Franchise / collection metadata (e.g. James Bond Collection, Marvel Cinematic Universe). Keyed by TMDB collection id, joined from film.tmdb_collection_id.';

CREATE INDEX IF NOT EXISTS idx_tmdb_collection_name ON tmdb_collection(collection_name);

-- =============================================================================
-- production_country — ISO 3166-1 alpha-2 country lookup
-- =============================================================================

CREATE TABLE IF NOT EXISTS production_country (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL UNIQUE,     -- ISO 3166-1 alpha-2
    country_name TEXT NOT NULL                   -- English name from TMDB
);

COMMENT ON TABLE production_country IS 'Country lookup for production_countries. Lazy-populated from TMDB during ingestion / backfill.';

CREATE INDEX IF NOT EXISTS idx_production_country_name ON production_country(country_name);

-- =============================================================================
-- film_production_country — junction: which countries co-produced each film
-- =============================================================================

CREATE TABLE IF NOT EXISTS film_production_country (
    film_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, country_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (country_id) REFERENCES production_country(country_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_production_country IS 'Junction linking films to their production countries (from TMDB production_countries).';

CREATE INDEX IF NOT EXISTS idx_film_production_country_film ON film_production_country(film_id);
CREATE INDEX IF NOT EXISTS idx_film_production_country_country ON film_production_country(country_id);
