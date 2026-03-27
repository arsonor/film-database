-- Migration 009: Add tmdb_collection_id to film table for franchise auto-linking
-- TMDB's belongs_to_collection field identifies films in the same franchise.
-- Storing this ID lets us auto-create film_sequel relationships when adding films.

ALTER TABLE film ADD COLUMN IF NOT EXISTS tmdb_collection_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_film_tmdb_collection_id ON film(tmdb_collection_id);
