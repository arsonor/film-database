# Film Database — Implementation Plan

## Progress Tracker

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | PostgreSQL schema creation | ✅ DONE | schema.sql (603 lines) + seed_taxonomy.sql (445 lines) |
| 2 | TMDB integration module | ✅ DONE | tmdb_service.py, tmdb_mapper.py, parse_film_list.py, tmdb_resolver.py |
| 3 | Claude enrichment module | ✅ DONE | claude_enricher.py, taxonomy_config.py, enrichment_runner.py, db_inserter.py, test_enrichment_pipeline.py |
| 4 | Seed 3 reference films | ✅ DONE | 3 films inserted + verify_db.py ALL CHECKS PASSED |
| 4.5 | Fix: Awards + Streaming support | ✅ DONE | Awards via Claude enrichment, Streaming via TMDB watch/providers |
| 5 | Backend API (FastAPI) | ✅ DONE | 12 files, 3 routers, 13 taxonomy dimensions, fix: transaction + theme hierarchy |
| 5.5 | API: Geography search + Language filter + missing filter params | ✅ DONE | New geography endpoint, language taxonomy+filter, character_contexts+place_contexts filters |
| 6 | Frontend: browse + search + filters | 🔲 TODO | React + Tailwind + shadcn/ui, poster grid, filter sidebar |
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

## Step 5: Backend API (FastAPI) ✅

### Objective
Full REST API bridging the database and the frontend. Exposes all film data with rich filtering, CRUD operations, taxonomy endpoints for filter dropdowns, and person filmography.

### Files Created (12)
- `backend/app/__init__.py` — Package init
- `backend/app/database.py` — Async SQLAlchemy engine + session factory + get_db dependency
- `backend/app/models/__init__.py` — 38 SQLAlchemy ORM models mirroring schema.sql
- `backend/app/schemas/film.py` — FilmListItem, FilmDetail, FilmCreate, FilmUpdate, PaginatedFilms + sub-schemas
- `backend/app/schemas/taxonomy.py` — TaxonomyItem, TaxonomyList
- `backend/app/schemas/person.py` — PersonSummary, PersonDetail, FilmographyEntry
- `backend/app/schemas/__init__.py` — Package init
- `backend/app/routers/films.py` — GET list (paginated+filtered), GET detail, POST create, PUT update, GET stats
- `backend/app/routers/taxonomy.py` — GET /taxonomy/{dimension} (13 dimensions via single dynamic endpoint)
- `backend/app/routers/persons.py` — GET search, GET detail with filmography
- `backend/app/routers/__init__.py` — Package init
- `backend/app/main.py` — FastAPI app with CORS (localhost:3000), lifespan, router includes

### Also Modified
- `database/seed_taxonomy.sql` — Added sport sub-themes (sport: motor, sport: individual, sport: collective, sport: tournament)
- `backend/app/services/taxonomy_config.py` — Synced sport sub-themes in VALID_THEMES
- `backend/STEP5_VALIDATION.md` — 24-point test checklist

### Architecture Decisions
- Raw SQL via `text()` for complex filtered list query (avoids cartesian products from 15+ JOINs)
- Batch loading for list endpoint: categories + directors loaded in 2 extra queries instead of N+1
- `ANY(:param)` array binding for taxonomy filter subqueries
- Create endpoint follows exact same insertion pattern as `scripts/db_inserter.py`
- Update endpoint uses clear-and-reinsert for junction tables

### Fixes Applied During Validation
- **Transaction bug:** Removed nested `db.begin()` in create/update endpoints — SQLAlchemy async session auto-begins a transaction; replaced with `await db.commit()` at the end
- **Theme hierarchy:** Taxonomy endpoint now aggregates sub-theme film counts into parent items (e.g., "art" shows sum of all "art: *" sub-themes)

### Known Limitation
- Person details (gender, date_of_birth, nationality) always null — TMDB mapper only extracts name/photo. Needs future enhancement to call TMDB `/person/{id}` endpoint.

---

## Step 5.5: API Enhancements — Geography, Language & Missing Filters ✅

### Problem
The frontend needs additional filtering capabilities that are missing from the Step 5 API:

1. **Geography:** The `country` filter only searches `geography.country` via ILIKE. There's no way to find all films set in "Paris" or "Los Angeles" (state_city level), no autocomplete endpoint, and no taxonomy-style listing of locations with film counts.

2. **Language:** There's no language filter at all. The `language` table and `film_language` junction exist, but neither a taxonomy endpoint nor a filter param were implemented. Filtering by original language (e.g., "all Japanese films") is a natural use case.

3. **Missing taxonomy filter params:** The `GET /api/films` endpoint is missing filter params for `character_contexts` and `place_contexts`, even though both dimensions have taxonomy endpoints and junction tables. The frontend needs these to offer complete filtering.

### Files Created (2)
- `backend/app/routers/geography.py` — GET /api/geography/search?q= + GET /api/geography/countries
- `backend/app/schemas/geography.py` — GeographySearchResult, CountryItem

### Files Modified (3)
- `backend/app/routers/films.py` — Added location, language, character_contexts, place_contexts filter params
- `backend/app/routers/taxonomy.py` — Added "languages" dimension with is_original filtering
- `backend/app/main.py` — Included geography router

---

## Step 6: Frontend — Browse, Search & Filter

### Objective
Build the main frontend interface: a responsive film browser with poster grid, taxonomy-based filter sidebar, search bar, active filter chips, sorting, and pagination. This view is the primary way to explore the film database.

### Tech Stack
- **Vite + React 18 + TypeScript**
- **Tailwind CSS** for utility styling
- **shadcn/ui** for pre-built UI components (Button, Badge, Input, Select, ScrollArea, Sheet, Skeleton, etc.)
- **Lucide React** for icons (ships with shadcn/ui)
- API calls: native `fetch` with typed wrapper (no heavy libraries)

### Architecture

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # Typed API client (fetch wrapper)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx      # Top bar with search + sort controls
│   │   │   ├── Sidebar.tsx     # Filter sidebar (desktop) + Sheet (mobile)
│   │   │   └── Layout.tsx      # Main layout shell
│   │   ├── films/
│   │   │   ├── FilmGrid.tsx    # Responsive poster grid
│   │   │   ├── FilmCard.tsx    # Individual poster card
│   │   │   └── Pagination.tsx  # Page navigation
│   │   └── filters/
│   │       ├── FilterSection.tsx   # Collapsible section for one taxonomy
│   │       ├── ActiveFilters.tsx   # Removable filter chip bar
│   │       └── FilterChip.tsx      # Individual clickable/removable chip
│   ├── hooks/
│   │   ├── useFilms.ts         # Film list fetching + state
│   │   ├── useTaxonomy.ts      # Taxonomy data fetching
│   │   └── useFilterState.ts   # Filter state management + URL sync
│   ├── types/
│   │   └── api.ts              # TypeScript types matching API schemas
│   ├── lib/
│   │   └── utils.ts            # shadcn/ui cn() utility + helpers
│   ├── App.tsx                 # Root with routing
│   └── main.tsx                # Vite entry point
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── components.json             # shadcn/ui config
```

### UI Design — Filter Sidebar

Taxonomy chip sections (11):
1. Categories
2. Themes
3. Atmospheres
4. Character Types (characters_type)
5. Character Contexts (character_context — archetypes, age, gender…)
6. Motivations
7. Messages
8. Cinema Types
9. Cultural Movements
10. Time Periods
11. Place Contexts (urban, space, road movie…)

Special filter inputs:
12. Location — autocomplete text input backed by `GET /api/geography/search?q=`
13. Language — dropdown or autocomplete backed by `GET /api/taxonomy/languages`
14. Director — free text input (debounced)
15. Year range — two number inputs (min/max)
16. Seen toggle — 3-state: All / Seen / Unseen

*(Full implementation details — scaffolding, components, hooks, theming, technical notes — in PROMPTS.md Step 6 Prompt, sections A through J)*

### Validation

After implementation:
1. `cd frontend && npm install && npm run dev` → starts on http://localhost:3000
2. Backend must be running on http://localhost:8000
3. Film grid shows the 3 seeded films with poster images
4. Clicking a category chip in sidebar filters the grid
5. Search bar filters by typing (e.g., "Kubrick" → shows 2001)
6. Active filters appear as removable chips above the grid
7. Sort by title/year works correctly
8. Pagination works (test with per_page=2)
9. URL updates when filters change (browser back button works)
10. Mobile responsive: sidebar becomes slide-in drawer
11. Loading skeletons display during API calls

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
