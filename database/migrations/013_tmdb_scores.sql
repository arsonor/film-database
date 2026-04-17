-- Add TMDB score columns and weighted rating to film table
ALTER TABLE film ADD COLUMN IF NOT EXISTS tmdb_score NUMERIC(3,1);
ALTER TABLE film ADD COLUMN IF NOT EXISTS tmdb_vote_count INTEGER;
ALTER TABLE film ADD COLUMN IF NOT EXISTS weighted_score NUMERIC(4,2);

COMMENT ON COLUMN film.tmdb_score IS 'TMDB vote average (0.0–10.0)';
COMMENT ON COLUMN film.tmdb_vote_count IS 'Number of TMDB user votes';
COMMENT ON COLUMN film.weighted_score IS 'Bayesian weighted rating accounting for vote count';
