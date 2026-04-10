-- Film Database Schema
-- PostgreSQL DDL for a personal film database with rich taxonomy classification

-- Note: CREATE DATABASE must be run separately as superuser
-- CREATE DATABASE film_database;

-- Connect to the database and set search path
-- \c film_database
SET search_path TO public;

-- =============================================================================
-- TRIGGER FUNCTION FOR updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
SET search_path = public;

-- =============================================================================
-- CORE TABLE: FILM
-- =============================================================================

-- Central entity storing all film metadata
CREATE TABLE IF NOT EXISTS film (
    film_id SERIAL PRIMARY KEY,
    original_title TEXT NOT NULL,
    duration INTEGER,                          -- Duration in minutes
    color BOOLEAN DEFAULT TRUE,                -- Color film (false = black & white original)
    first_release_date DATE,
    summary TEXT,
    poster_url TEXT,
    backdrop_url TEXT,
    imdb_id VARCHAR(20) UNIQUE,
    tmdb_id INTEGER UNIQUE,
    budget BIGINT,                             -- Production budget in USD
    revenue BIGINT,                            -- Worldwide box office in USD
    tmdb_collection_id INTEGER,                -- TMDB collection ID for franchise auto-linking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE film IS 'Central table storing all film metadata, linked to classification dimensions via junction tables';
COMMENT ON COLUMN film.color IS 'True for color films, false for originally black & white films';
COMMENT ON COLUMN film.budget IS 'Production budget in USD';
COMMENT ON COLUMN film.revenue IS 'Worldwide box office revenue in USD';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS film_updated_at_trigger ON film;
CREATE TRIGGER film_updated_at_trigger
    BEFORE UPDATE ON film
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Indexes for film table
CREATE INDEX IF NOT EXISTS idx_film_tmdb_id ON film(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_film_imdb_id ON film(imdb_id);
CREATE INDEX IF NOT EXISTS idx_film_original_title ON film(original_title);
CREATE INDEX IF NOT EXISTS idx_film_tmdb_collection_id ON film(tmdb_collection_id);
CREATE INDEX IF NOT EXISTS idx_film_first_release_date ON film(first_release_date);

-- =============================================================================
-- PEOPLE & ROLES
-- =============================================================================

-- Person table storing cast and crew members
CREATE TABLE IF NOT EXISTS person (
    person_id SERIAL PRIMARY KEY,
    firstname TEXT,
    lastname TEXT NOT NULL,
    gender VARCHAR(1),                         -- M, F, or NULL
    date_of_birth DATE,
    date_of_death DATE,
    nationality TEXT,
    tmdb_id INTEGER UNIQUE,
    photo_url TEXT
);

COMMENT ON TABLE person IS 'Stores all people involved in films (actors, directors, crew)';
COMMENT ON COLUMN person.gender IS 'Single character: M (male), F (female), or NULL (unknown/other)';

CREATE INDEX IF NOT EXISTS idx_person_tmdb_id ON person(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_person_lastname ON person(lastname);

-- Job roles for crew members
CREATE TABLE IF NOT EXISTS person_job (
    job_id SERIAL PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

COMMENT ON TABLE person_job IS 'Lookup table for crew job roles (Director, Writer, Cinematographer, etc.)';

-- Crew junction table (film <-> person <-> job)
CREATE TABLE IF NOT EXISTS crew (
    film_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, person_id, job_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES person_job(job_id) ON DELETE CASCADE
);

COMMENT ON TABLE crew IS 'Junction table linking films to crew members and their roles';

CREATE INDEX IF NOT EXISTS idx_crew_film_id ON crew(film_id);
CREATE INDEX IF NOT EXISTS idx_crew_person_id ON crew(person_id);
CREATE INDEX IF NOT EXISTS idx_crew_job_id ON crew(job_id);

-- Casting table for actors and their characters
CREATE TABLE IF NOT EXISTS casting (
    cast_id SERIAL PRIMARY KEY,
    film_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    character_name TEXT,
    cast_order INTEGER,                        -- Billing order (1 = lead)
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES person(person_id) ON DELETE CASCADE
);

COMMENT ON TABLE casting IS 'Stores actor appearances in films with character names and billing order';
COMMENT ON COLUMN casting.cast_order IS 'Billing order: 1 = lead actor, higher numbers = supporting roles';

CREATE INDEX IF NOT EXISTS idx_casting_film_id ON casting(film_id);
CREATE INDEX IF NOT EXISTS idx_casting_person_id ON casting(person_id);

-- =============================================================================
-- PRODUCTION
-- =============================================================================

-- Studios/production companies
CREATE TABLE IF NOT EXISTS studio (
    studio_id SERIAL PRIMARY KEY,
    studio_name TEXT NOT NULL,
    country_name TEXT
);

COMMENT ON TABLE studio IS 'Production companies and studios';

-- Film-Studio junction table
CREATE TABLE IF NOT EXISTS production (
    film_id INTEGER NOT NULL,
    studio_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, studio_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (studio_id) REFERENCES studio(studio_id) ON DELETE CASCADE
);

COMMENT ON TABLE production IS 'Junction table linking films to their production studios';

CREATE INDEX IF NOT EXISTS idx_production_film_id ON production(film_id);
CREATE INDEX IF NOT EXISTS idx_production_studio_id ON production(studio_id);

-- =============================================================================
-- LANGUAGE & TITLES
-- =============================================================================

-- Languages lookup table
CREATE TABLE IF NOT EXISTS language (
    language_id SERIAL PRIMARY KEY,
    language_code VARCHAR(10) NOT NULL UNIQUE,
    language_name TEXT NOT NULL
);

COMMENT ON TABLE language IS 'Lookup table for languages (ISO codes and names)';

-- Film titles in various languages
CREATE TABLE IF NOT EXISTS film_language (
    film_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    film_title TEXT NOT NULL,
    is_original BOOLEAN DEFAULT FALSE,         -- Is this the original language?
    has_dubbing BOOLEAN DEFAULT FALSE,         -- Is dubbing available in this language?
    PRIMARY KEY (film_id, language_id, film_title),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES language(language_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_language IS 'Film titles in different languages, tracking original language and dubbing availability';
COMMENT ON COLUMN film_language.is_original IS 'True if this is the original language of the film';
COMMENT ON COLUMN film_language.has_dubbing IS 'True if dubbing is available in this language';

CREATE INDEX IF NOT EXISTS idx_film_language_film_id ON film_language(film_id);
CREATE INDEX IF NOT EXISTS idx_film_language_language_id ON film_language(language_id);

-- =============================================================================
-- CLASSIFICATION: CATEGORY / GENRE
-- =============================================================================

-- Film categories/genres
CREATE TABLE IF NOT EXISTS category (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL,
    historic_subcategory_name TEXT,            -- For Historical subcategories (biopic, western, etc.)
    sort_order INTEGER DEFAULT 999,
    UNIQUE (category_name, historic_subcategory_name)
);

COMMENT ON TABLE category IS 'Film genres/categories (Action, Drama, etc.) with optional historical subcategories';
COMMENT ON COLUMN category.historic_subcategory_name IS 'Subcategory for Historical films: biopic, western, peplum, etc.';

-- Film-Category junction table
CREATE TABLE IF NOT EXISTS film_genre (
    film_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, category_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_genre IS 'Junction table linking films to their genres/categories';

CREATE INDEX IF NOT EXISTS idx_film_genre_film_id ON film_genre(film_id);
CREATE INDEX IF NOT EXISTS idx_film_genre_category_id ON film_genre(category_id);

-- =============================================================================
-- CLASSIFICATION: CINEMA TYPE / CINEMATOGRAPHY
-- =============================================================================

-- Cinema types/techniques (merged with cultural movements)
CREATE TABLE IF NOT EXISTS cinema_type (
    cinema_type_id SERIAL PRIMARY KEY,
    technique_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE cinema_type IS 'Cinema types, techniques, and cultural movements (animation, art house, noir, new wave, etc.)';

-- Film-CinemaType junction table
CREATE TABLE IF NOT EXISTS film_technique (
    film_id INTEGER NOT NULL,
    cinema_type_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, cinema_type_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (cinema_type_id) REFERENCES cinema_type(cinema_type_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_technique IS 'Junction table linking films to their cinematographic techniques';

CREATE INDEX IF NOT EXISTS idx_film_technique_film_id ON film_technique(film_id);
CREATE INDEX IF NOT EXISTS idx_film_technique_cinema_type_id ON film_technique(cinema_type_id);

-- =============================================================================
-- CLASSIFICATION: GEOGRAPHY & PLACE
-- =============================================================================

-- Geographic locations (hierarchical: continent > country > state/city)
CREATE TABLE IF NOT EXISTS geography (
    geography_id SERIAL PRIMARY KEY,
    continent TEXT,
    country TEXT,
    state_city TEXT,
    UNIQUE (continent, country, state_city)
);

COMMENT ON TABLE geography IS 'Geographic locations with hierarchical structure (continent/country/state-city)';

-- Film-Geography junction with place type
CREATE TABLE IF NOT EXISTS film_set_place (
    film_id INTEGER NOT NULL,
    geography_id INTEGER NOT NULL,
    place_type VARCHAR(20) NOT NULL CHECK (place_type IN ('diegetic', 'shooting', 'fictional')),
    PRIMARY KEY (film_id, geography_id, place_type),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (geography_id) REFERENCES geography(geography_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_set_place IS 'Links films to geographic locations with context (diegetic=narrative, shooting=filming, fictional=imaginary)';
COMMENT ON COLUMN film_set_place.place_type IS 'diegetic=in-film narrative location, shooting=real filming location, fictional=invented location';

CREATE INDEX IF NOT EXISTS idx_film_set_place_film_id ON film_set_place(film_id);
CREATE INDEX IF NOT EXISTS idx_film_set_place_geography_id ON film_set_place(geography_id);

-- Place environment/context
CREATE TABLE IF NOT EXISTS place_context (
    place_context_id SERIAL PRIMARY KEY,
    environment TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE place_context IS 'Types of environments/settings (urban, rural, space, etc.)';

-- Film-PlaceContext junction table
CREATE TABLE IF NOT EXISTS film_place (
    film_id INTEGER NOT NULL,
    place_context_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, place_context_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (place_context_id) REFERENCES place_context(place_context_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_place IS 'Junction table linking films to their environmental settings';

CREATE INDEX IF NOT EXISTS idx_film_place_film_id ON film_place(film_id);
CREATE INDEX IF NOT EXISTS idx_film_place_place_context_id ON film_place(place_context_id);

-- =============================================================================
-- CLASSIFICATION: TIME CONTEXT
-- =============================================================================

-- Time periods
CREATE TABLE IF NOT EXISTS time_context (
    time_context_id SERIAL PRIMARY KEY,
    time_period TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE time_context IS 'Historical periods and seasons (contemporary, medieval, WW2, summer, etc.)';

-- Film-TimeContext junction table
CREATE TABLE IF NOT EXISTS film_period (
    film_id INTEGER NOT NULL,
    time_context_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, time_context_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (time_context_id) REFERENCES time_context(time_context_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_period IS 'Junction table linking films to their time periods';

CREATE INDEX IF NOT EXISTS idx_film_period_film_id ON film_period(film_id);
CREATE INDEX IF NOT EXISTS idx_film_period_time_context_id ON film_period(time_context_id);

-- =============================================================================
-- CLASSIFICATION: THEMES
-- =============================================================================

-- Thematic elements
CREATE TABLE IF NOT EXISTS theme_context (
    theme_context_id SERIAL PRIMARY KEY,
    theme_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE theme_context IS 'Thematic elements and subject matter (war, crime, politics, etc.)';

-- Film-Theme junction table
CREATE TABLE IF NOT EXISTS film_theme (
    film_id INTEGER NOT NULL,
    theme_context_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, theme_context_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (theme_context_id) REFERENCES theme_context(theme_context_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_theme IS 'Junction table linking films to their thematic elements';

CREATE INDEX IF NOT EXISTS idx_film_theme_film_id ON film_theme(film_id);
CREATE INDEX IF NOT EXISTS idx_film_theme_theme_context_id ON film_theme(theme_context_id);

-- =============================================================================
-- CLASSIFICATION: CHARACTERS (merged character types + contexts + archetypes)
-- =============================================================================

-- Character types, contexts, and archetypes (merged from characters_type + character_context)
CREATE TABLE IF NOT EXISTS character_context (
    character_context_id SERIAL PRIMARY KEY,
    context_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE character_context IS 'Character types, contexts, and archetypes (solitary, childhood, detective, vampire, etc.)';

-- Film-CharacterContext junction table
CREATE TABLE IF NOT EXISTS film_character_context (
    film_id INTEGER NOT NULL,
    character_context_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, character_context_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (character_context_id) REFERENCES character_context(character_context_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_character_context IS 'Junction table linking films to character contexts and archetypes';

CREATE INDEX IF NOT EXISTS idx_film_character_context_film_id ON film_character_context(film_id);
CREATE INDEX IF NOT EXISTS idx_film_character_context_context_id ON film_character_context(character_context_id);

-- =============================================================================
-- CLASSIFICATION: ATMOSPHERE
-- =============================================================================

-- Film atmosphere/tone
CREATE TABLE IF NOT EXISTS atmosphere (
    atmosphere_id SERIAL PRIMARY KEY,
    atmosphere_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE atmosphere IS 'Film atmosphere and tone (feel good, violent, mysterious, etc.)';

-- Film-Atmosphere junction table
CREATE TABLE IF NOT EXISTS film_atmosphere (
    film_id INTEGER NOT NULL,
    atmosphere_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, atmosphere_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (atmosphere_id) REFERENCES atmosphere(atmosphere_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_atmosphere IS 'Junction table linking films to their atmospheric qualities';

CREATE INDEX IF NOT EXISTS idx_film_atmosphere_film_id ON film_atmosphere(film_id);
CREATE INDEX IF NOT EXISTS idx_film_atmosphere_atmosphere_id ON film_atmosphere(atmosphere_id);

-- =============================================================================
-- CLASSIFICATION: MOTIVATIONS & RELATIONS
-- =============================================================================

-- Character motivations and relationships
CREATE TABLE IF NOT EXISTS motivation_relation (
    motivation_id SERIAL PRIMARY KEY,
    motivation_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE motivation_relation IS 'Character motivations and interpersonal dynamics (vengeance, friendship, jealousy, etc.)';

-- Film-Motivation junction table
CREATE TABLE IF NOT EXISTS film_motivation (
    film_id INTEGER NOT NULL,
    motivation_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, motivation_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (motivation_id) REFERENCES motivation_relation(motivation_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_motivation IS 'Junction table linking films to character motivations';

CREATE INDEX IF NOT EXISTS idx_film_motivation_film_id ON film_motivation(film_id);
CREATE INDEX IF NOT EXISTS idx_film_motivation_motivation_id ON film_motivation(motivation_id);

-- =============================================================================
-- CLASSIFICATION: MESSAGE CONVEYED
-- =============================================================================

-- Film's message or narrative approach
CREATE TABLE IF NOT EXISTS message_conveyed (
    message_id SERIAL PRIMARY KEY,
    message_name TEXT NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 999
);

COMMENT ON TABLE message_conveyed IS 'The message or narrative tone of the film (satirical, philosophical, nostalgic, etc.)';

-- Film-Message junction table
CREATE TABLE IF NOT EXISTS film_message (
    film_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, message_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES message_conveyed(message_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_message IS 'Junction table linking films to their conveyed messages';

CREATE INDEX IF NOT EXISTS idx_film_message_film_id ON film_message(film_id);
CREATE INDEX IF NOT EXISTS idx_film_message_message_id ON film_message(message_id);

-- =============================================================================
-- FILM RELATIONSHIPS (Sequels, Prequels, Remakes)
-- =============================================================================

-- Relationships between films
CREATE TABLE IF NOT EXISTS film_sequel (
    film_id INTEGER NOT NULL,
    related_film_id INTEGER NOT NULL,
    relation_type VARCHAR(20) NOT NULL CHECK (relation_type IN ('sequel', 'prequel', 'remake', 'spinoff', 'reboot')),
    PRIMARY KEY (film_id, related_film_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (related_film_id) REFERENCES film(film_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_sequel IS 'Relationships between films (sequel, prequel, remake, spinoff, reboot)';
COMMENT ON COLUMN film_sequel.relation_type IS 'Type of relationship: sequel, prequel, remake, spinoff, or reboot';

CREATE INDEX IF NOT EXISTS idx_film_sequel_film_id ON film_sequel(film_id);
CREATE INDEX IF NOT EXISTS idx_film_sequel_related_film_id ON film_sequel(related_film_id);

-- =============================================================================
-- SOURCE / ORIGIN
-- =============================================================================

-- Source material for films
CREATE TABLE IF NOT EXISTS source (
    source_id SERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,                 -- original screenplay, novel, comic, etc.
    source_title TEXT,
    author TEXT
);

COMMENT ON TABLE source IS 'Source material for films (novel, comic, play, true story, etc.)';
COMMENT ON COLUMN source.source_type IS 'Type: original screenplay, novel, comic, TV series, true story, play, video game, poem, short story';

-- Film-Source junction table
CREATE TABLE IF NOT EXISTS film_origin (
    film_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, source_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES source(source_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_origin IS 'Junction table linking films to their source material';

CREATE INDEX IF NOT EXISTS idx_film_origin_film_id ON film_origin(film_id);
CREATE INDEX IF NOT EXISTS idx_film_origin_source_id ON film_origin(source_id);

-- =============================================================================
-- EXPLOITATION / STREAMING
-- =============================================================================

-- Streaming platforms
CREATE TABLE IF NOT EXISTS stream_platform (
    platform_id SERIAL PRIMARY KEY,
    platform_name TEXT NOT NULL UNIQUE
);

COMMENT ON TABLE stream_platform IS 'Streaming and distribution platforms';

-- Film-Platform junction table
CREATE TABLE IF NOT EXISTS film_exploitation (
    film_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, platform_id),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES stream_platform(platform_id) ON DELETE CASCADE
);

COMMENT ON TABLE film_exploitation IS 'Junction table tracking where films are available for streaming';

CREATE INDEX IF NOT EXISTS idx_film_exploitation_film_id ON film_exploitation(film_id);
CREATE INDEX IF NOT EXISTS idx_film_exploitation_platform_id ON film_exploitation(platform_id);

-- =============================================================================
-- AWARDS
-- =============================================================================

-- Film awards and nominations
CREATE TABLE IF NOT EXISTS award (
    award_id SERIAL PRIMARY KEY,
    film_id INTEGER NOT NULL,
    festival_name TEXT NOT NULL,
    category TEXT,
    award_year INTEGER,
    result VARCHAR(20) CHECK (result IN ('won', 'nominated')),
    FOREIGN KEY (film_id) REFERENCES film(film_id) ON DELETE CASCADE
);

COMMENT ON TABLE award IS 'Film awards and nominations from festivals and ceremonies';
COMMENT ON COLUMN award.result IS 'Whether the film won or was only nominated';

CREATE INDEX IF NOT EXISTS idx_award_film_id ON award(film_id);
CREATE INDEX IF NOT EXISTS idx_award_festival_name ON award(festival_name);
CREATE INDEX IF NOT EXISTS idx_award_year ON award(award_year);

-- =============================================================================
-- USER AUTH & FILM STATUS
-- =============================================================================

-- User profile (id matches Supabase auth.users UUID)
CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    tier TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'pro', 'admin')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE user_profile IS 'User profiles synced from Supabase Auth';
COMMENT ON COLUMN user_profile.tier IS 'User tier: free, pro, or admin';

CREATE INDEX IF NOT EXISTS idx_user_profile_email ON user_profile(email);
CREATE INDEX IF NOT EXISTS idx_user_profile_tier ON user_profile(tier);

DROP TRIGGER IF EXISTS user_profile_updated_at_trigger ON user_profile;
CREATE TRIGGER user_profile_updated_at_trigger
    BEFORE UPDATE ON user_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Per-user film status (seen, favorite, watchlist, rating)
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

COMMENT ON TABLE user_film_status IS 'Per-user film status tracking (seen, favorites, watchlist, ratings)';

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

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
