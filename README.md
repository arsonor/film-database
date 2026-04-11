# Film Database

A personal film database application with a rich taxonomy-based filtering interface, AI-powered enrichment, and a recommendation engine. The database contains ~3200+ films spanning from 1902 to 2026.

## Features

- **Browse & Filter** — Explore films with 11 taxonomy dimensions (categories, themes, atmospheres, characters, motivations, etc.), plus location, language, studio, and year range filters
- **Film Detail** — Full metadata view with poster/backdrop, cast & crew, classification tags, awards, streaming platforms, related films, and similar films carousel
- **Inline Editing** — Edit taxonomy tags, financials, awards, and film relations directly from the detail page
- **Add Film** — Search TMDB, auto-enrich with Claude AI taxonomy classification, review and save
- **Taxonomy Admin** — Add, rename, merge, and delete taxonomy values from `/admin/taxonomy`
- **Seen/Unseen Toggle** — Track which films you've seen, toggle directly from the browse grid or detail page
- **Bulk Ingestion Pipeline** — Parse filmographies from .docx, resolve via TMDB, enrich via Claude Batch API, insert into DB

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL |
| Backend | Python, FastAPI, SQLAlchemy (async) |
| Frontend | React, TypeScript, Tailwind CSS, shadcn/ui |
| Data API | TMDB (The Movie Database) |
| AI Enrichment | Claude API (Anthropic) — taxonomy classification, batch processing |

## Project Structure

```
film-database/
├── database/
│   ├── schema.sql              # PostgreSQL schema (DDL)
│   ├── seed_taxonomy.sql       # Taxonomy lookup tables seed data
│   └── migrations/             # Schema migrations
├── backend/
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── routers/            # API route handlers (films, taxonomy, persons, geography)
│       ├── services/           # Business logic (TMDB, Claude, recommendations, taxonomy config)
│       └── schemas/            # Pydantic request/response models
├── frontend/
│   └── src/
│       ├── pages/              # BrowsePage, FilmDetailPage, AddFilmPage, TaxonomyAdminPage
│       ├── components/         # UI components (layout, films, filters, admin)
│       ├── hooks/              # Custom React hooks
│       ├── api/                # API client
│       └── lib/                # Utilities
├── scripts/
│   ├── parse_film_list.py      # Parse Films_list.docx into structured JSON
│   ├── tmdb_resolver.py        # Resolve film titles to TMDB IDs
│   ├── claude_batch_enrichment.py  # Claude Batch API enrichment pipeline
│   ├── db_inserter.py          # Insert enriched films into PostgreSQL
│   ├── export_taxonomy.py      # Regenerate seed_taxonomy.sql + taxonomy_config.py from DB
│   ├── backfill_person_details.py  # Fetch person details from TMDB
│   ├── refresh_posters.py      # Refresh poster/backdrop URLs from TMDB
│   ├── refresh_person_photos.py    # Refresh person photo URLs from TMDB
│   ├── refresh_streaming.py    # Update streaming platform availability
│   └── verify_db.py            # Database verification script
├── CLAUDE.md                   # Project context for Claude Code
├── PLAN.md                     # Implementation plan & progress
└── .env                        # Environment variables (not committed)
```

## How to Run

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
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Environment Variables

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL=postgresql+asyncpg://postgres:<password>@localhost:5432/film_database`
- `TMDB_API_KEY` — get from https://www.themoviedb.org/settings/api
- `ANTHROPIC_API_KEY` — get from https://console.anthropic.com/ (Settings > API Keys)

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
```
Backend: http://localhost:8000 | Swagger docs: http://localhost:8000/docs

```bash
# Terminal 2 — Frontend
cd frontend
npm run dev
```
Frontend: http://localhost:3000

### Common Commands

```bash
# Run a database migration
psql -U postgres -d film_database -f database/migrations/<migration>.sql

# Seed / reset database from scratch
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql

# Refresh image URLs from TMDB
python scripts/refresh_posters.py
python scripts/refresh_person_photos.py

# Refresh streaming platform data
python scripts/refresh_streaming.py
python scripts/refresh_streaming.py --dry-run
python scripts/refresh_streaming.py --country BE

# Backfill person details (directors, composers, top-6 cast)
python scripts/backfill_person_details.py
python scripts/backfill_person_details.py --dry-run

# Export taxonomy from DB to source files
python scripts/export_taxonomy.py
python scripts/export_taxonomy.py --dry-run
```

## Taxonomy Dimensions

Films are classified across 11 dimensions:

| Dimension | Examples |
|-----------|---------|
| Categories | Action, Drama, Comedy, Science-Fiction, Historical: biopic |
| Cinema Types | art house, blockbuster, animation, black and white |
| Cultural Movements | new wave, neo-noir, expressionism, blaxploitation |
| Themes | war, investigation, dystopia, art: cinema, survival |
| Characters | solitary, couple, ensemble cast, buddies |
| Character Contexts | teenager, female, antihero, vampire, android |
| Atmospheres | contemplative, violent, mysterious, hypnotic |
| Motivations | vengeance, redemption, quest, manipulation |
| Messages | satirical, philosophical, feminist, black comedy |
| Time Periods | WW2, contemporary, medieval, future |
| Place Contexts | urban, space, road movie, huis clos |


