-- Step 19: Chain It game + game hub restructure

-- 1. Add game_type to daily_challenge (for multiple games sharing the table)
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS game_type TEXT NOT NULL DEFAULT 'tag_it';
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS target_film_id INTEGER REFERENCES film(film_id);

-- Recreate PK to include game_type
ALTER TABLE daily_challenge DROP CONSTRAINT IF EXISTS daily_challenge_pkey;
ALTER TABLE daily_challenge ADD PRIMARY KEY (challenge_date, game_type);

-- 2. Add game_type + chain-specific fields to game_result
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS game_type TEXT NOT NULL DEFAULT 'tag_it';
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS chain_length INTEGER;
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS origin_film_id INTEGER REFERENCES film(film_id);
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS target_film_id INTEGER REFERENCES film(film_id);

-- Update unique daily index to include game_type
DROP INDEX IF EXISTS idx_game_result_user_daily_unique;
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_result_user_daily_unique
    ON game_result(user_id, challenge_date, game_type) WHERE mode = 'daily';

CREATE INDEX IF NOT EXISTS idx_game_result_game_type ON game_result(game_type);
