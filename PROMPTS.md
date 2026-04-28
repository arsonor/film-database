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

## Step 8 Prompt — Add Film Workflow ✅ DONE

*(see git history for original prompt)*

### Step 8 Summary
- Backend: `add_film.py` router with GET `/add-film/search` and POST `/add-film/enrich` (graceful failure with enrichment_failed flag). Registered in main.py.
- Backend: `schemas/add_film.py` with TMDBSearchResult, TMDBSearchResponse, EnrichRequest, EnrichmentPreview
- Frontend: `AddFilmPage.tsx` 3-step wizard (Search → Enrich → Review → Save → redirect)
- Frontend: Header "+" button, `/add` route, searchTMDB/enrichFilm/saveFilm in api/client.ts
- Enrichment quality: rewritten system prompt, new taxonomy values (migration 007), underscore renames (migration 008)
- Fixed Mulholland Drive reference example (missing comma)

---

## Step 8.5 Prompt — Auto-link Franchise Sequels via TMDB Collection ✅ DONE

*(see git history for original prompt)*

### Step 8.5 Summary
- Migration 009: `tmdb_collection_id` column on film table + index
- `tmdb_service.py`: captures `belongs_to_collection` from TMDB response
- `tmdb_mapper.py`: extracts `tmdb_collection_id` into film dict
- `films.py` create endpoint: stores collection_id + auto-links siblings via `film_sequel`
- `schema.sql`: updated for fresh installs
- New scripts: `backfill_collection_ids.py` (backfill existing films + auto-link), `refresh_streaming.py` (refresh streaming platforms from TMDB with unmapped provider reporting)

---

## Step 8.6 Prompt — Editable Categories, Financials, Awards + Person Data ✅ DONE

*(see git history for original prompt)*

### Step 8.6 Summary
- Frontend: `EditableFinancials.tsx` (new), editable `AwardsTable` (won/nominated toggle + X remove), `EditableTagSection` for categories in Classification section
- Backend: `awards: list[dict] | None` added to `FilmUpdate`, clear-and-reinsert in `update_film()`, gender column added to `_find_or_create_person()` INSERT + COALESCE
- Pipeline: `tmdb_mapper.py` now passes `gender` via `TMDB_GENDER_MAP` in both `_map_cast()` and `_map_crew()` output dicts
- New script: `backfill_person_details.py` (fetches `/person/{tmdb_id}` for all persons missing data, updates gender + date_of_birth + date_of_death + nationality)

---

## Step 9 — Bulk Ingestion (~2500 films)

No Claude Code prompt needed — this step uses the existing scripts built in steps 2-3. See PLAN.md for the full 4-stage procedure.

---

## Step 10 / 10.5 / 10.6 — UX Improvements, Taxonomy Admin, Delete Film ✅ DONE

*(see git history for original prompts)*

---

## Step 11 Prompt — Deployment + Admin Auth ✅ DONE

*(see git history for original prompts)*

### Step 11 Summary
- Backend: `auth.py` with `require_admin` dependency (bearer token vs `ADMIN_SECRET_KEY`, dev fallback), CORS from env, `/api/auth/login` + `/api/auth/check` endpoints, `Depends(require_admin)` on all POST/PUT/PATCH/DELETE endpoints
- Frontend: `AuthContext.tsx` (localStorage token, validate on mount via `/api/auth/check`), `LoginPage.tsx` (dark theme, password field, redirect on success)
- Frontend: `client.ts` gains `getAuthHeaders()` + `VITE_API_URL` env support, all write calls include auth headers
- Frontend: admin-only gating in Header (Add Film, Tags, Login/Logout buttons), BrowsePage (vu toggle), FilmDetailPage (edit controls, delete, seen toggle), TaxonomyAdminPage + AddFilmPage (redirect if !isAdmin)
- Deployment: `Procfile` for Render, Supabase for DB, Vercel for frontend CDN

---

## Step 12: Taxonomy restructure — merge dimensions, add sort_order grouping, rebalance tags

*(see git history for original prompts)*

---

## Step 13 Prompt — Performance Optimization (Deployed)

*(see git history for original prompts)*

---

## Step 14: Advanced 'click on tag' behaviour

No particular prompt

---

## Step 15a Prompt — Supabase Auth + User Roles + vu Migration

*(see git history for original prompts)*

---

## Step 15b Prompt — Personal Tracking UI + My Collection + Nav Menu

*(see git history for original prompts)*

---

## Step 15c Prompt — Tier-Gated Taxonomy Access

*(see git history for original prompts)*

---

## Step 16a Prompt — Recommender: "Refine in Browse" Button

Step 16a Summary
Backend: GET /api/taxonomy/tag-frequencies (24h cache, mutation-invalidated) — kept for use by future 16b/16c logic.
Frontend: "Refine in Browse →" button in Similar Films section header. Pro/Admin only. Click loads all tags from the current film into /browse in OR mode (per-dimension), letting the user manually deselect/AND-toggle from a complete starting state. Smart-selection approach (selectDistinctiveTags) was prototyped and discarded — applying all tags in OR mode tested better in practice because the user is already the best judge of which tags matter for that specific film.

---

## Step 16b Prompt — Recommender: Similar Films Algorithm (In-DB)

**Goal:** New endpoint `GET /api/films/{id}/similar?limit=N` returning the top-N most similar films using IDF-weighted Jaccard across 9 taxonomy dimensions plus structural bonuses.

One thing worth flagging:
cachetools is referenced in the 16b prompt — verify it's already in backend/requirements.txt. If not, that dependency add should be part of 16b. Standard library functools.lru_cache doesn't support TTL so we genuinely need it.

### Read first

- PLAN.md "Step 16: Recommender Engine" for the formula and weights
- `backend/app/routers/films.py` for SQL patterns (especially the parallel-query approach in `get_film`)
- `backend/app/database.py`
- `backend/app/auth.py` for `get_current_user`
- `backend/app/tier_config.py`
- `backend/app/schemas/film.py`

### Algorithm reference

Per source film S and each candidate C:
- For each dimension d in {atmospheres, themes, motivations, messages, cinema_types, characters, categories, place_contexts, time_periods}:
  - per_dim_score(d) = sum of idf(t) over shared tags / sum of idf(t) over union of tags
- total = Σ_d W_d × per_dim_score(d) + bonuses
- Bonuses: +0.10 (any director match), +0.03 (any studio match AND same release decade), +0.05 × normalized `weighted_score`
- Exclude: self, any film linked via `film_sequel` in either direction

Dimension weights: atmospheres 1.4, themes 1.3, motivations 1.1, messages 1.0, cinema_types 1.0, characters 0.9, categories 0.7, place_contexts 0.6, time_periods 0.5.

### Implementation

1. **New module** `backend/app/services/recommender.py`:
   - Constants block at the top of the file: `DIMENSION_WEIGHTS`, `BONUS_DIRECTOR`, `BONUS_STUDIO_DECADE`, `BONUS_QUALITY_MAX`, `IDF_CACHE_TTL_HOURS = 24`. Easy to tune in 16d.
   - `compute_idf_map(db) → dict[dim, dict[tag, float]]`: one query per dimension grouping by tag with COUNT(DISTINCT film_id). Total film count from a single COUNT query. idf(t) = `log(total_films / count(t))`.
   - `get_similar_films(db, film_id, limit) → list[SimilarFilm]`: orchestrates the SQL + post-processing for `shared_tags`.
   - `invalidate_film(film_id)` and `invalidate_idf()` exposed for cache busting from routers.

2. **Caching** (two layers):
   - **IDF map**: module-level dict, lazy-loaded on first request, refreshed every 24h via background asyncio task on app startup. Manually invalidatable.
   - **Per-film similarity results**: `cachetools.TTLCache(maxsize=2000, ttl=3600)` keyed by `(film_id, limit, tier)`. Tier in the key because result count varies by tier.

3. **SQL approach** — a single CTE-based query:
   - CTE 1: source film's tags per dimension (UNION ALL across the 9 junction tables → columns `dimension`, `tag_id`, `tag_name`).
   - CTE 2: candidate films' tag arrays per dimension (one row per (film_id, dimension) with array_agg of tags). Filter out self and `film_sequel` matches early.
   - Main SELECT: for each candidate, compute per-dimension scores using array intersection / union with the source's tags weighted by IDF. IDF can be passed in as a JSONB parameter (PostgreSQL handles JSONB fast) or joined from a temporary `tag_idf` table built from the cached IDF map.
   - Apply bonuses via LEFT JOINs (crew on shared director, production on shared studio + decade match).
   - ORDER BY score DESC LIMIT N.
   - Return film_id, original_title, first_release_date, duration, poster_url, director (concat), score, plus enough info to derive `shared_tags`.

   If the all-in-one CTE gets unwieldy: alternative is a 2-step approach — (1) get candidate IDs ranked by a coarser score in SQL, (2) re-fetch the top-N with full shared_tags in Python. Cleaner separation, only N=12 extra small queries.

4. **Endpoint** in `backend/app/routers/films.py`:
   ```
   @router.get("/films/{film_id}/similar", response_model=SimilarFilmsResponse)
   async def similar_films(
       film_id: int,
       limit: int = Query(12, ge=1, le=20),
       db: AsyncSession = Depends(get_db),
       user: UserInfo | None = Depends(get_current_user),
   ):
   ```
   - Tier-cap the requested `limit`: anonymous → min(limit, 3), free → min(limit, 6), pro/admin → limit.
   - 404 if film_id doesn't exist.

5. **Schemas** in `backend/app/schemas/film.py`:
   ```
   class SimilarFilm(BaseModel):
       film_id: int
       original_title: str
       first_release_date: date | None = None
       duration: int | None = None
       poster_url: str | None = None
       director: str | None = None
       categories: list[str] = []
       score: float
       score_pct: int  # 0–100, score normalized for UI display
       shared_tags: dict[str, list[str]]  # dim → top 3 shared tags

   class SimilarFilmsResponse(BaseModel):
       items: list[SimilarFilm]
   ```

6. **Cache invalidation hooks** — wire into existing endpoints:
   - `update_film` (PUT /films/{id}): call `recommender.invalidate_film(film_id)` after commit.
   - `add_film_relation` and `delete_film_relation`: invalidate both `film_id` and `related_film_id`.
   - `delete_film`: invalidate that film_id. Other entries naturally filter the deleted film via the JOIN.

### Performance target

First request for a film: ≤500ms uncached. Cached: ≤50ms. If the SQL is slow, profile with EXPLAIN ANALYZE — most likely missing or unused indexes on junction tables. The schema already has these per `schema.sql`; verify with the query plan.

### Acceptance

- `GET /api/films/{mulholland_drive_id}/similar` returns 12 films, all sharing some atmospheric/thematic DNA. Lynch films near top, neo-noir / dreamlike / mysterious titles present.
- `GET /api/films/{la_haine_id}/similar` surfaces social/political dramas with similar oppressive atmosphere.
- Sequel films excluded by construction (verify with a known franchise).
- Source film never present in its own results.
- Updating a film's tags via PUT → next call returns refreshed results (no stale cache).
- Adding a `film_sequel` relation → that film disappears from each other's similar list on next call.

---

## Step 16c Prompt — Recommender: SimilarFilmsCarousel UI

**Goal:** Replace the placeholder `SimilarFilmsCarousel` with the real recommendation UI driven by the 16b endpoint, with the "Refine in Browse →" button (16a) integrated into the section header.

### Read first

- `frontend/src/components/films/SimilarFilmsCarousel.tsx` (the placeholder being replaced)
- `frontend/src/components/films/FilmCard.tsx`
- `frontend/src/components/films/SectionHeading.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/types/api.ts`
- `frontend/src/pages/FilmDetailPage.tsx` (where the carousel is mounted)
- `frontend/src/lib/recommender.ts` (from 16a)

### Implementation

1. **Types** in `frontend/src/types/api.ts`: add `SimilarFilm` and `SimilarFilmsResponse` mirroring the backend schemas from 16b.

2. **API client** in `frontend/src/api/client.ts`: add `fetchSimilarFilms(filmId, limit)`.

3. **New hook** `frontend/src/hooks/useSimilarFilms.ts`:
   - React Query, staleTime 5min, only fetches when `filmId` is truthy.
   - Pass `limit` derived from tier (anonymous 3, free 6, pro/admin 12).

4. **Updated component** `SimilarFilmsCarousel.tsx`:
   - Props: `filmId: number`, `tier: "anonymous" | "free" | "pro" | "admin"`, `currentFilm: FilmDetail` (needed for the Refine button to read tags).
   - **Section header**: "Similar Films" on the left, **"Refine in Browse →"** button on the right (calls `selectDistinctiveTags(currentFilm, idfMap, tier)` from 16a, builds URLSearchParams, navigates).
   - **Body**: horizontal scroll container, FilmCard for each film. Scroll-snap on mobile. Cards show poster + title + year + (Pro only) a thin "match: 78%" indicator from `score_pct`.
   - **"Why?" tooltip** on each card (Pro/Admin only): hover shows top shared tags per dimension. Use shadcn/ui `Tooltip` if available; max width ~280px; dimensions as small headers, tags as inline chips.
   - **Tier teasing**: at tier limit, show a blurred 5th-position card with overlay "Sign up free for more" (anonymous) or "Upgrade to Pro for full recommendations" (free). Click → `/auth` or pricing.
   - **Loading**: skeleton cards (already partially in placeholder).
   - **Error**: tasteful inline message, do not break the page.
   - **Empty state**: if a film has too few tags to compute similarity (rare), fall back to the existing placeholder copy.

5. **Wire-up** in `FilmDetailPage.tsx`:
   - Pass `currentFilm={film}` and the user's `tier`.
   - Remove the temporary Refine button placement from 16a (the section header is the canonical home).
   - Keep the existing scroll-anchor `id="similar-films"` on the wrapping section.

### Visual polish

- No layout shift when the carousel resolves — reserve the height during loading.
- Score percentage uses subdued color (muted-foreground), not amber — it's secondary information.
- Tooltip dimension labels go through `dimensionLabel` from `lib/utils.ts` for consistency.

### Acceptance

- Mulholland Drive page: 12 films in carousel for Pro, 6 for free, 3 for anonymous.
- Hovering "Why?" on Pro shows top shared tags per dimension; tooltip absent on free/anonymous.
- Clicking "Refine in Browse →" navigates to /browse with 5–8 distinctive tags pre-selected (matches 16a acceptance).
- Direct sequels (visible in Related Films) do **not** appear in Similar Films.
- After admin adds a manual relation between two films, refreshing the page removes that film from each other's Similar Films section.

---
