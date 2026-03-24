# Film Database — Implementation Plan

## Progress Tracker

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | PostgreSQL schema creation | ✅ DONE | schema.sql (603 lines) + seed_taxonomy.sql (445 lines) |
| 2 | TMDB integration module | ✅ DONE | tmdb_service.py, tmdb_mapper.py, parse_film_list.py, tmdb_resolver.py |
| 3 | Claude enrichment module | ✅ DONE | claude_enricher.py, taxonomy_config.py, enrichment_runner.py, db_inserter.py, test_enrichment_pipeline.py |
| 4 | Seed 3 reference films | ✅ DONE | 3 films inserted + verify_db.py ALL CHECKS PASSED |
| 4.5 | Fix: Awards + Streaming support | ✅ DONE | Awards via Claude enrichment, Streaming via TMDB watch/providers |
| 5 | Backend API (FastAPI) | 🔲 TODO | Filtering, CRUD, search |
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

## Step 4.5: Fix Awards + Streaming Support

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

### Planned Deliverables
- `backend/app/main.py` — FastAPI app entry
- `backend/app/models/` — SQLAlchemy ORM models
- `backend/app/routers/films.py` — Film CRUD + search + filter endpoints
- `backend/app/routers/taxonomy.py` — Taxonomy list endpoints
- `backend/app/routers/persons.py` — Person filmography endpoints
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/database.py` — DB connection and session management

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
