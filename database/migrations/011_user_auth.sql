-- Step 15a: User authentication and per-user film status
-- Adds user_profile and user_film_status tables

-- 1. User profile table (id matches Supabase auth.users UUID)
CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    tier TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'pro', 'admin')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profile_email ON user_profile(email);
CREATE INDEX IF NOT EXISTS idx_user_profile_tier ON user_profile(tier);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS user_profile_updated_at_trigger ON user_profile;
CREATE TRIGGER user_profile_updated_at_trigger
    BEFORE UPDATE ON user_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 2. Per-user film status
CREATE TABLE IF NOT EXISTS user_film_status (
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id) ON DELETE CASCADE,
    seen BOOLEAN DEFAULT FALSE,
    favorite BOOLEAN DEFAULT FALSE,
    watchlist BOOLEAN DEFAULT FALSE,
    rating SMALLINT CHECK (rating IS NULL OR (rating >= 1 AND rating <= 10)),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, film_id)
);

CREATE INDEX IF NOT EXISTS idx_user_film_status_user ON user_film_status(user_id);
CREATE INDEX IF NOT EXISTS idx_user_film_status_film ON user_film_status(film_id);
CREATE INDEX IF NOT EXISTS idx_user_film_status_seen ON user_film_status(user_id, seen) WHERE seen = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_film_status_favorite ON user_film_status(user_id, favorite) WHERE favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_film_status_watchlist ON user_film_status(user_id, watchlist) WHERE watchlist = TRUE;

DROP TRIGGER IF EXISTS user_film_status_updated_at_trigger ON user_film_status;
CREATE TRIGGER user_film_status_updated_at_trigger
    BEFORE UPDATE ON user_film_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
