-- User custom film lists
CREATE TABLE IF NOT EXISTS user_list (
    list_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    list_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, list_name)
);

CREATE INDEX IF NOT EXISTS idx_user_list_user ON user_list(user_id);

CREATE TABLE IF NOT EXISTS user_list_film (
    list_id INTEGER NOT NULL REFERENCES user_list(list_id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (list_id, film_id)
);

CREATE INDEX IF NOT EXISTS idx_user_list_film_list ON user_list_film(list_id);
CREATE INDEX IF NOT EXISTS idx_user_list_film_film ON user_list_film(film_id);
