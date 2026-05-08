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

### Algorithm

**IDF-weighted Jaccard per dimension, summed across 9 dimensions, plus structural bonuses.**

For source film S and candidate C, per-dimension d:
- per_dim_score(d) = Σ_{t ∈ T_S^d ∩ T_C^d} idf(t) / Σ_{t ∈ T_S^d ∪ T_C^d} idf(t)
- total = Σ_d W_d × per_dim_score(d) + bonuses

**Initial dimension weights** (tunable):
atmospheres 1.4 · themes 1.3 · motivations 1.1 · messages 1.0 · cinema_types 1.0 · characters 0.9 · categories 0.7 · place_contexts 0.6 · time_periods 0.5

**Bonuses**:
- Same director (any overlap): +0.10
- Same studio + same release decade: +0.03
- Quality nudge: +0.05 × normalized weighted_score

---

## Step 16c Prompt — Recommender: SimilarFilmsCarousel UI

**Goal:** Replace the placeholder `SimilarFilmsCarousel` with the real recommendation UI driven by the 16b endpoint, with the "Refine in Browse →" button (16a) integrated into the section header.

---

## Step 17a-Backend Prompt — Stats Dashboard API

```
Read CLAUDE.md, then PLAN.md (Step 17a section, paying special attention to the Tier visibility model and Response shape JSON), then this prompt.

Read these files for context before changing anything:
- backend/app/routers/films.py (especially the existing get_stats() at the bottom and the parallel-query pattern used in get_film())
- backend/app/auth.py (for get_current_user, UserInfo)
- backend/app/tier_config.py
- backend/app/main.py (router registration pattern)
- database/schema.sql (skim person, crew, casting, award, source, film_origin, film_genre, category, theme_context, atmosphere, user_film_status)

## Task: Build a single bulk dashboard stats endpoint with tier-aware payload

### 1. Create `backend/app/routers/stats.py`

New router with one endpoint:

`GET /api/stats/dashboard` — returns the full dashboard payload, with locked sections returned as `null`.

**Tier resolution:**
- Use `Depends(get_current_user)` to get optional `UserInfo`
- Resolve tier: `user.tier if user else "anonymous"`
- Decide which sections to populate:
  - `quick`: always (but `seen_count` = 0 for anonymous; pulled from user_film_status for logged-in users)
  - `geography`: ALWAYS `null` in 17a (placeholder)
  - `financials`: `null` for anonymous, populated for free/pro/admin
  - `people`: `null` for anonymous and free, populated for pro/admin
  - `taxonomy`: `null` for anonymous and free, populated for pro/admin
  - `personal_stats`: populated only for logged-in pro/admin

### 2. Implementation pattern

Follow the parallel-query pattern from `get_film()` in films.py. Define an internal `_parallel_query(sql, params)` helper that uses `engine.connect()` and a semaphore. Build a list of coroutines, gather only the ones needed for the resolved tier, then assemble the response dict.

Do NOT run queries for sections the user can't access — saves significant DB load.

### 3. Exact SQL for each block

**quick.total_films:**
```sql
SELECT COUNT(*) FROM film
```

**quick.total_directors / total_actors / total_composers:**
```sql
-- Directors and Composers via crew
SELECT pj.role_name, COUNT(DISTINCT c.person_id) AS cnt
FROM crew c JOIN person_job pj ON c.job_id = pj.job_id
WHERE pj.role_name IN ('Director', 'Composer')
GROUP BY pj.role_name

-- Actors via casting
SELECT COUNT(DISTINCT person_id) FROM casting
```

**quick.by_decade:**
```sql
SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
       COUNT(*) AS count
FROM film WHERE first_release_date IS NOT NULL
GROUP BY decade ORDER BY decade
```

**quick.duration_distribution:**
```sql
SELECT bucket, COUNT(*) AS count FROM (
  SELECT CASE
    WHEN duration < 60 THEN '<60'
    WHEN duration < 90 THEN '60-89'
    WHEN duration < 120 THEN '90-119'
    WHEN duration < 150 THEN '120-149'
    WHEN duration < 180 THEN '150-179'
    ELSE '180+'
  END AS bucket
  FROM film WHERE duration IS NOT NULL
) sub GROUP BY bucket
```
Return buckets in fixed order client-side; backend can return any order, frontend will reshape.

**quick.color_by_decade:**
```sql
SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
       COUNT(*) FILTER (WHERE color = TRUE) AS color,
       COUNT(*) FILTER (WHERE color = FALSE) AS bw
FROM film WHERE first_release_date IS NOT NULL
GROUP BY decade ORDER BY decade
```

**quick.top_studios** (top 20):
```sql
SELECT s.studio_name AS name, COUNT(*) AS count
FROM production p JOIN studio s ON p.studio_id = s.studio_id
GROUP BY s.studio_name ORDER BY count DESC LIMIT 20
```

**quick.most_awarded_films** (top 20):
```sql
SELECT f.film_id, f.original_title AS title, f.poster_url,
       EXTRACT(YEAR FROM f.first_release_date)::int AS year,
       COUNT(*) FILTER (WHERE a.result='won') AS wins,
       COUNT(*) FILTER (WHERE a.result='nominated') AS nominations
FROM award a JOIN film f ON a.film_id = f.film_id
GROUP BY f.film_id, f.original_title, f.poster_url, f.first_release_date
ORDER BY wins DESC, nominations DESC LIMIT 20
```

**quick.by_source_type:**
```sql
SELECT s.source_type, COUNT(DISTINCT fo.film_id) AS count
FROM film_origin fo JOIN source s ON fo.source_id = s.source_id
GROUP BY s.source_type ORDER BY count DESC
```

**financials.top_grossing** (top 20):
```sql
SELECT film_id, original_title AS title, poster_url,
       EXTRACT(YEAR FROM first_release_date)::int AS year, revenue
FROM film WHERE revenue IS NOT NULL AND revenue > 0
ORDER BY revenue DESC LIMIT 20
```

**financials.top_budgets** (same pattern, ORDER BY budget DESC, WHERE budget IS NOT NULL AND budget > 0).

**financials.most_profitable** (top 20):
```sql
SELECT film_id, original_title AS title, poster_url,
       EXTRACT(YEAR FROM first_release_date)::int AS year,
       budget, revenue,
       (revenue::float / budget) AS ratio
FROM film
WHERE budget IS NOT NULL AND budget > 1000000
  AND revenue IS NOT NULL AND revenue > 0
ORDER BY ratio DESC LIMIT 20
```

**financials.avg_budget_by_decade:**
```sql
SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
       AVG(budget)::bigint AS avg_budget,
       COUNT(*) AS film_count
FROM film
WHERE budget IS NOT NULL AND budget > 0 AND first_release_date IS NOT NULL
GROUP BY decade HAVING COUNT(*) >= 3
ORDER BY decade
```

**financials.budget_revenue_scatter** (capped at 500):
```sql
SELECT f.film_id, f.original_title AS title, f.budget, f.revenue,
       (SELECT MIN(c.category_name) FROM film_genre fg
        JOIN category c ON fg.category_id = c.category_id
        WHERE fg.film_id = f.film_id
          AND c.historic_subcategory_name IS NULL) AS category
FROM film f
WHERE f.budget IS NOT NULL AND f.budget > 0
  AND f.revenue IS NOT NULL AND f.revenue > 0
ORDER BY f.revenue DESC LIMIT 500
```

**people.top_directors** (top 15):
```sql
SELECT p.person_id,
       TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
       p.photo_url, p.nationality,
       COUNT(*) AS film_count,
       MIN(EXTRACT(YEAR FROM f.first_release_date)::int) AS first_year,
       MAX(EXTRACT(YEAR FROM f.first_release_date)::int) AS last_year
FROM crew c
JOIN person p ON c.person_id = p.person_id
JOIN person_job pj ON c.job_id = pj.job_id
JOIN film f ON c.film_id = f.film_id
WHERE pj.role_name = 'Director' AND f.first_release_date IS NOT NULL
GROUP BY p.person_id, p.firstname, p.lastname, p.photo_url, p.nationality
ORDER BY film_count DESC, last_year DESC LIMIT 15
```

**people.top_actors** (top 15) — same pattern via casting:
```sql
SELECT p.person_id,
       TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
       p.photo_url, p.nationality,
       COUNT(*) AS film_count,
       MIN(EXTRACT(YEAR FROM f.first_release_date)::int) AS first_year,
       MAX(EXTRACT(YEAR FROM f.first_release_date)::int) AS last_year
FROM casting ca
JOIN person p ON ca.person_id = p.person_id
JOIN film f ON ca.film_id = f.film_id
WHERE f.first_release_date IS NOT NULL
GROUP BY p.person_id, p.firstname, p.lastname, p.photo_url, p.nationality
ORDER BY film_count DESC LIMIT 15
```

**people.top_composers** (top 15) — same as top_directors with `role_name = 'Composer'`.

**people.top_director_nationalities** (top 15):
```sql
SELECT p.nationality, COUNT(DISTINCT p.person_id) AS count
FROM crew c
JOIN person p ON c.person_id = p.person_id
JOIN person_job pj ON c.job_id = pj.job_id
WHERE pj.role_name = 'Director' AND p.nationality IS NOT NULL
GROUP BY p.nationality ORDER BY count DESC LIMIT 15
```

**people.top_actor_nationalities** — same via casting.

**people.gender_split** — three queries grouped (all persons / directors / actors):
```sql
-- All persons
SELECT COALESCE(gender, 'unknown') AS g, COUNT(*) AS c
FROM person GROUP BY COALESCE(gender, 'unknown')
```
For directors: filter via crew + 'Director' role. For actors: via casting.

Reshape into `{"M": int, "F": int, "unknown": int}` in Python before returning.

**people.directors_gender_by_decade:**
```sql
SELECT (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
       COUNT(*) FILTER (WHERE p.gender = 'M') AS male,
       COUNT(*) FILTER (WHERE p.gender = 'F') AS female
FROM crew c
JOIN person p ON c.person_id = p.person_id
JOIN person_job pj ON c.job_id = pj.job_id
JOIN film f ON c.film_id = f.film_id
WHERE pj.role_name = 'Director' AND f.first_release_date IS NOT NULL
GROUP BY decade ORDER BY decade
```
Return keys as `{"decade": ..., "M": ..., "F": ...}`.

**people.living_status** (directors / actors): for each person involved as director (or actor), count `living` (date_of_death IS NULL AND date_of_birth IS NOT NULL), `deceased` (date_of_death IS NOT NULL), `unknown` (date_of_birth IS NULL).

**people.directors_by_birth_decade:**
```sql
SELECT (EXTRACT(YEAR FROM p.date_of_birth)::int / 10) * 10 AS birth_decade,
       COUNT(DISTINCT p.person_id) AS count
FROM crew c
JOIN person p ON c.person_id = p.person_id
JOIN person_job pj ON c.job_id = pj.job_id
WHERE pj.role_name = 'Director' AND p.date_of_birth IS NOT NULL
GROUP BY birth_decade ORDER BY birth_decade
```

**taxonomy.top_themes** (top 20, exclude subtypes):
```sql
SELECT tc.theme_name AS name, COUNT(*) AS count
FROM film_theme ft JOIN theme_context tc ON ft.theme_context_id = tc.theme_context_id
WHERE tc.theme_name NOT LIKE '%: %'  -- exclude "parent: sub" subtypes
GROUP BY tc.theme_name ORDER BY count DESC LIMIT 20
```

**taxonomy.category_distribution:**
```sql
SELECT c.category_name AS name, COUNT(*) AS count
FROM film_genre fg JOIN category c ON fg.category_id = c.category_id
WHERE c.historic_subcategory_name IS NULL
GROUP BY c.category_name ORDER BY count DESC
```

**taxonomy.top_atmospheres** (top 30 for word cloud):
```sql
SELECT a.atmosphere_name AS name, COUNT(*) AS count
FROM film_atmosphere fa JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id
GROUP BY a.atmosphere_name ORDER BY count DESC LIMIT 30
```

**taxonomy.category_by_decade_heatmap:**
```sql
SELECT c.category_name AS category,
       (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
       COUNT(*) AS count
FROM film_genre fg
JOIN category c ON fg.category_id = c.category_id
JOIN film f ON fg.film_id = f.film_id
WHERE c.historic_subcategory_name IS NULL
  AND f.first_release_date IS NOT NULL
GROUP BY c.category_name, decade
ORDER BY c.category_name, decade
```

**personal_stats** (logged-in pro/admin only):
- `seen_count` = `SELECT COUNT(*) FROM user_film_status WHERE user_id=:uid AND seen=TRUE`
- `unseen_count` = `total_films - seen_count`
- `seen_pct` = `round(seen_count / total_films * 100, 1)`
- `favorite_count`, `watchlist_count`, `rated_count` = similar counts with the matching flags
- `avg_rating` = `SELECT AVG(rating) FROM user_film_status WHERE user_id=:uid AND rating IS NOT NULL`
- `seen_by_decade`:
  ```sql
  SELECT (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
         COUNT(*) AS count
  FROM user_film_status u JOIN film f ON u.film_id = f.film_id
  WHERE u.user_id = :uid AND u.seen = TRUE AND f.first_release_date IS NOT NULL
  GROUP BY decade ORDER BY decade
  ```
- `top_seen_categories`: same join, GROUP BY category, top 10

### 4. Pydantic schemas

Define response models in the same file (or a new `backend/app/schemas/stats.py` if you prefer). Use Optional types for the section fields so they can be `null`.

### 5. Register router

In `backend/app/main.py`, add:
```python
from backend.app.routers import stats
app.include_router(stats.router, prefix="/api")
```

### 6. Decision on existing /api/stats

The existing minimal `/api/stats` endpoint in `films.py` (returns total_films, seen, unseen, by_decade, top_categories, top_countries) is now redundant. **Keep it for backward compatibility for now** — don't delete. The new `/api/stats/dashboard` is the dashboard endpoint; the old one stays as-is.

### 7. Verification

Test manually with curl:
```bash
# Anonymous
curl http://localhost:8000/api/stats/dashboard | jq '.tier, .quick.total_films, .financials, .people, .taxonomy'
# Expect: "anonymous", <number>, null, null, null

# Logged in (use a test JWT with tier=pro)
curl -H "Authorization: Bearer <jwt>" http://localhost:8000/api/stats/dashboard | jq '.tier, .people.top_directors[0]'
```

Response for anonymous should be reasonably fast (<500ms locally). For pro, all sections populated, target <1.5s. Use parallel queries.
```

---

## Step 17a-Frontend Prompt — Stats Dashboard UI

```
Read CLAUDE.md, then PLAN.md (Step 17a section, especially the Tier visibility model), then this prompt.

Read these files for context before changing anything:
- frontend/src/App.tsx (route registration)
- frontend/src/components/layout/Header.tsx (nav links)
- frontend/src/api/client.ts (API call patterns, getAuthHeaders, BASE)
- frontend/src/types/api.ts
- frontend/src/context/AuthContext.tsx (useAuth hook, isAuthenticated, tier)
- frontend/src/lib/tierAccess.ts (existing tier patterns to mirror)
- frontend/src/pages/CollectionPage.tsx (existing page example with same dark theme)
- frontend/src/components/films/FilmCard.tsx (poster card pattern for top-grossing/awarded film cards)

## Task: Build the /stats dashboard page with 5 tabs (Quick / Geography / Financials / People / Taxonomy)

### 0. Install dependency

```bash
cd frontend
npm install recharts
```

### 1. Add types in `frontend/src/types/api.ts`

Add at the bottom of the file:

```typescript
export type Tier = "anonymous" | "free" | "pro" | "admin";

export interface QuickStatsPayload {
  total_films: number;
  total_directors: number;
  total_actors: number;
  total_composers: number;
  by_decade: { decade: number; count: number }[];
  duration_distribution: { bucket: string; count: number }[];
  color_by_decade: { decade: number; color: number; bw: number }[];
  top_studios: { name: string; count: number }[];
  most_awarded_films: { film_id: number; title: string; poster_url: string | null; year: number | null; wins: number; nominations: number }[];
  by_source_type: { source_type: string; count: number }[];
}

export interface FinancialsPayload {
  top_grossing: { film_id: number; title: string; poster_url: string | null; year: number | null; revenue: number }[];
  top_budgets: { film_id: number; title: string; poster_url: string | null; year: number | null; budget: number }[];
  most_profitable: { film_id: number; title: string; poster_url: string | null; year: number | null; budget: number; revenue: number; ratio: number }[];
  avg_budget_by_decade: { decade: number; avg_budget: number; film_count: number }[];
  budget_revenue_scatter: { film_id: number; title: string; budget: number; revenue: number; category: string | null }[];
}

export interface PeoplePayload {
  top_directors: PersonRank[];
  top_actors: PersonRank[];
  top_composers: PersonRank[];
  top_director_nationalities: { nationality: string; count: number }[];
  top_actor_nationalities: { nationality: string; count: number }[];
  gender_split: { all: GenderCounts; directors: GenderCounts; actors: GenderCounts };
  directors_gender_by_decade: { decade: number; M: number; F: number }[];
  living_status: { directors: LivingCounts; actors: LivingCounts };
  directors_by_birth_decade: { birth_decade: number; count: number }[];
}

export interface PersonRank {
  person_id: number;
  name: string;
  photo_url: string | null;
  nationality: string | null;
  film_count: number;
  first_year: number | null;
  last_year: number | null;
}
export interface GenderCounts { M: number; F: number; unknown: number }
export interface LivingCounts { living: number; deceased: number; unknown: number }

export interface TaxonomyPayload {
  top_themes: { name: string; count: number }[];
  category_distribution: { name: string; count: number }[];
  top_atmospheres: { name: string; count: number }[];
  category_by_decade_heatmap: { category: string; decade: number; count: number }[];
}

export interface PersonalStatsPayload {
  seen_count: number;
  unseen_count: number;
  seen_pct: number;
  favorite_count: number;
  watchlist_count: number;
  rated_count: number;
  avg_rating: number | null;
  seen_by_decade: { decade: number; count: number }[];
  top_seen_categories: { name: string; count: number }[];
}

export interface DashboardStats {
  tier: Tier;
  quick: QuickStatsPayload;
  geography: null;  // always null in 17a
  financials: FinancialsPayload | null;
  people: PeoplePayload | null;
  taxonomy: TaxonomyPayload | null;
  personal_stats: PersonalStatsPayload | null;
}
```

### 2. Add API call in `frontend/src/api/client.ts`

```typescript
export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${BASE}/stats/dashboard`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to load dashboard");
  return res.json();
}
```

### 3. Create `frontend/src/hooks/useDashboardStats.ts`

React Query wrapper with `staleTime: 5 * 60 * 1000` (5 minutes). Pattern: same as existing `useFilms.ts`.

### 4. Create `frontend/src/lib/nationalityFlags.ts`

Export a function `getNationalityFlag(nationality: string | null): string`. Static map of ~50 most common nationalities (English/American/French/German/Italian/Spanish/Japanese/Korean/Chinese/Indian/Russian/Brazilian/Mexican/Canadian/Australian/Swedish/Danish/Norwegian/Finnish/Dutch/Belgian/Polish/Czech/Hungarian/Greek/Turkish/Iranian/Israeli/Egyptian/South African/Argentine/Chilean/Cuban/Vietnamese/Thai/Indonesian/Filipino/Hong Kong/Taiwanese/Pakistani/Bangladeshi/Irish/Scottish/Welsh/Portuguese/Austrian/Swiss/Romanian/Bulgarian/Ukrainian/etc.) → emoji flag. Return empty string if not found. Be careful: nationality strings come from TMDB and are typically the demonym ("French") not the country ("France").

### 5. Create reusable components in `frontend/src/components/stats/`

**StatCard.tsx**: simple card with big number + label + optional sublabel. Props: `value: number | string`, `label: string`, `sublabel?: string`. Format large numbers with commas (use `toLocaleString()`).

**LockedTabPlaceholder.tsx**: shown for locked tabs. Props:
  - `reason: "signup" | "upgrade" | "coming_soon"`
  - `tabName: string` (e.g. "People")
  - For "signup": message "Sign up free to unlock {tabName}" + button to `/auth?mode=signup`
  - For "upgrade": message "Upgrade to Pro to unlock {tabName}" + button (no real upgrade flow yet, just disable or link to a placeholder)
  - For "coming_soon": message "Geography stats coming soon" + Lock icon, no CTA button
  - Use Lock icon from lucide-react, amber accent

**PersonRankCard.tsx**: compact card for People tab.
  - Props: `person: PersonRank, role: "Director" | "Actor" | "Composer"`
  - Photo (square, 80x80), name, flag emoji + nationality, film count, active years ("1943–1993")
  - Whole card is clickable → navigate to `/browse?q=<encoded name>` (using react-router's `Link` or `useNavigate`)
  - Fallback for missing photo: initials in a circle (firstname[0] + lastname[0])

**CategoryDecadeHeatmap.tsx**: custom SVG heatmap.
  - Props: `data: { category: string; decade: number; count: number }[]`
  - Compute: unique sorted categories (rows), unique sorted decades (columns), max count for color scaling
  - Render `<svg>` with one `<rect>` per cell. Color: amber with opacity = `count / maxCount` (clamped to 0.05–1.0 for visibility)
  - Cell size: 40×40 px. Show count as text inside cell when count > 0
  - Row labels (categories) on the left, column labels (decades) at the bottom rotated -45deg
  - On cell hover: tooltip with "{category} · {decade}s · {count} films"

**AtmosphereWordCloud.tsx**: simple sized-text cloud, NO library.
  - Props: `data: { name: string; count: number }[]`
  - Compute min/max counts. Map count → font size between 0.75rem and 2.5rem (linear)
  - Render as flex-wrap div, gap between words. Random soft color rotation between amber/slate/zinc shades
  - No clicks needed

### 6. Create the 5 tab components

**QuickStatsTab.tsx** (`data: QuickStatsPayload, personalStats: PersonalStatsPayload | null`):
Sections in this order:
  1. Top row: 4 StatCards (total films, directors, actors, composers)
  2. (If personalStats present:) personal-stats row — 4 StatCards (seen %, favorites, watchlist, rated)
  3. "Films by decade" — Recharts BarChart. If `personalStats.seen_by_decade` present, render a stacked bar (seen + remaining). Otherwise plain bar.
  4. "Duration distribution" — Recharts BarChart. Order buckets manually: `["<60", "60-89", "90-119", "120-149", "150-179", "180+"]`
  5. "Color vs B&W over time" — Recharts BarChart with stacked bars (color amber, bw slate)
  6. "Most awarded films" — horizontal scrollable row of poster cards (similar to SimilarFilmsCarousel pattern). Each card shows poster + title + year + "{wins}× won, {nominations}× nominated". Click → navigate to film detail.
  7. "Top studios" — Recharts BarChart (horizontal, top 20)
  8. "By source type" — Recharts PieChart

**GeographyTab.tsx**: just renders `<LockedTabPlaceholder reason="coming_soon" tabName="Geography" />`.

**FinancialsTab.tsx** (`data: FinancialsPayload`):
  1. Disclaimer at top: italic "Based on N films with available financial data — not adjusted for inflation"
  2. Two side-by-side horizontal scroll rows: "Top 20 highest-grossing" / "Top 20 biggest budgets" (poster cards)
  3. "Most profitable (revenue/budget ratio)" — horizontal poster row, show ratio under title ("×{ratio.toFixed(1)}")
  4. "Average budget by decade" — Recharts LineChart. Y-axis in millions ($M). Tooltip shows film_count.
  5. "Budget vs Revenue scatter" — Recharts ScatterChart. X = budget (log scale), Y = revenue (log scale). Each dot a film. Add reference line `y = 2x` (rough break-even). Tooltip: title + figures.

**PeopleTab.tsx** (`data: PeoplePayload`):
  1. Three sections side-by-side or stacked: "Most prolific directors" / "Most prolific actors" / "Most prolific composers". Each = grid of 5 PersonRankCard × 3 rows = 15 cards.
  2. "Director nationalities" / "Actor nationalities" — two horizontal BarCharts side-by-side
  3. "Gender split" — three small PieCharts side-by-side (all / directors / actors). Use blue for M, pink for F, gray for unknown.
  4. "Female directors over time" — BarChart of `directors_gender_by_decade`, stacked M+F. The visual story = how the F bar grows over recent decades.
  5. "Living vs deceased" — two PieCharts side-by-side (directors / actors)
  6. "Directors by birth decade" — BarChart

**TaxonomyTab.tsx** (`data: TaxonomyPayload`):
  1. "Top 20 themes" — horizontal BarChart
  2. "Categories distribution" — PieChart
  3. "Atmospheres" — AtmosphereWordCloud
  4. "Category evolution over time" — CategoryDecadeHeatmap (with subtitle explaining the pattern)

### 7. Create `frontend/src/pages/StatsPage.tsx`

- Use `useDashboardStats()` hook
- Use `useSearchParams` from react-router-dom to read/write `?tab=`
- Use shadcn/ui `Tabs` component (`Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`)
- Tabs: "Quick Stats" / "Geography" / "Financials" / "People" / "Taxonomy"
- Tier-based rendering inside each tab:
  - For each tab, check if `data.<section>` is `null` and the tier requires unlock → render `LockedTabPlaceholder` instead of the actual tab component
  - Quick: always render (always populated)
  - Geography: always render `<GeographyTab />` (which is itself the locked placeholder)
  - Financials: if anonymous → LockedTabPlaceholder reason="signup"; else render <FinancialsTab data={data.financials!} />
  - People: if anonymous or free → LockedTabPlaceholder (signup or upgrade); else render <PeopleTab>
  - Taxonomy: same logic as People

Page layout: Layout wrapper, page title "Database Stats", subtitle showing total film count, then the Tabs.

Loading state: skeleton loaders or simple "Loading…" text matching existing pages.
Error state: error message in existing page style.

### 8. Add route in `frontend/src/App.tsx`

Add `<Route path="/stats" element={<StatsPage />} />` next to the other routes.

### 9. Add nav link in `frontend/src/components/layout/Header.tsx`

Add a "Stats" link in the main nav bar, visible to everyone. Use `BarChart3` icon from lucide-react. Active styling when current path = `/stats`.

### Important notes

- All charts should match dark theme: tooltip background `#1f1f1f`, chart text muted, primary color amber (`#f59e0b`), secondary slate (`#64748b`).
- Recharts components need explicit `width` and `height` or wrap in `<ResponsiveContainer width="100%" height={300}>`.
- Format large numbers consistently: `1840000` → `"$1.84M"`, `12000` → `"12,000"`. Use a helper in `lib/utils.ts` if not already present.
- Don't break any existing page or feature.
- Mobile responsiveness: charts inside ResponsiveContainer; stat card grids use Tailwind `grid grid-cols-2 md:grid-cols-4`.
- Performance: the dashboard query is cached 5 minutes by React Query, so navigating between tabs is instant.
```

---

