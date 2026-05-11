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

## Step 17a-Stats Dashboard API & UI

*(see git history for original prompts)*
---

## Step 17c-Backend Prompt — Taxonomy stats enhancements

```
Read CLAUDE.md, then PLAN.md (Step 17c section, paying attention to the Backend changes payload shape), then this prompt.

Read these files for context before changing anything:
- backend/app/routers/stats.py (existing dashboard endpoint, parallel-query pattern, tier resolution)
- backend/app/tier_config.py
- backend/app/auth.py (UserInfo, get_current_user, tier check pattern)
- database/seed_taxonomy.sql (CINEMA_TYPE values + sort_orders, MESSAGE values + sort_orders)

## Task: Extend the Taxonomy section of the dashboard payload + add 2 new endpoints

### 1. Extend `taxonomy` block of `/api/stats/dashboard`

All new SQL queries follow the existing parallel-query pattern in `stats.py`. Add them only when tier is pro or admin (existing gating already handles this).

#### 1a. CHANGE `category_by_decade_heatmap` semantics from count to percentage

Replace the existing query. New SQL:

```sql
WITH decade_totals AS (
  SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
         COUNT(*) AS total
  FROM film
  WHERE first_release_date IS NOT NULL
  GROUP BY decade
),
category_decade AS (
  SELECT c.category_name AS category,
         (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
         COUNT(DISTINCT f.film_id) AS film_count
  FROM film_genre fg
  JOIN category c ON fg.category_id = c.category_id
  JOIN film f ON fg.film_id = f.film_id
  WHERE c.historic_subcategory_name IS NULL
    AND f.first_release_date IS NOT NULL
  GROUP BY c.category_name, decade
)
SELECT cd.category, cd.decade, cd.film_count,
       dt.total AS decade_total,
       ROUND((cd.film_count::numeric / dt.total) * 100, 2) AS pct
FROM category_decade cd
JOIN decade_totals dt ON cd.decade = dt.decade
WHERE dt.total >= 5
ORDER BY cd.category, cd.decade
```

Return rows shaped: `{category, decade, film_count, decade_total, pct}`.

#### 1b. NEW `cinema_movements_by_decade` (count-based, curated subset)

The curated movement set lives as a Python constant at the top of the file:

```python
CINEMA_MOVEMENT_NAMES = [
    'silent', 'expressionism', 'hollywood golden age', 'neo-realism', 'noir',
    'new wave', 'new hollywood', 'neo-noir', 'black and white',
    'blockbuster', 'art house', 'franchise',
]
```

SQL:

```sql
SELECT ct.technique_name AS movement,
       (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
       COUNT(DISTINCT f.film_id) AS count,
       ct.sort_order
FROM film_technique fte
JOIN cinema_type ct ON fte.cinema_type_id = ct.cinema_type_id
JOIN film f ON fte.film_id = f.film_id
WHERE ct.technique_name = ANY(:movement_names)
  AND f.first_release_date IS NOT NULL
GROUP BY ct.technique_name, decade, ct.sort_order
ORDER BY ct.sort_order, decade
```

Pass `:movement_names` = `CINEMA_MOVEMENT_NAMES`.

Return rows shaped: `{movement, decade, count, sort_order}`.

#### 1c. NEW `message_by_decade_heatmap` (% within decade)

SQL:

```sql
WITH decade_totals AS (
  SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
         COUNT(*) AS total
  FROM film
  WHERE first_release_date IS NOT NULL
  GROUP BY decade
  HAVING COUNT(*) >= 20
),
message_totals AS (
  SELECT mc.message_id, mc.message_name, mc.sort_order,
         COUNT(DISTINCT fm.film_id) AS total_count
  FROM message_conveyed mc
  LEFT JOIN film_message fm ON mc.message_id = fm.message_id
  GROUP BY mc.message_id, mc.message_name, mc.sort_order
  HAVING COUNT(DISTINCT fm.film_id) >= 5
),
message_decade AS (
  SELECT mc.message_name AS message,
         mc.sort_order,
         (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
         COUNT(DISTINCT f.film_id) AS film_count
  FROM film_message fm
  JOIN message_conveyed mc ON fm.message_id = mc.message_id
  JOIN film f ON fm.film_id = f.film_id
  WHERE f.first_release_date IS NOT NULL
    AND mc.message_id IN (SELECT message_id FROM message_totals)
  GROUP BY mc.message_name, mc.sort_order, decade
)
SELECT md.message, md.decade, md.film_count, dt.total AS decade_total,
       ROUND((md.film_count::numeric / dt.total) * 100, 2) AS pct,
       md.sort_order
FROM message_decade md
JOIN decade_totals dt ON md.decade = dt.decade
ORDER BY md.sort_order, md.decade
```

Return rows shaped: `{message, decade, film_count, decade_total, pct, sort_order}`.

#### 1d. NEW `atmosphere_by_category` (cross-tab, % within category)

SQL:

```sql
WITH category_totals AS (
  SELECT c.category_name AS category, COUNT(DISTINCT fg.film_id) AS total
  FROM film_genre fg
  JOIN category c ON fg.category_id = c.category_id
  WHERE c.historic_subcategory_name IS NULL
  GROUP BY c.category_name
),
ca AS (
  SELECT c.category_name AS category,
         a.atmosphere_name AS atmosphere,
         a.sort_order AS atmosphere_sort_order,
         COUNT(DISTINCT fg.film_id) AS film_count
  FROM film_genre fg
  JOIN category c ON fg.category_id = c.category_id
  JOIN film_atmosphere fa ON fg.film_id = fa.film_id
  JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id
  WHERE c.historic_subcategory_name IS NULL
  GROUP BY c.category_name, a.atmosphere_name, a.sort_order
)
SELECT ca.category, ca.atmosphere, ca.atmosphere_sort_order,
       ca.film_count, ct.total AS category_total,
       ROUND((ca.film_count::numeric / ct.total) * 100, 2) AS pct
FROM ca
JOIN category_totals ct ON ca.category = ct.category
ORDER BY ca.category, ca.atmosphere_sort_order
```

Return rows shaped: `{category, atmosphere, atmosphere_sort_order, film_count, category_total, pct}`.

### 2. NEW endpoint `GET /api/stats/person-tags`

Query params: `person_id: int` (required), `role: str` (one of `director`, `composer`, `actor`, default `director`).

Tier check: only pro/admin allowed. Return 403 otherwise.

Logic:
- Validate person exists. If not, return 404.
- Resolve film_id list:
  - For director / composer: `SELECT film_id FROM crew WHERE person_id = :pid AND job_id IN (SELECT job_id FROM person_job WHERE role_name = 'Director'|'Composer')`
  - For actor: `SELECT film_id FROM casting WHERE person_id = :pid`
- If 0 films, return `{person: {...}, top_themes: [], top_atmospheres: [], ...}` (empty lists).
- Otherwise run 4 small queries against the resolved film list:
  - top 8 themes (excluding `: ` subtypes)
  - top 5 atmospheres
  - top 5 character contexts
  - top 3 messages
- Return shape per `PersonTagsResponse` defined in PLAN.md.

Use a `WITH person_films AS (...)` CTE in each query to keep things readable.

### 3. NEW endpoint `GET /api/stats/people-with-films`

Query params: `role: str` (`director`/`composer`/`actor`, default `director`), `q: str | None` (optional name search).

Tier check: pro/admin only.

Return top 30 people in that role, with `film_count >= 3`, ordered by `film_count DESC`. If `q` provided, filter `WHERE name ILIKE '%q%'`.

SQL pattern (director shown):

```sql
SELECT p.person_id,
       TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
       COUNT(DISTINCT c.film_id) AS film_count
FROM crew c
JOIN person p ON c.person_id = p.person_id
JOIN person_job pj ON c.job_id = pj.job_id
WHERE pj.role_name = 'Director'
  AND (:q::text IS NULL OR (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE '%' || :q || '%')
GROUP BY p.person_id, p.firstname, p.lastname
HAVING COUNT(DISTINCT c.film_id) >= 3
ORDER BY film_count DESC, name
LIMIT 30
```

For actor: same pattern via `casting` (no role_name needed since casting is implicitly actors).

### 4. Pydantic schemas

Add new response models in `backend/app/routers/stats.py` (or extract to `backend/app/schemas/stats.py` if cleaner):

- Update `TaxonomyPayload` to add `cinema_movements_by_decade`, `message_by_decade_heatmap`, `atmosphere_by_category`. Update `category_by_decade_heatmap` shape (now has `film_count`, `decade_total`, `pct` instead of just `count`).
- New `PersonTagsResponse`, `PersonSearchResult`.

### 5. Verification

Manual test:
```bash
# Get pro JWT or use admin
curl -H "Authorization: Bearer <jwt>" http://localhost:8000/api/stats/dashboard | jq '.taxonomy.cinema_movements_by_decade[0:3], .taxonomy.message_by_decade_heatmap[0:3], .taxonomy.atmosphere_by_category[0:3]'

curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/api/stats/people-with-films?role=director&q=kuro" | jq '.'

curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/api/stats/person-tags?person_id=42&role=director" | jq '.'
```

Dashboard payload should still respond in <2s for pro tier despite the added queries (they're parallel).
```

---

## Step 17c-Frontend Prompt — Taxonomy stats enhancements UI

```
Read CLAUDE.md, then PLAN.md (Step 17c section), then this prompt.

Read these files for context before changing anything:
- frontend/src/components/stats/CategoryDecadeHeatmap.tsx (existing heatmap to generalize/rename)
- frontend/src/components/stats/TaxonomyTab.tsx (will receive 5 new sections)
- frontend/src/components/stats/Section.tsx (for consistent section wrapping)
- frontend/src/components/stats/PersonRankCard.tsx (reuse pattern for autocomplete result rendering if helpful)
- frontend/src/components/stats/chartTheme.ts
- frontend/src/types/api.ts (extend types)
- frontend/src/api/client.ts (add 2 new API functions)

## Task: Implement 5 taxonomy enhancements in the dashboard

### 1. Extend types in `frontend/src/types/api.ts`

Update `TaxonomyPayload`:

```typescript
export interface CategoryDecadeCell {
  category: string;
  decade: number;
  film_count: number;
  decade_total: number;
  pct: number;
}

export interface CinemaMovementCell {
  movement: string;
  decade: number;
  count: number;
  sort_order: number;
}

export interface MessageDecadeCell {
  message: string;
  decade: number;
  film_count: number;
  decade_total: number;
  pct: number;
  sort_order: number;
}

export interface AtmosphereByCategoryCell {
  category: string;
  atmosphere: string;
  atmosphere_sort_order: number;
  film_count: number;
  category_total: number;
  pct: number;
}

export interface TaxonomyPayload {
  top_themes: { name: string; count: number }[];
  category_distribution: { name: string; count: number }[];
  top_atmospheres: { name: string; count: number }[];
  category_by_decade_heatmap: CategoryDecadeCell[];     // shape changed
  cinema_movements_by_decade: CinemaMovementCell[];     // NEW
  message_by_decade_heatmap: MessageDecadeCell[];       // NEW
  atmosphere_by_category: AtmosphereByCategoryCell[];   // NEW
}

export interface PersonSearchResult {
  person_id: number;
  name: string;
  film_count: number;
}

export interface TagCount {
  name: string;
  count: number;
}

export interface PersonTagsResponse {
  person: { person_id: number; name: string; film_count: number };
  top_themes: TagCount[];
  top_atmospheres: TagCount[];
  top_characters: TagCount[];
  top_messages: TagCount[];
}
```

### 2. Add API functions in `frontend/src/api/client.ts`

```typescript
export async function searchPeopleWithFilms(
  role: "director" | "composer" | "actor",
  q: string,
): Promise<PersonSearchResult[]> {
  const params = new URLSearchParams({ role });
  if (q) params.set("q", q);
  const res = await fetch(`${BASE}/stats/people-with-films?${params}`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to search people");
  return res.json();
}

export async function getPersonTags(
  personId: number,
  role: "director" | "composer" | "actor",
): Promise<PersonTagsResponse> {
  const res = await fetch(
    `${BASE}/stats/person-tags?person_id=${personId}&role=${role}`,
    { headers: { ...getAuthHeaders() } },
  );
  if (!res.ok) throw new ApiError(res.status, "Failed to load person tags");
  return res.json();
}
```

### 3. Generalize `CategoryDecadeHeatmap.tsx` → rename to `DecadeHeatmap.tsx`

Generalize the existing component to support both count and percentage display, plus arbitrary row/decade dimensions.

New prop signature:
```typescript
interface DecadeHeatmapProps<T> {
  data: T[];
  rowKey: (cell: T) => string;        // e.g., (c) => c.category
  decadeKey: (cell: T) => number;     // e.g., (c) => c.decade
  valueKey: (cell: T) => number;      // numeric value used for color intensity (count or pct)
  cellLabel: (cell: T) => string;     // text shown inside cell, e.g., "12%" or "24"
  tooltip: (cell: T) => string;       // tooltip text
  rowSortOrder?: (cell: T) => number; // optional custom sort key for rows (else alphabetical)
  rowLabelWidth?: number;             // default 110, increase to 160 for long movement names
}
```

Keep the same SVG layout (40×40 cells, amber color scaling) but compute opacity from `valueKey`. The colour formula stays `0.05 + (value / maxValue) * 0.95` clamped.

When `rowSortOrder` is provided, sort rows by it. Otherwise sort alphabetically by `rowKey`.

Update the import in `TaxonomyTab.tsx` and any other usages.

### 4. Create `frontend/src/components/stats/AtmosphereCategoryHeatmap.tsx`

A separate dedicated component because the axis structure is different (categories are rows, atmospheres are cols, both labels are short). It's structurally similar to `DecadeHeatmap` but with atmosphere names as column labels (rotated -45deg, like decades) and percentages in cells.

Most atmosphere names are short ("feel good", "violent") so column width can be 50px. Cell shows "25%" if pct >= 1, blank if 0.

Hover tooltip: "Comedy · feel good · 25% (120 of 480 films)".

### 5. Create `frontend/src/components/stats/PersonTagsWidget.tsx`

A self-contained interactive widget. Internal state:
- `role: "director" | "composer" | "actor"` (default "director")
- `query: string` (text in search box)
- `selectedPerson: PersonSearchResult | null`
- `tags: PersonTagsResponse | null`
- `loading: boolean`

Layout:
- Top row: 3-button toggle (Director / Composer / Actor) using shadcn Toggle/ToggleGroup, plus a search Input next to it
- When `query.length >= 2` and no `selectedPerson`: debounced (250ms) call to `searchPeopleWithFilms`, show dropdown of up to 30 results below the input. Each row: "Name — N films". Click → sets selectedPerson, clears query, calls getPersonTags.
- When `selectedPerson` is set: show the 4 ranked lists (themes/atmospheres/characters/messages), and a "× Reset" button next to the person name (e.g. "Akira Kurosawa — 27 films  ×")
- Resetting clears selectedPerson and tags, returns to search state.
- Changing the role toggle resets the selection too.

Display of the 4 lists:
- Use a 2-column grid (Themes | Atmospheres in row 1, Characters | Messages in row 2) on desktop. On mobile, single column.
- Each list has a small heading (e.g., "Top 8 themes") and entries shown as `<TagPill>` with the count beside the name (`war (8)`).
- Use existing Tag chip styling if available, or a simple badge with amber border.

Loading state: show a small skeleton or spinner.

### 6. Update `TaxonomyTab.tsx` with all 5 new sections

Keep the existing top sections (Top 20 themes / Categories distribution / Atmosphere word cloud) at the top.

New sections in this order:

1. **Categories × decade (% within decade)** — use `<DecadeHeatmap>` with the new props.
   - Subtitle: "What share of each decade's films belongs to each genre. Each cell = % of decade."
   - cellLabel: returns `${pct}%` if pct >= 1, else empty
   - tooltip: `"{category} · {decade}s · {pct}% ({film_count} of {decade_total} films)"`
2. **Cinema movements × decade (counts)** — use `<DecadeHeatmap>` with rowSortOrder so movements appear chronologically.
   - Subtitle: "Number of films tagged with each movement, per decade. The diagonal pattern reveals when each era dominated."
   - cellLabel: returns count if > 0
   - rowLabelWidth: 160 (for "hollywood golden age")
3. **Messages × decade (% within decade)** — use `<DecadeHeatmap>` with rowSortOrder.
   - Subtitle: "% of films per decade conveying each message. Notice when feminist films emerge, when ecological themes appear..."
   - cellLabel: returns `${pct}%` if pct >= 0.5, else empty
4. **Most common tags by filmography** — use `<PersonTagsWidget>`.
   - Subtitle: "Pick a director, actor, or composer to see their characteristic themes, atmospheres, characters, and messages."
5. **Atmosphere by genre** — use `<AtmosphereCategoryHeatmap>`.
   - Subtitle: "% of films in each genre matching each atmosphere. A genre's signature mood profile."

Wrap each in `<Section title="..." subtitle="...">`.

### 7. Verification

After implementation, log in as Pro/Admin, visit `/stats?tab=taxonomy`:
- All existing top sections still render correctly
- 3 heatmaps render with correct row ordering (categories alphabetical, movements chronological by sort_order, messages chronological by sort_order)
- Cell labels show "%" for the two percentage heatmaps, plain numbers for cinema movements
- Person widget: switch role, search a few directors, verify tag breakdowns appear
- Atmosphere×category heatmap renders 12 rows (categories) × ~23 cols (atmospheres). Tooltips work.

### Important notes

- Match existing dark theme. Heatmap cell color stays amber.
- Mobile: heatmaps need horizontal scroll (existing pattern, kept). Person widget grid collapses to 1 column.
- Don't break existing PeopleTab, FinancialsTab, QuickStatsTab — only the Taxonomy tab is touched.
- All new sections inherit the existing tab gating (Pro/Admin only) — no new tier checks needed in frontend.
- React Query: the dashboard query is already cached, so the new fields come along for free. The two new endpoints (person-tags, people-with-films) don't need React Query — use simple `useState` + `useEffect` debounced calls inside `PersonTagsWidget`.
```

---


