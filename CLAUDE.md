# Film Database — Project Context for Claude Code

## Project Overview

A personal film database application with a rich filtering interface, recommendation engine, and agentic capabilities for adding/enriching films. The database contains ~2500+ films spanning from 1902 to 2026.

## Source Documents

Three reference documents define this project (located in the associated Claude.ai project):

1. **Films_list.docx** — Chronological filmography (~2500+ titles) organized by year, grouped by region (Francophone, Anglo-Saxon, Asian, Other). Includes franchise entries and animation. Titles are mostly in French.
2. **Film_attributes.docx** — the original (v1) taxonomy of classification attributes. **Superseded** by `Taxonomy dimensions & tags.txt` (at the project root), which defines the current 7-dimension Taxonomy v2 — see the Classification Dimensions section below.
3. **Film_database.pdf** — Entity-Relationship diagram showing the relational schema.

## Tech Stack

- **Database:** PostgreSQL
- **Backend:** Python (FastAPI)
- **Frontend:** React + Tailwind CSS + shadcn/ui
- **Primary Data API:** TMDB (The Movie Database) — posters, cast/crew, genres, keywords, runtime, release dates, production companies, languages, overview. Supports French titles via locale parameter.
- **Complementary Sources:** Wikidata/Wikipedia (awards, cultural movements), OMDb (IMDb cross-reference)
- **Recommendation Engine:** Tag-based similarity scoring + Claude API for external suggestions
- **AI Enrichment:** Claude API for classifying films into the full taxonomy

## Database Design Principles

### Core Entity: FILM
Central table linked to all classification dimensions via junction tables (many-to-many relationships).

**Film attributes:**
- film_id, original_title, duration, color (boolean), first_release_date, summary, vu (boolean = seen by user), poster_url, backdrop_url, imdb_id, tmdb_id
- **budget** (production budget in USD)
- **revenue** (worldwide box office in USD)

### People & Roles
- `person` — id, firstname, lastname, gender, date_of_birth, date_of_death, nationality, tmdb_id, photo_url
- `person_job` — id, role_name (Director, Writer, Cinematographer, Composer, Producer, Editor, etc.)
- `crew` — film_id, person_id, job_id
- `casting` — id, film_id, person_id, character_name, cast_order (detailed: include secondary characters)

### Production
- `studio` — id, name, country
- `production` — film_id, studio_id

### Titles & Languages
- `language` — id, code, name
- `film_language` — film_id, language_id, film_title, is_original (boolean), has_dubbing (boolean)

### Classification Dimensions (Taxonomy v2 — all many-to-many)

**7 dimensions**, in display order: **Genre · Theme · Time Period · Place · Atmosphere · Character · Cinema Type**.

Each dimension is split into named **sub-dimensions** encoded as `sort_order` blocks of 100 (block = `sort_order / 100`). The database stores the ordering; the labels live in `frontend/src/lib/taxonomyGroups.ts` and `backend/app/services/taxonomy_config.py`. Blocks are listed below in their exact display order — **that order is meaningful and must be preserved**.

> Source of truth for names and ordering: `database/seed_taxonomy.sql`. Tag definitions: `database/tags_definition.md`. Never invent a tag name from this file — grep the seed.

#### Genre — `category` (55 tags)
The 12 **main genres** occupy block 1 (`sort_order < 200`); everything above is a **sub-genre**. Film cards and the detail-page hero show main genres only; the Genre taxonomy section shows everything. Every film must carry at least one main genre.

- **Main** — Drama, Comedy, Romance, Historical, Action, Adventure, Thriller, Science-Fiction, Fantasy, Horror, Musical, Documentary
- **Drama / Romance** — melodrama, coming of age, slice of life, tragedy
- **Comedy** — parodic, satirical, absurdist, black comedy
- **Thriller / Adventure** — psychological, war, crime, investigation, spy, heist, mafia/organized crime, serial killer, survival, chase/escape, odyssey/quest, disaster, apocalypse
- **Historical / Justice** — courtroom, prison, biopic, fait divers/true incident, western, peplum, swashbuckler, costume drama, wu xia pian, revisionist/alternate history
- **Sci-fi / Fantasy** — supernatural, whimsical/zany, dystopia, tales and legends
- **Horror** — jumpscare, slasher, gore, body horror, gothic horror, folk horror
- **Miscellaneous** — docufiction, martial arts

*Legacy note:* `category.historic_subcategory_name` still exists but is inert — all Genre rows are flat, with the column NULL. A partial unique index `uq_category_name_no_subcategory` enforces uniqueness on the name alone.

#### Theme — `theme_context` (96 tags)
- **Society & World** — social, societal, generational, political, religion, business, journalism/media, censorship, conspiracy, sect, immigration, colonialism, slavery, nature/wildlife, AI/technology
- **Values & Reflection** — humanist, feminist, nostalgic, ecological, patriotic, anti establishment, traditionalist/way of life, philosophical, metaphysical
- **Bonds & attachments** *(Human Relations)* — love, friendship, solidarity, communication, family/parenthood
- **Desire & transgression** *(Human Relations)* — power, manipulation, sex, adultery, jealousy, perversion
- **Interpersonal conflict** *(Human Relations)* — class/culture clash, rivalry, fight, rebellion/revolt, vengeance, harassment
- **Crime & abuse of power** *(Human Relations)* — delinquency, police violence, sex crime, kidnapping/hostage, trafficking/fraud, corruption, terrorism
- **Wounds & burdens** *(Personal / Inner conflict)* — trauma/accident, identity crisis, illness, amnesia, death, grief/mourning, addiction/drugs, loneliness, guilt
- **Drives & arcs** *(Personal / Inner conflict)* — obsession, greed/ambition, doubt/dilemma, lie, sacrifice, honor/duty, emancipation, redemption, transformation, time passing, dream
- **Art** *(Art, Sport & Entertainment)* — art, art: music/dance, art: cinema, art: literature, art: fashion, art: painting, art: sculpture, art: theatre, art: radio, art: architecture
- **Sport** *(Art, Sport & Entertainment)* — sport, sport: individual, sport: collective, sport: tournament, sport: motor
- **Entertainment** *(Art, Sport & Entertainment)* — food/cooking, party, game, gambling, contest
- **Face to the unknown** — sorcery, alien contact, paranormal, curse, time travel/loop, virtual/parallel universe, invasion, exploration

The `art: X` / `sport: X` tags are children of the bare `art` / `sport` parents; dashboards that count "top themes" filter out names matching `'%: %'` so the parents aren't double-counted.

#### Time Period — `time_context` (22 tags)
Chronological tags use `sort_order` 1–15 (block 0), so the whole dimension fits blocks 0/1/2.

- **Chronological** — future, contemporary, 2000-2010's, 1980-90's, 1950-60-70's, WW2, 1920-30's, WW1, 1900-1910's, 19th, modern age, medieval, antiquity, prehistoric, undetermined
- **Time span** — single day, several years, decades-spanning
- **Seasons** — spring, summer, autumn, winter

Year ranges (enforced in the enrichment prompt via `TIME_PERIOD_YEAR_RANGES`): future 2030+ · contemporary 2020–2029 · 2000-2010's 2000–2019 · 1980-90's 1980–1999 · 1950-60-70's 1946–1979 · WW2 1939–1945 · 1920-30's 1919–1938 · WW1 1914–1918 · 1900-1910's 1900–1913 · 19th 1800–1899 · modern age 1500–1799 · medieval 500–1500 · antiquity 3000 BC–500 AD · prehistoric before recorded civilization · undetermined no identifiable period.

#### Place — `place_context` (30 tags)
- **Environments** — urban, small town, rural, forest, mountains, desert, beach, maritime, island, underground, space, planet
- **Buildings & institutions** — building, household/house/apartment, company/factory, school/university, hospital, jail, military, castle, hotel
- **Narrative settings** — road movie, huis clos/confined setting
- **Vehicles** — car/bus, train, airplane, ship, submarine, spaceship
- *(unlabelled block 5)* — no particular

#### Geography (separate from Place)
**Geography** — continent, country, state/city
**film_set_place** — film_id, geography_id, **place_type**: one of:
  - `diegetic` = location as depicted in the film's narrative
  - `shooting` = real physical shooting location
  - `fictional` = invented/fantasy location

A separate `production_country` / `film_production_country` pair records the *producing* countries (ISO codes from TMDB) — do not confuse it with diegetic or shooting geography.

#### Atmosphere — `atmosphere` (25 tags)
- **Light / Joyful** — family-friendly, feel good, crazy/nutty, delicate/intimate
- **Dark / Extreme** — depressive/sad, violent, disturbing, steamy, sordid
- **Pace, Tension & Scale** — epic, edge of your seat, mysterious, oppressive, claustrophobic, contemplative/meditative
- **Artistic Directing** — cityscape, pastoral, gritty/realistic, meticulous, hypnotic/immersive, psychedelic, ethereal, symbolic, dreamlike/surreal, poetic

#### Character — `character_context` (59 tags)
- **Group structure** — solitary, tandem, trio, couple, relatives, generations, buddies, team/group/gang, ensemble cast
- **Age & identity** — childhood, teenager, elderly, adult/child, female lead, male ensemble, LGBT, interracial
- **Social status & traits** — ordinary, poor/marginal, wealthy, genius, simpleton/fool, loser, star/celebrity, disturbed/madness, disabled, outcast/misfit, sex worker, psychopath
- **Narrative devices** — double, cross-dressing, unreliable narrator
- **Archetypes — human** — super hero, chosen one, antihero, scientist/researcher, mentor, cop, detective, secret agent, vigilante, gangster, soldier, warrior, knight, samurai, pirate, viking, witch/wizard, femme fatale
- **Non-human & creatures** — animal, monster/terrestrial creature, devil, ghost/spirit, vampire, zombie, alien, android/robot, vehicle

#### Cinema Type — `cinema_type` (40 tags)
Cultural movements are no longer a separate dimension — they live in the *Movements & eras* block below.

- **Visual techniques** — animation, mixed animation, CGI, 3D, motion capture, black and white, aesthetics, found footage, dogma
- **Industry & culture** — blockbuster, art house, B, franchise, popular culture
- **Sequencing** *(Narrative techniques)* — chapters/multi-sequence, flashback/non linear, real time, timelapse, slow-motion, sequence-shot, split screen, musical montage
- **Voice & Dialogue** *(Narrative techniques)* — dialogs/punchline, slang dialogs, few/no dialogs, voiceover, monologue, fourth wall break
- **Movements & eras** — silent, expressionism, realism, neo-realism, noir, hollywood golden age, new hollywood, new wave, slow cinema, neo-noir, blaxploitation, giallo

#### Dissolved dimensions (historical)
`motivation_relation` and `message_conveyed` were the 8th and 9th dimensions until Taxonomy v2. Migration `026_taxonomy_v2.sql` migrated every association into Genre / Theme / Atmosphere and migration `027_drop_dissolved_taxonomy.sql` dropped the tables. **Do not reintroduce them.** Where the old tags went:
- motivations → mostly **Theme** (love, power, manipulation, vengeance, obsession, sacrifice…); `odyssey` + `quest` merged into the **Genre** `odyssey/quest`; `world-saving` deleted.
- messages → **Theme** (humanist, feminist, nostalgic, ecological, patriotic, anti establishment, traditionalist/way of life, philosophical, metaphysical, political), **Genre** (parodic, satirical, absurdist, revisionist/alternate history) and **Atmosphere** (symbolic, poetic, `dreamlike` + `surreal` merged into `dreamlike/surreal`).

### Film Relationships
- `film_sequel` — film_id, related_film_id, relation_type: sequel, prequel, remake, spinoff, reboot

### Source / Origin
- `source` — id, type (original screenplay, novel, comic, TV series, true story, play, video game, poem, short story, remake), source_title, author

### Exploitation
- `stream_platform` — id, platform_name
- `film_exploitation` — film_id, platform_id

### Awards
- `award` — film_id, festival/ceremony name, category, year, result (won/nominated)

## Important Design Notes

1. **Place Context Duality:** Always differentiate between diegetic (in-film narrative location) and shooting (real filming location). A film set in "Los Angeles" may have been shot in Vancouver.
2. **Cast Detail Level:** Include secondary characters, not just leads. Aim for top 10-15 cast members when available.
3. **Fight keyword:** Now a **Theme** (Interpersonal conflict block). Reserved strictly for physical body combat/confrontation scenes, not metaphorical struggles.
4. **Budget & Revenue:** Store in USD. TMDB provides this data for most films. Useful for profitability analysis.
5. **Taxonomy is extensible:** When a film's characteristics don't fit existing keywords, add new ones — but a new tag must be given a `sort_order` **inside the right sub-dimension block**, otherwise it lands at the 999 default and falls outside the block layout the sidebar and dashboards rely on. Add the label to `taxonomyGroups.ts` if you open a new block.
6. **French titles:** Many films in the list have French titles. Always store both original and French titles via film_language table.
7. **Awards:** Populated via Claude enrichment (major festivals and ceremonies: Oscars, Cannes, Venice, Berlin, César, BAFTA, Golden Globes). Claude knows award history for well-known films.
8. **Streaming:** Populated via TMDB watch/providers endpoint (`/movie/{id}/watch/providers`), mapped to our platform names. Streaming data is volatile — consider refreshing periodically.
9. **Main vs sub genres:** "is a main genre" = `category.sort_order < 200`. Any query that feeds a card badge, a genre pie chart or a genre-keyed heatmap must apply that filter — `historic_subcategory_name IS NULL` no longer discriminates (all 55 Genre rows are flat).

## Three Reference Films (validated classification)

These serve as ground truth for the taxonomy classification pipeline. They are kept in sync with `REFERENCE_EXAMPLES` in `backend/app/services/taxonomy_config.py` (which is what the enrichment prompt actually ships) and with `scripts/data/reference_films_fallback.json`. **Tagged under Taxonomy v2** — main genres first, then sub-genres.

### 2001: A Space Odyssey (1968)
- Genre: Science-Fiction, Drama, Adventure · odyssey/quest
- Theme: alien contact, AI/technology, death, time passing, transformation, philosophical, metaphysical, power, doubt/dilemma, exploration
- Time Period: prehistoric, 1950-60-70's, future, decades-spanning
- Place: space, desert — Geography: Kenya (Africa, diegetic)
- Atmosphere: contemplative/meditative, oppressive, mysterious, disturbing, psychedelic, symbolic, dreamlike/surreal, epic
- Character: solitary, tandem, android/robot (HAL 9000), alien, scientist/researcher
- Cinema Type: blockbuster, art house, slow cinema, new hollywood, aesthetics
- Source: novel — *The Sentinel*, Arthur C. Clarke

### La Haine (1995)
- Genre: Drama, Thriller · tragedy
- Theme: social, societal, generational, political, delinquency, death, police violence, immigration, trauma/accident, friendship, solidarity, rebellion/revolt, vengeance, fight, humanist, philosophical
- Time Period: 1980-90's, single day
- Place: urban, building — Geography: France / Île-de-France, Paris (diegetic)
- Atmosphere: violent, oppressive, depressive/sad, gritty/realistic, cityscape
- Character: trio, buddies, interracial, poor/marginal, teenager, cop
- Cinema Type: art house, black and white, realism, slang dialogs
- Source: original screenplay

### Mulholland Drive (2001)
- Genre: Drama, Thriller · psychological, crime, investigation, mafia/organized crime
- Theme: dream, art: cinema, identity crisis, amnesia, trauma/accident, love, obsession, jealousy, manipulation, lie, sex, adultery, vengeance, metaphysical
- Time Period: 2000-2010's
- Place: urban — Geography: United States / Los Angeles, Hollywood (diegetic)
- Atmosphere: mysterious, steamy, disturbing, oppressive, hypnotic/immersive, symbolic, dreamlike/surreal
- Character: tandem, couple, female lead, double, LGBT, star/celebrity
- Cinema Type: art house, flashback/non linear, aesthetics, neo-noir
- Source: original screenplay

## Project Structure

```
film-database/
├── CLAUDE.md              # This file — project context
├── PLAN.md                # Implementation plan & progress tracking
├── database/
│   ├── schema.sql         # PostgreSQL schema (DDL)
│   ├── seed_taxonomy.sql  # Pre-populate taxonomy reference tables
│   └── migrations/        # Schema migrations
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app entry
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic (TMDB, Claude, recommendations)
│   │   └── schemas/       # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Main views
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # Utilities, API client
│   ├── package.json
│   └── tailwind.config.js
├── scripts/
│   ├── parse_film_list.py # Parse Films_list.docx into structured data
│   ├── tmdb_fetcher.py    # TMDB API integration
│   ├── claude_enricher.py # Claude API taxonomy classification
│   └── bulk_ingest.py     # Orchestrate bulk film ingestion
└── .gitignore
```

## API Endpoints (planned)

| Endpoint | Method | Purpose |
|---|---|---|
| `/films` | GET | Paginated list with multi-filter query params |
| `/films/{id}` | GET | Full film detail with all relations |
| `/films/search` | GET | Full-text + faceted search across all taxonomy |
| `/films/{id}/recommendations` | GET | Similar films (in-DB + external via Claude) |
| `/films` | POST | Add new film (manual or from TMDB ID) |
| `/films/{id}` | PUT | Edit film metadata/tags |
| `/taxonomy/{type}` | GET | List all values for a taxonomy dimension |
| `/persons/{id}` | GET | Person filmography |
| `/films/enrich` | POST | Trigger Claude-based enrichment for a film |


## Quick Reference — Common Commands

All commands run from the project root: `G:\Users\Martin\GITHUB\film-database`

### Start / Restart Backend (FastAPI)
```bash
# Activate virtual environment first (if not already active)
.\.venv\Scripts\Activate.ps1

# Start (or restart by pressing Ctrl+C first if already running)
uvicorn backend.app.main:app --reload
```
The `--reload` flag auto-restarts on Python file changes, but does NOT reload when `.env` changes or when new dependencies are installed. In those cases, press **Ctrl+C** and re-run the command.

Backend runs at: http://localhost:8000
API docs (Swagger): http://localhost:8000/docs

### Start / Restart Frontend (Vite + React)
```bash
cd frontend
npm run dev
```
Vite hot-reloads on file changes automatically. Press **Ctrl+C** and re-run if you need a full restart.

Frontend runs at: http://localhost:3000

### Run a Database Migration
```bash
psql -U postgres -d film_database -f database/migrations/009_collection_id.sql
```
Replace the filename with the migration you need to run. Always restart the backend after schema or seed changes.

### Seed / Reset Database (from scratch)
```bash
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
python scripts/seed_reference_films.py --offline
python scripts/verify_db.py
```

### Refresh Image URLs from TMDB
```bash
# Film posters & backdrops
python scripts/refresh_posters.py

# Person photos (fixes tmdb_ids + updates photos via name matching)
python scripts/refresh_person_photos.py
python scripts/refresh_person_photos.py --diagnose    # check current state
python scripts/refresh_person_photos.py --dry-run     # preview changes
```

### Refresh Streaming Platforms
```bash
python scripts/refresh_streaming.py
python scripts/refresh_streaming.py --dry-run
python scripts/refresh_streaming.py --country BE    # Belgium instead of France
```

### Git Workflow
```bash
git add .
git commit -m "Step X: description"
git push origin main
```

---

## First-Time Setup

### Prerequisites
- **PostgreSQL** installed and running
- **Python 3.11+** with pip
- **Node.js 18+** with npm

### 1. Database
```bash
createdb -U postgres film_database
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
```

### 2. Python Backend
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 3. Frontend
```bash
cd frontend
npm install
```

### 4. Environment Variables
Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgre26@localhost:5432/film_database`
- `TMDB_API_KEY` — get from https://www.themoviedb.org/settings/api
- `ANTHROPIC_API_KEY` — get from https://console.anthropic.com/ (Settings → API Keys)

### 5. Seed Reference Data
```bash
python scripts/seed_reference_films.py --offline
python scripts/verify_db.py
```

### 6. Launch
Open two terminals:
```bash
# Terminal 1 — Backend
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```
Open http://localhost:3000 in your browser.