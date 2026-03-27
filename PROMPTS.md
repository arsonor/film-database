# Claude Code Prompts — Step-by-step

## Step 1 Prompt — PostgreSQL Schema Creation ✅ DONE

*(see git history for original prompt)*

---

## Step 2 Prompt — TMDB Integration Module ✅ DONE

*(see git history for original prompt)*

---

## Step 3 Prompt — Claude Enrichment Module ✅ DONE

*(see git history for original prompt)*

---

## Step 4 Prompt — Seed 3 Reference Films ✅ DONE

*(see git history for original prompt)*

---

## Step 4.5 Prompt — Fix: Awards + Streaming Platform Support ✅ DONE

*(see git history for original prompt)*

---

## Step 5 Prompt — Backend API (FastAPI) ✅ DONE

*(see git history for original prompt)*

### Step 5 Summary
- 12 files created: database.py, models, 3 schema files, 3 routers, main.py, package inits
- 3 routers: films (list+filter+detail+create+update+stats), taxonomy (13 dimensions), persons (search+detail)
- Fixes applied: removed nested db.begin() (session auto-begins), added hierarchical theme count aggregation
- Also updated: seed_taxonomy.sql (sport sub-themes), taxonomy_config.py (sync)

---

## Step 5.5 Prompt — API Enhancements: Geography, Language & Missing Filters ✅ DONE

*(see git history for original prompt)*

### Step 5.5 Summary
- 2 new files: geography.py router (search + countries endpoints), geography.py schemas
- 3 modified files: films.py (added location, language, character_contexts, place_contexts filter params), taxonomy.py (added "languages" dimension with is_original filtering), main.py (geography router)
- Location filter searches across continent + country + state_city (replaces old country-only filter, backward compat kept)
- Language filter uses is_original = TRUE to filter by original language

---

## Step 6 Prompt — Frontend: Browse, Search & Filter ✅ DONE

*(see git history for original prompt)*

### Step 6 Summary
- Full frontend app: Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui
- Dark theme (charcoal #0f0f0f, amber #f59e0b accent, Letterboxd/Criterion aesthetic)
- 2 pages: BrowsePage (main grid+filters), FilmDetailPage (placeholder for step 7)
- 3 layout components: Layout, Header (search+sort), Sidebar (16 filter controls, Sheet on mobile)
- 3 film components: FilmGrid (responsive 2-6 cols, skeletons), FilmCard (poster+metadata+seen), Pagination
- 3 filter components: FilterSection (collapsible), FilterChip (amber toggle), ActiveFilters (removable chips bar)
- 3 hooks: useFilterState (URL-synced), useFilms (debounced fetch), useTaxonomy (11 dimensions cached)
- Also: scripts/refresh_posters.py (TMDB CDN refresh), fixed La Haine tmdb_id (3405→406)

---

## Step 6.5 Prompt — Taxonomy Refinements + Filter UX Fixes ✅ DONE

*(see git history for original prompt)*

### Step 6.5 Summary
- Migration `database/migrations/006_sort_order.sql`: added sort_order columns to theme_context and time_context, merged themes (trauma+accident → trauma/accident, technology+artificial_intelligence → AI/technology), removed survival from motivations, set sort_order values for thematic groupings and chronological time periods
- Seed data: added Documentary category, added Historical: event subcategory, updated sort_order in seed_taxonomy.sql
- Backend `films.py`: replaced OR logic with AND logic (HAVING COUNT) for all taxonomy filters, added parent expansion for hierarchical dims (themes, categories), special composite-key handling for categories filter, added studios filter param
- Backend `taxonomy.py`: added studios dimension, SORTED_DIMENSIONS set for sort_order-based ordering, categories now returns "Parent: sub" display format, added HIERARCHICAL_DIMENSIONS for count aggregation
- Frontend: removed Director filter from Sidebar/ActiveFilters/FilterState/API client, replaced year inputs with DualRangeSlider component, added Studios dropdown, added group separators in FilterSection for themes/time_periods based on sort_order gaps
- Updated taxonomy_config.py to sync merged theme names

---

## Step 7 Prompt — Film Detail View + Edit ✅ DONE

*(see git history for original prompt)*

### Step 7 Summary
- Full detail page: cinematic hero (backdrop gradient, poster, meta, category badges, director links), seen/unseen toggle (PATCH `/films/{id}/vu`), external links (TMDB, IMDb, Allociné, Wikipedia)
- Cast: horizontal scrollable PersonCard components with TMDB photos, clickable → `/browse?q=Name`
- Crew: grouped by role (Director, Writer, Cinematographer, Composer, etc.)
- All taxonomy sections with inline editing via EditableTagSection (view/edit toggle, autocomplete add, remove tags, save/cancel)
- Awards table (trophy icons), streaming badges, related films, similar films placeholder
- 7 new components: PersonCard, SectionHeading, EditableTagSection, ExternalLinks, AwardsTable, SimilarFilmsCarousel, useFilmDetail hook
- 3 modified files: types/api.ts (8 new interfaces), api/client.ts (3 new functions), lib/utils.ts (3 new helpers)
- Bug fixes: tag dropdown `.slice(0,15)` cap removed + `max-h` increased; person tmdb_ids fixed via name-matching against TMDB movie credits
- New script: `refresh_person_photos.py` (matches by name, fixes tmdb_id + photo_url, `--diagnose`/`--restore`/`--dry-run`/`--verbose` modes)

---

## Step 8 Prompt — Add Film Workflow

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 8 specification (sections A through H). Then read ALL of the following files to understand the current codebase:

**Backend — Existing services (the pipeline to wire up):**
- `backend/app/services/tmdb_service.py` — `TMDBService` class: `search_film(title, year)`, `get_film_details(tmdb_id)`, `get_film_details_fr(tmdb_id)`, `get_watch_providers(tmdb_id)`, `build_poster_url()`. Uses `httpx.AsyncClient`, has rate limiting built in. Needs `api_key` in constructor.
- `backend/app/services/tmdb_mapper.py` — `TMDBMapper` class: `map_film_to_db(tmdb_data, fr_data)` returns dict with keys: `film`, `titles`, `categories`, `historic_subcategories`, `crew`, `cast`, `studios`, `languages`, `keywords`, `production_countries`, `streaming_platforms`. Also `map_watch_providers(providers)`.
- `backend/app/services/claude_enricher.py` — `ClaudeEnricher` class: `enrich_film(tmdb_mapped_data)` takes the mapper output, calls Claude API, returns enrichment dict with all taxonomy classifications. Needs `api_key` in constructor. Can take 5-15 seconds.
- `backend/app/services/taxonomy_config.py` — Valid taxonomy values used for Claude prompt and validation.

**Backend — Existing API (reuse for save):**
- `backend/app/routers/films.py` — `POST /api/films` creates a film from `FilmCreate` schema. Already handles all junction table insertions (cast, crew, studios, taxonomy, awards, streaming). Also `GET /api/films/{film_id}` for detail.
- `backend/app/schemas/film.py` — `FilmCreate` schema: expects `film` (dict), `titles`, `crew`, `cast`, `studios`, `enrichment` (dict), `streaming_platforms`, etc.
- `backend/app/main.py` — Current routers registered: films, taxonomy, persons, geography. New router must be added here.
- `backend/app/database.py` — `get_db` dependency for DB sessions.

**Frontend — Existing code to reference/reuse:**
- `frontend/src/pages/FilmDetailPage.tsx` — Detail page layout (reference for preview styling)
- `frontend/src/components/films/EditableTagSection.tsx` — Reusable tag editing component (reuse in review step)
- `frontend/src/components/films/PersonCard.tsx` — Person display (reuse in preview cast/crew)
- `frontend/src/components/layout/Header.tsx` — Where to add the "Add Film" navigation button
- `frontend/src/api/client.ts` — Existing API client pattern (fetchJson, ApiError)
- `frontend/src/types/api.ts` — Existing types
- `frontend/src/App.tsx` — Route definitions (add `/add` route)
- `frontend/src/index.css` — Dark theme variables

**Also read for context:**
- `backend/requirements.txt` — Already includes `anthropic`, `httpx`, etc.
- `.env.example` — Shows expected env vars (DATABASE_URL, TMDB_API_KEY, ANTHROPIC_API_KEY)

### Goal

Create a 3-step "Add Film" workflow accessible from the frontend. The user searches for a film by title on TMDB, the system fetches full details and classifies it with Claude AI, the user reviews/edits the proposed tags, and saves to the database.

### Step-by-step flow:

**1. Search (frontend → backend → TMDB API):**
- User types a title (+ optional year) and clicks Search
- `GET /api/add-film/search?title=...&year=...` calls `TMDBService.search_film()`
- Returns candidates with poster, title, year, overview
- Candidates already in the DB are flagged `already_in_db: true`

**2. Enrich (frontend → backend → TMDB + Claude APIs):**
- User selects a candidate
- `POST /api/add-film/enrich` with `{ tmdb_id }` triggers the full pipeline:
  - `TMDBService.get_film_details()` + `get_film_details_fr()` → raw TMDB data
  - `TMDBMapper.map_film_to_db()` → structured data
  - `TMDBService.get_watch_providers()` + `TMDBMapper.map_watch_providers()` → streaming
  - `ClaudeEnricher.enrich_film()` → taxonomy classification
- Returns a complete preview payload (matches `FilmCreate` structure)
- Frontend shows all proposed data in an editable preview
- If Claude fails: return TMDB data with empty enrichment, flag the failure

**3. Save (frontend → backend → PostgreSQL):**
- User reviews tags, edits as needed, clicks "Add to Database"
- `POST /api/films` (existing endpoint) receives the payload
- Film is inserted with all relations
- Frontend redirects to `/films/{new_film_id}`

### Backend Implementation Details

**New files:**
- `backend/app/routers/add_film.py` — New router with search + enrich endpoints
- `backend/app/schemas/add_film.py` — TMDBSearchResult, TMDBSearchResponse, EnrichRequest, EnrichmentPreview

**Modified files:**
- `backend/app/main.py` — Register the `add_film` router

**Service initialization pattern:**
```python
# In add_film.py router
import os
from backend.app.services.tmdb_service import TMDBService
from backend.app.services.tmdb_mapper import TMDBMapper
from backend.app.services.claude_enricher import ClaudeEnricher

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
```

For `TMDBService` which uses `httpx.AsyncClient`: create and close it per request using `async with`:
```python
async with TMDBService(TMDB_API_KEY) as tmdb:
    results = await tmdb.search_film(title, year)
```

For `ClaudeEnricher`: it uses `anthropic.AsyncAnthropic` which manages its own connection — can be instantiated per request without concern.

### Frontend Implementation Details

**New files:**
- `frontend/src/pages/AddFilmPage.tsx` — Multi-step wizard (Search → Review → Save)
- `frontend/src/hooks/useAddFilm.ts` — (optional) Hook to manage the add-film state machine

**Modified files:**
- `frontend/src/types/api.ts` — TMDBSearchResult, EnrichmentPreview interfaces
- `frontend/src/api/client.ts` — searchTMDB, enrichFilm, saveFilm functions
- `frontend/src/App.tsx` — Add `/add` route
- `frontend/src/components/layout/Header.tsx` — Add "+" button navigating to `/add`

**The AddFilmPage has three internal states:**
1. `searching` — shows search form + results grid
2. `enriching` — shows loading spinner with progress messages
3. `reviewing` — shows full editable preview with "Add to Database" button

**Key UX considerations:**
- The enrichment step takes 5-15 seconds (Claude API). Show a clear loading state with animated messages: "Fetching from TMDB...", "Classifying with AI...", "Preparing preview..."
- The review/edit step should reuse the tag editing pattern from `EditableTagSection` — all taxonomy sections start in edit mode
- Films already in DB should be clearly indicated in search results (grayed out poster, "Already in database" label, link to existing detail page)
- A "Back to Search" button in the review step lets the user go back without losing context

### Validation

After implementation:
1. "+" button in header navigates to `/add`
2. Search "Inception" → TMDB candidates appear with posters
3. Click a candidate → enrichment loading state with progress messages
4. Preview loads: film info + all Claude-proposed taxonomy tags
5. Tags are editable (can remove/add in each section)
6. "Add to Database" → film saves, redirect to new detail page
7. Film appears in browse grid with correct poster and data
8. Search same film again → flagged "already in database"
9. French title search works (e.g., "Les Quatre Cents Coups")
10. If Claude API fails: preview shows with empty tags, user can add manually
11. If TMDB search returns no results: clear "no results" message
12. Mobile responsive across all 3 steps

Do NOT run the server or npm commands yourself. Just create/modify the files correctly. The user will run and test manually.
