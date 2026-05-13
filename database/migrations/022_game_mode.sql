-- Step 18: Game mode tables ("Tag It")

CREATE TABLE IF NOT EXISTS daily_challenge (
    challenge_date DATE PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    decoy1_film_id INTEGER REFERENCES film(film_id),
    decoy2_film_id INTEGER REFERENCES film(film_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_result (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    mode TEXT NOT NULL CHECK (mode IN ('daily', 'free')),
    challenge_date DATE,
    tags_used INTEGER NOT NULL,
    lives_remaining INTEGER NOT NULL CHECK (lives_remaining >= 0 AND lives_remaining <= 3),
    jokers_used INTEGER DEFAULT 0,
    stars INTEGER NOT NULL CHECK (stars >= 0 AND stars <= 5),
    tag_sequence JSONB,
    completed BOOLEAN DEFAULT TRUE,
    played_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_result_user ON game_result(user_id);
CREATE INDEX IF NOT EXISTS idx_game_result_daily ON game_result(challenge_date);
CREATE INDEX IF NOT EXISTS idx_game_result_user_mode ON game_result(user_id, mode);

-- Prevent duplicate daily submissions per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_result_user_daily_unique
    ON game_result(user_id, challenge_date) WHERE mode = 'daily';
