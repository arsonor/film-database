# Film Database — Implementation Plan

## Progress Tracker

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | PostgreSQL schema creation | ✅ DONE | schema.sql (603 lines) + seed_taxonomy.sql (445 lines) |
| 2 | TMDB integration module | ✅ DONE | tmdb_service.py, tmdb_mapper.py, parse_film_list.py, tmdb_resolver.py |
| 3 | Claude enrichment module | ✅ DONE | claude_enricher.py, taxonomy_config.py, enrichment_runner.py, db_inserter.py, test_enrichment_pipeline.py |
| 4 | Seed 3 reference films | ✅ DONE | 3 films inserted + verify_db.py ALL CHECKS PASSED |
| 4.5 | Fix: Awards + Streaming support | ✅ DONE | Awards via Claude enrichment, Streaming via TMDB watch/providers |
| 5 | Backend API (FastAPI) | ✅ DONE | SQLAlchemy ORM, CRUD, filtering, search, taxonomy endpoints |
| 6 | Frontend: search grid + filters | 🔲 TODO | Poster grid, filter sidebar |
| 7 | Film detail view + edit | 🔲 TODO | Full detail panel, tag editing |
| 8 | Add Film workflow | 🔲 TODO | TMDB search → Claude enrich → save |
| 9 | Recommendation engine (in-DB) | 🔲 TODO | Tag similarity scoring |
| 10 | Claude-powered recommendations | 🔲 TODO | External film suggestions |
| 11 | Bulk ingestion (~2500 films) | 🔲 TODO | Parse Films_list.docx, batch process |
| 12 | Dashboard & stats | 🔲 TODO | Analytics, charts, coverage |

---

## Step 1: PostgreSQL Schema ✅

- `database/schema.sql` (603 lines) — Full DDL, 40+ indexes, updated_at trigger
- `database/seed_taxonomy.sql` (445 lines) — All lookup tables pre-populated

## Step 2: TMDB Integration Module ✅

- `backend/app/services/tmdb_service.py` — Async TMDB client
- `backend/app/services/tmdb_mapper.py` — TMDB → DB mapper
- `scripts/parse_film_list.py` — Films_list.docx parser
- `scripts/tmdb_resolver.py` — Batch resolver with resume

## Step 3: Claude Enrichment Module ✅

- `backend/app/services/claude_enricher.py` — Taxonomy classification via Claude API
- `backend/app/services/taxonomy_config.py` — All valid taxonomy values + reference examples
- `scripts/claude_enrichment_runner.py` — CLI batch enrichment
- `scripts/db_inserter.py` — Full DB insertion pipeline
- `scripts/test_enrichment_pipeline.py` — Validation against reference films

## Step 4: Seed 3 Reference Films ✅

- `scripts/data/reference_films_fallback.json` — Complete pre-built data for 3 films
- `scripts/seed_reference_films.py` — Orchestration (full + offline modes)
- `scripts/verify_db.py` — 14 verification queries + PASS/FAIL (fixed: per-query connections)
- `database/setup_db.sh` + `database/setup_db.py` — DB setup scripts

### Known Issues Fixed
- `setup_db.py`: SQL parsing fails on $$ blocks — workaround: use `psql` directly
- `verify_db.py`: transaction poisoning with asyncpg — fixed: each query uses its own connection

## Step 4.5: Fix Awards + Streaming Support ✅

### Problem
Schema has `award` and `stream_platform`/`film_exploitation` tables but nothing in the pipeline populates them.

### Solution
- **Awards:** Add to Claude enrichment prompt (Claude knows Oscar, Cannes, César, etc.). Add awards to reference film examples, db_inserter, verify_db.
- **Streaming:** Add `get_watch_providers()` to TMDB service (uses `/movie/{id}/watch/providers`). Map TMDB provider names to our platform names. Add to db_inserter, verify_db.

### Files Modified
- `claude_enricher.py` — awards section in enrichment prompt + validation
- `taxonomy_config.py` — awards in reference examples
- `tmdb_service.py` — `get_watch_providers()` method
- `tmdb_mapper.py` — `PROVIDER_NAME_MAP` + `map_watch_providers()` + `streaming_platforms` in output
- `db_inserter.py` — `_insert_awards()`, `_insert_streaming()`, updated `_clear_junctions()`
- `reference_films_fallback.json` — awards data + streaming_platforms field
- `verify_db.py` — queries 15 (awards), 16 (streaming), updated completeness check
- `CLAUDE.md` — documented awards/streaming approach

### Re-seed After Fix
```bash
psql -U postgres -d film_database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
python scripts/seed_reference_films.py --offline
python scripts/verify_db.py
```

---

## Step 5: Backend API (FastAPI)

### Objective
Build the full REST API that serves as the bridge between the database and the future frontend. This API must expose all film data with rich filtering, support CRUD operations, and provide taxonomy endpoints for filter dropdowns.

### Architecture Decisions
- **Async throughout:** SQLAlchemy 2.0 async with asyncpg (already installed)
- **Raw SQL preferred for complex queries:** The schema uses many junction tables; SQLAlchemy ORM for models but raw SQL (via `text()`) for complex multi-join filter queries to keep them readable and performant
- **Pydantic v2** for request/response schemas
- **CORS enabled** for local frontend dev (localhost:3000)

### Planned Deliverables

**Core files:**
- `backend/app/main.py` — FastAPI app with CORS, lifespan (DB pool startup/shutdown), router includes
- `backend/app/database.py` — Async engine + session factory using DATABASE_URL from .env
- `backend/app/models/__init__.py` — SQLAlchemy ORM models reflecting schema.sql (Film, Person, PersonJob, Crew, Casting, Studio, Production, Language, FilmLanguage, Category, FilmGenre, CinemaType, FilmTechnique, CulturalMovement, FilmMovement, Geography, FilmSetPlace, TimePeriod, FilmPeriod, PlaceContext, FilmPlace, ThemeContext, FilmTheme, CharactersType, FilmCharacters, CharacterContext, FilmCharacterContext, Atmosphere, FilmAtmosphere, MessageConveyed, FilmMessage, Motivation, FilmMotivation, Source, FilmOrigin, StreamPlatform, FilmExploitation, Award, FilmSequel)
- `backend/app/schemas/film.py` — Pydantic schemas: FilmListItem (compact for grid), FilmDetail (full with all relations), FilmCreate, FilmUpdate, FilmSearchParams
- `backend/app/schemas/taxonomy.py` — TaxonomyItem, TaxonomyList
- `backend/app/schemas/person.py` — PersonSummary, PersonDetail
- `backend/app/routers/films.py` — Film endpoints: list (paginated + filtered), detail, search, create, update
- `backend/app/routers/taxonomy.py` — Taxonomy endpoints: one per dimension (categories, themes, atmospheres, etc.)
- `backend/app/routers/persons.py` — Person filmography endpoint

**Key endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/films` | GET | Paginated list with multi-filter: categories, themes, atmosphere, time_period, director, year range, search query. Returns FilmListItem[] |
| `GET /api/films/{id}` | GET | Full film detail with all junction data (cast, crew, themes, etc.). Returns FilmDetail |
| `GET /api/films/search` | GET | Full-text search across original_title, all film_language titles, person names, summary |
| `POST /api/films` | POST | Create film from TMDB data + enrichment JSON |
| `PUT /api/films/{id}` | PUT | Update film metadata and tag junctions |
| `GET /api/taxonomy/{dimension}` | GET | List all values for a taxonomy dimension (e.g., /api/taxonomy/categories) |
| `GET /api/persons/{id}` | GET | Person detail with filmography |
| `GET /api/stats` | GET | DB statistics: film count, genre distribution, decade distribution |

**Filtering logic for `GET /api/films`:**
- Multiple filter params: `?categories=Drama,Thriller&atmosphere=mysterious&year_min=1990&year_max=2005&director=David+Lynch`
- All filters are AND-combined
- Multi-value within a dimension is OR (e.g., categories=Drama,Thriller → Drama OR Thriller)
- Pagination: `?page=1&per_page=20`
- Sorting: `?sort_by=year&sort_order=desc` (supported: year, title, duration, budget, revenue)

### Validation
After implementation:
1. `uvicorn backend.app.main:app --reload` should start without errors
2. `GET /docs` → Swagger UI should list all endpoints
3. `GET /api/films` → Should return the 3 seeded films
4. `GET /api/films?categories=Drama` → Should filter correctly
5. `GET /api/films/1` → Should return full film detail with all junctions populated
6. `GET /api/taxonomy/categories` → Should return all seeded category values

---

## Environment Setup

### PostgreSQL
```bash
createdb -U postgres film_database
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
```

### Python
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Seed Data
```bash
python scripts/seed_reference_films.py --offline
python scripts/verify_db.py
```

### API Keys (.env)
- `DATABASE_URL=postgresql+asyncpg://postgres:postgre26@localhost:5432/film_database`
- `TMDB_API_KEY` — https://www.themoviedb.org/settings/api
- `ANTHROPIC_API_KEY` — for Claude enrichment
