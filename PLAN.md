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
| 6 | Frontend: browse + search + filters | ✅ DONE | Vite + React + TS + Tailwind + shadcn/ui, dark theme, 11 taxonomy filters + location/language |
| 6.5 | Taxonomy refinements + filter UX fixes | ✅ DONE | AND logic, sort_order, theme merges, Historical subcategories, studios filter, dual-slider |
| 7 | Film detail view + edit | ✅ DONE | Full detail page, tag editing, vu toggle, external links, person navigation, person photo fix |
| 8 | Add Film workflow | 🔄 IN PROGRESS | TMDB search → Claude enrich → review → save |
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
- `scripts/verify_db.py` — 14 verification queries + PASS/FAIL
- `database/setup_db.sh` + `database/setup_db.py` — DB setup scripts

## Step 4.5: Fix Awards + Streaming Support ✅

*(see PLAN.md git history for details)*

## Step 5: Backend API (FastAPI) ✅

*(see PLAN.md git history for details)*

## Step 5.5: API Enhancements — Geography, Language & Missing Filters ✅

*(see PLAN.md git history for details)*

## Step 6: Frontend — Browse, Search & Filter ✅

*(see PLAN.md git history for details)*

## Step 6.5: Taxonomy Refinements + Filter UX Fixes ✅

- Migration `006_sort_order.sql` — sort_order columns, theme merges (trauma/accident, AI/technology), motivation cleanup
- Backend: AND logic (HAVING COUNT) in all taxonomy filters, parent expansion for hierarchical dims (themes, categories)
- Backend: Categories filter handles composite "Parent: sub" format, studios filter + taxonomy dimension
- Frontend: Director filter removed, dual-handle year range slider, studios dropdown, theme/time group separators

## Step 7: Film Detail View + Edit ✅

- Full detail page with cinematic hero section (backdrop gradient, poster, meta, vu toggle, external links)
- Cast/crew sections with TMDB photos, clickable → `/browse?q=Name`
- All taxonomy sections with inline editing (EditableTagSection)
- Awards table, streaming badges, related films, similar films placeholder
- Backend: PATCH `/films/{id}/vu` for lightweight toggle
- Bug fixes: tag dropdown cap removed (was limited to 15), person photo tmdb_id mismatch fixed
- New script: `refresh_person_photos.py` (name-based matching against TMDB movie credits)

---

## Step 8: Add Film Workflow

### Goal

Let the user add a new film to the database from the frontend through a guided 3-step process: **Search → Enrich → Save**. This connects the three backend pipelines (TMDB service, Claude enrichment, DB insertion) built in steps 2-4 into a single interactive flow exposed via API endpoints and a frontend wizard.

This step also serves as an end-to-end integration test for the full pipeline before bulk ingestion at step 11.

### A. Backend: New Router — `backend/app/routers/add_film.py`

Create a new router with three endpoints that orchestrate the add-film pipeline:

**1. `GET /api/add-film/search?title=...&year=...`** — Search TMDB for candidates

Uses the existing `TMDBService.search_film()`. Returns a list of candidates:
```python
@router.get("/add-film/search")
async def search_tmdb(
    title: str = Query(..., min_length=1),
    year: int | None = None,
):
    # Initialize TMDBService with TMDB_API_KEY from env
    # Call search_film(title, year) in both fr-FR and en-US
    # Deduplicate by tmdb_id
    # Return list of SearchResult (tmdb_id, title, original_title, release_date, overview, poster_url)
```

Schema for the response:
```python
class TMDBSearchResult(BaseModel):
    tmdb_id: int
    title: str
    original_title: str
    release_date: str | None
    overview: str | None
    poster_url: str | None
```

Before returning results, check which `tmdb_id`s already exist in the DB and mark them (so the frontend can show "already in database" on those candidates).

**2. `POST /api/add-film/enrich`** — Fetch TMDB details + run Claude enrichment

Takes a `tmdb_id`, runs the full pipeline:
```python
@router.post("/add-film/enrich")
async def enrich_film(tmdb_id: int = Body(...)):
    # 1. Check if film already exists in DB → 409 if so
    # 2. TMDBService.get_film_details(tmdb_id) → raw TMDB data
    # 3. TMDBService.get_film_details_fr(tmdb_id) → French data
    # 4. TMDBMapper.map_film_to_db(tmdb_data, fr_data) → mapped data
    # 5. TMDBService.get_watch_providers(tmdb_id) → streaming platforms
    # 6. TMDBMapper.map_watch_providers(providers) → platform names
    # 7. ClaudeEnricher.enrich_film(mapped_data) → enrichment dict
    # 8. Merge everything into a single preview payload and return it
```

This is the most complex endpoint — it's where all three services converge. It should:
- Return the full preview data: film core fields, titles, cast, crew, studios, enrichment (all taxonomy tags), streaming platforms, awards
- NOT save anything to the database yet — this is just a preview
- Handle errors gracefully: if Claude enrichment fails, return TMDB data with empty enrichment so the user can still add tags manually
- Include a `streaming_platforms` field from the TMDB watch/providers response

The response should match the structure expected by `POST /api/films` (the existing `FilmCreate` schema) so the frontend can send it directly to the save endpoint after the user reviews and edits.

**3. `POST /api/add-film/save`** — Save the enriched film to DB

This can simply delegate to the existing `POST /api/films` endpoint (or call the same logic internally). The frontend sends the (potentially user-edited) payload from step 2.

Alternatively, the existing `POST /api/films` endpoint may already be sufficient — the frontend can call it directly. Evaluate whether a separate `/add-film/save` endpoint adds value (e.g., for additional validation, or to set `vu = false` by default) or if reusing `POST /api/films` is cleaner.

### B. Backend: Service Initialization

The existing services (`TMDBService`, `TMDBMapper`, `ClaudeEnricher`) were designed for CLI script usage. They need to be usable from FastAPI request handlers:

- `TMDBService` needs `TMDB_API_KEY` from env — create a dependency or initialize in the router
- `ClaudeEnricher` needs `ANTHROPIC_API_KEY` from env — same pattern
- `TMDBMapper` takes a `TMDBService` instance

Consider a simple approach: instantiate them at module level in the router (reading from env), or create a lightweight dependency injection pattern. No need for a full DI framework — keep it simple.

**Important:** `TMDBService` uses `httpx.AsyncClient` which should be properly managed (not recreated per request). Either use `TMDBService` as a context manager in each request, or create a long-lived instance in the app lifespan.

### C. Backend: Schemas — `backend/app/schemas/add_film.py`

Create Pydantic schemas for the add-film endpoints:

```python
class TMDBSearchResult(BaseModel):
    tmdb_id: int
    title: str
    original_title: str
    release_date: str | None
    overview: str | None
    poster_url: str | None
    already_in_db: bool = False

class TMDBSearchResponse(BaseModel):
    results: list[TMDBSearchResult]

class EnrichRequest(BaseModel):
    tmdb_id: int

class EnrichmentPreview(BaseModel):
    """Full preview of what will be saved — matches FilmCreate structure."""
    film: dict              # Core film fields
    titles: list[dict]
    categories: list[str]
    historic_subcategories: list[str]
    crew: list[dict]        # With tmdb_id, firstname, lastname, role, photo_url
    cast: list[dict]        # With tmdb_id, firstname, lastname, character_name, cast_order, photo_url
    studios: list[dict]     # With name, country
    streaming_platforms: list[str]
    enrichment: dict        # All taxonomy classifications from Claude
    keywords: list[str]     # TMDB keywords (for reference)
    production_countries: list[str]
```

### D. Frontend: New Page — `frontend/src/pages/AddFilmPage.tsx`

A new page at route `/add` with a multi-step wizard. The page has three distinct states/steps:

**Step 1 — Search:**
- Search form: text input for title + optional year input
- "Search TMDB" button
- Results grid: poster thumbnails, title, year, overview snippet
- Each result is clickable (unless marked "already in database", in which case show a link to the existing detail page)
- Clicking a result triggers enrichment (step 2)

**Step 2 — Review & Edit:**
- Loading state while enrichment runs (can take 5-15 seconds due to Claude API call)
- Display a progress indicator: "Fetching from TMDB...", "Classifying with AI...", "Almost ready..."
- Once loaded, show a preview of the film in a layout similar to the detail page but in "edit mode":
  - Film poster + title + year + duration (read-only from TMDB)
  - Synopsis (editable textarea)
  - Cast & crew list (read-only, from TMDB — no need to edit these)
  - All taxonomy sections in edit mode by default (reuse `EditableTagSection` or similar pattern):
    - Categories, Cinema types, Cultural movements
    - Themes, Characters, Character contexts, Motivations, Atmospheres, Messages
    - Time periods, Place contexts, Geography
    - Studios, Source, Financials
  - Streaming platforms (editable list)
  - Awards (from Claude enrichment, editable)
- "Back to Search" button to go back to step 1
- **"Add to Database"** button to proceed to step 3

**Step 3 — Save & Redirect:**
- Send the (possibly edited) payload to `POST /api/films` (or `POST /api/add-film/save`)
- Show success message
- Redirect to the new film's detail page (`/films/{new_film_id}`)
- On error: show error message, stay on step 2 so the user can retry

### E. Frontend: Navigation — Add Button in Header

Add a "+" or "Add Film" button in the `Header` component that navigates to `/add`. Use a subtle but accessible placement (e.g., next to the search bar or in the right section alongside sort controls).

### F. Frontend: Route — `App.tsx`

Add the new route:
```tsx
<Route path="/add" element={<AddFilmPage />} />
```

### G. Frontend: API Client — `frontend/src/api/client.ts`

Add functions for the add-film workflow:
```typescript
export async function searchTMDB(title: string, year?: number): Promise<TMDBSearchResult[]>
export async function enrichFilm(tmdbId: number): Promise<EnrichmentPreview>
export async function saveFilm(data: EnrichmentPreview): Promise<{ film_id: number }>
```

### H. Frontend: Types — `frontend/src/types/api.ts`

Add interfaces:
```typescript
export interface TMDBSearchResult {
    tmdb_id: number;
    title: string;
    original_title: string;
    release_date: string | null;
    overview: string | null;
    poster_url: string | null;
    already_in_db: boolean;
}

export interface EnrichmentPreview {
    film: Record<string, any>;
    titles: Record<string, any>[];
    categories: string[];
    historic_subcategories: string[];
    crew: Record<string, any>[];
    cast: Record<string, any>[];
    studios: Record<string, any>[];
    streaming_platforms: string[];
    enrichment: Record<string, any>;
    keywords: string[];
    production_countries: string[];
}
```

### Implementation Order

1. Backend first: create `add_film.py` router with search + enrich + save endpoints, register in `main.py`
2. Backend schemas: `add_film.py` in schemas
3. Test backend manually: `GET /api/add-film/search?title=Inception`, then `POST /api/add-film/enrich` with the returned tmdb_id
4. Frontend: types + API client functions
5. Frontend: `AddFilmPage.tsx` with the 3-step wizard
6. Frontend: header button + route

### Important Technical Notes

1. **Claude API timeout:** The enrichment call can take 5-15 seconds. The FastAPI endpoint should have a generous timeout, and the frontend should show a clear loading state.

2. **Error handling for Claude:** If the Anthropic API key is missing or Claude fails, the enrich endpoint should still return the TMDB data with an empty enrichment dict and a flag indicating enrichment failed, so the user can manually tag the film.

3. **Duplicate prevention:** The search endpoint checks existing tmdb_ids. The enrich endpoint returns 409 if the film already exists. The save endpoint also has tmdb_id uniqueness check (already in `POST /api/films`).

4. **Service lifecycle:** `TMDBService` creates an `httpx.AsyncClient`. Either initialize it once in the app lifespan and store on `app.state`, or create/close it per request using `async with TMDBService(api_key) as tmdb:`.

5. **Streaming platforms:** The `get_watch_providers()` call uses country="FR" by default (matching the user's location). The `map_watch_providers()` method in `TMDBMapper` maps TMDB provider names to our `stream_platform` table names.

6. **Existing `POST /api/films`:** Already handles full film creation including all junctions. The `FilmCreate` schema accepts `film`, `titles`, `crew`, `cast`, `studios`, `enrichment`, `streaming_platforms`. The `EnrichmentPreview` from the enrich endpoint should be compatible with this schema.

7. **Person photo_url:** The `TMDBMapper._map_cast()` and `_map_crew()` methods already build full TMDB CDN URLs from `profile_path`. The person `tmdb_id` comes directly from the TMDB credits response — this is the correct ID (unlike the fallback JSON which had wrong IDs).

### Validation

After implementation:
1. Navigate to `/add` — search form displays
2. Type "Inception" → search returns TMDB candidates with posters
3. Click a result → loading state appears ("Classifying with AI...")
4. Preview loads: film info + all taxonomy tags from Claude
5. All taxonomy sections are editable (can remove/add tags)
6. Click "Add to Database" → film is saved
7. Redirect to new film's detail page → all data correct
8. Navigate to `/browse` → new film appears in the grid
9. Try adding same film again → "already in database" shown on search result
10. Try a French film title (e.g., "Les Quatre Cents Coups") → TMDB finds it via fr-FR locale
11. If Claude API is down/missing: enrich still returns TMDB data, user can tag manually
12. Mobile responsive: all steps usable on phone screen

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

### Backend
```bash
uvicorn backend.app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
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
