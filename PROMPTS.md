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

## Step 5.5 Prompt — API Enhancements: Geography, Language & Missing Filters

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 5.5 specification. Then read ALL of the following files to understand the current codebase:

- `backend/app/routers/films.py` — Current film list endpoint with filters (see `_taxonomy_filters` list and the `country` filter)
- `backend/app/routers/taxonomy.py` — Current taxonomy endpoint with `DIMENSION_MAP` dict and hierarchical theme handling
- `backend/app/schemas/film.py` — Current Pydantic schemas (FilmListItem, FilmUpdate, etc.)
- `backend/app/schemas/taxonomy.py` — TaxonomyItem, TaxonomyList schemas
- `backend/app/main.py` — Router includes (you'll add a new geography router)
- `database/schema.sql` — See the `geography`, `film_set_place`, `language`, `film_language`, `place_context`, `film_place`, `character_context`, `film_character_context` table definitions

### Goal

Enhance the backend API with 4 additions needed by the frontend before Step 6 begins:

1. **Geography search endpoint** — new router + schemas
2. **Enhanced location filter** — replace limited `country` param with broader `location`
3. **Language taxonomy + filter** — new dimension in taxonomy + filter param on films
4. **Missing taxonomy filter params** — add `character_contexts` and `place_contexts` to film list

### A. Geography Router — `backend/app/routers/geography.py` (NEW FILE)

Create a new router with two endpoints:

**`GET /api/geography/search?q=paris&limit=20`**

Search across all 3 geography levels (continent, country, state_city) using ILIKE. Return matching locations with film counts.

```sql
SELECT g.geography_id, g.continent, g.country, g.state_city,
       COUNT(DISTINCT fsp.film_id) AS film_count
FROM geography g
LEFT JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
WHERE g.continent ILIKE :q
   OR g.country ILIKE :q
   OR g.state_city ILIKE :q
GROUP BY g.geography_id, g.continent, g.country, g.state_city
ORDER BY film_count DESC
LIMIT :limit
```

Build a `label` field by joining non-null parts: e.g. "Paris, France, Europe" or "France, Europe" or "Europe".

Response schema (`GeographySearchResult`):
```python
class GeographySearchResult(BaseModel):
    geography_id: int
    label: str              # "Paris, France, Europe"
    continent: str | None
    country: str | None
    state_city: str | None
    film_count: int
```

**`GET /api/geography/countries`**

Return all distinct countries with film counts, sorted by count DESC. Useful for a dropdown.

```sql
SELECT g.country, COUNT(DISTINCT fsp.film_id) AS film_count
FROM geography g
JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
WHERE g.country IS NOT NULL
GROUP BY g.country
ORDER BY film_count DESC
```

Response: `list[CountryItem]` where `CountryItem` has `country: str` and `film_count: int`.

### B. Geography Schemas — `backend/app/schemas/geography.py` (NEW FILE)

```python
from pydantic import BaseModel

class GeographySearchResult(BaseModel):
    geography_id: int
    label: str
    continent: str | None = None
    country: str | None = None
    state_city: str | None = None
    film_count: int = 0

class CountryItem(BaseModel):
    country: str
    film_count: int = 0
```

### C. Enhanced Location Filter — modify `backend/app/routers/films.py`

In the `list_films` function:

1. **Add new query parameter** `location: str | None = None` alongside the existing `country` parameter.

2. **Merge both**: if `location` is provided, use it. If only `country` is provided (backward compat), use `country` as `location`. If both, prefer `location`.

3. **Replace the current country filter** SQL with a broader version that searches across all geography levels:

```python
# Location filter (replaces old country-only filter)
loc = location or country
if loc:
    where_clauses.append(
        """f.film_id IN (
            SELECT fsp.film_id FROM film_set_place fsp
            JOIN geography g ON fsp.geography_id = g.geography_id
            WHERE g.country ILIKE :location
               OR g.state_city ILIKE :location
               OR g.continent ILIKE :location
        )"""
    )
    params["location"] = f"%{loc}%"
```

4. **Add `character_contexts` query parameter**: `character_contexts: list[str] | None = Query(None)`

5. **Add `place_contexts` query parameter**: `place_contexts: list[str] | None = Query(None)`

6. **Add `language` query parameter**: `language: str | None = None`

7. **Add both new taxonomy entries to `_taxonomy_filters` list**:
```python
(character_contexts, "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
(place_contexts, "film_place", "place_context_id", "place_context", "place_context_id", "environment"),
```

8. **Add language filter** (not a taxonomy array filter — it's a single string ILIKE):
```python
if language:
    where_clauses.append(
        """f.film_id IN (
            SELECT fl.film_id FROM film_language fl
            JOIN language l ON fl.language_id = l.language_id
            WHERE fl.is_original = TRUE
              AND l.language_name ILIKE :language
        )"""
    )
    params["language"] = f"%{language}%"
```

### D. Language Taxonomy — modify `backend/app/routers/taxonomy.py`

Add `"languages"` to the taxonomy endpoint. Since language needs special handling (count only `is_original = TRUE` entries), add it as a special case alongside the existing `categories` special case.

**Option:** Add `"languages"` to `DIMENSION_MAP` with a custom flag, or handle it as an `if dimension == "languages":` block before the generic query.

The query for languages:
```sql
SELECT l.language_id, l.language_name,
       COUNT(DISTINCT fl.film_id) AS film_count
FROM language l
LEFT JOIN film_language fl ON l.language_id = fl.language_id AND fl.is_original = TRUE
GROUP BY l.language_id, l.language_name
ORDER BY film_count DESC, l.language_name ASC
```

Note: sorted by film_count DESC first (most common languages at top), then alphabetically. This is different from other dimensions which sort alphabetically. The frontend will benefit from seeing "English (50)" and "French (30)" before "Latin (0)".

### E. Register Geography Router — modify `backend/app/main.py`

Add the geography router import and include:

```python
from backend.app.routers import films, persons, taxonomy, geography

app.include_router(geography.router, prefix="/api")
```

### F. Important Technical Notes

1. **Don't break existing endpoints.** The `country` param on `GET /api/films` must keep working. The `location` param is an addition, not a replacement. If both are provided, `location` takes priority.

2. **Use `await db.execute(text(...))` for all queries** — same pattern as existing routers. No ORM.

3. **The language filter uses `is_original = TRUE`** to filter by the film's original language, not by which languages it has titles in. A French film dubbed in English should only match `language=French`.

4. **Geography search `q` param must have `min_length=1`** to prevent empty searches that return everything.

5. **The `_taxonomy_filters` list in films.py** uses a consistent tuple structure: `(param_value, junction_table, junction_fk, lookup_table, lookup_pk, lookup_name_col)`. The two new entries follow this exact pattern.

### Validation

After all changes:

1. `uvicorn backend.app.main:app --reload` — starts without errors
2. Swagger UI at `/docs` shows the new geography endpoints
3. `GET /api/geography/search?q=france` — returns geography entries matching "france"
4. `GET /api/geography/search?q=paris` — returns Paris entries with film counts
5. `GET /api/geography/countries` — returns country list sorted by film count
6. `GET /api/films?location=France` — returns films set in France
7. `GET /api/films?location=Paris` — returns films set in Paris (state_city match)
8. `GET /api/films?country=France` — still works (backward compat)
9. `GET /api/taxonomy/languages` — returns languages with film counts, sorted by count DESC
10. `GET /api/films?language=English` — returns films with English as original language
11. `GET /api/films?character_contexts=psychopath` — filters correctly
12. `GET /api/films?place_contexts=urban` — filters correctly
13. All existing filters still work exactly as before (categories, themes, etc.)

Do NOT run the server yourself — just ensure the code is correct and all imports resolve. The user will test manually.

---

## Step 6 Prompt — Frontend: Browse, Search & Filter

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 6 specification. Then read these files to understand the API you'll be consuming:

- `backend/app/schemas/film.py` — FilmListItem, FilmDetail, PaginatedFilms response shapes
- `backend/app/schemas/taxonomy.py` — TaxonomyItem, TaxonomyList response shapes
- `backend/app/schemas/geography.py` — GeographySearchResult, CountryItem response shapes
- `backend/app/schemas/person.py` — PersonSummary, PersonDetail response shapes
- `backend/app/routers/films.py` — Film endpoint query parameters and filtering logic
- `backend/app/routers/taxonomy.py` — Taxonomy dimensions including languages
- `backend/app/routers/geography.py` — Geography search and countries endpoints
- `backend/app/main.py` — CORS config (allows localhost:3000)

### Goal

Build the main frontend application: a dark-themed, responsive film browser with poster grid, taxonomy filter sidebar, search bar, active filter chips, sorting, and pagination. This is the primary user interface for exploring the film database.

Tech stack: **Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui**

The backend API runs on `http://localhost:8000`. The frontend dev server will run on `http://localhost:3000`.

### A. Project Scaffolding — `frontend/`

Initialize the project in the `frontend/` directory at the repo root:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

Then set up Tailwind CSS and shadcn/ui:

```bash
npm install -D tailwindcss @tailwindcss/vite
npx shadcn@latest init
```

When running `npx shadcn@latest init`, choose:
- Style: New York
- Base color: Zinc
- CSS variables: Yes

Then install the shadcn/ui components we need:

```bash
npx shadcn@latest add badge button input scroll-area select separator sheet skeleton toggle
```

**Configure Vite** (`vite.config.ts`):
```typescript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

The proxy means the frontend calls `/api/films` and Vite forwards to `http://localhost:8000/api/films`. This avoids CORS issues in development.

### B. TypeScript Types — `src/types/api.ts`

Define types matching the API response schemas exactly. Read `backend/app/schemas/film.py`, `backend/app/schemas/taxonomy.py`, and `backend/app/schemas/geography.py` for the exact shapes.

```typescript
export interface FilmListItem {
  film_id: number;
  original_title: string;
  first_release_date: string | null; // ISO date string
  duration: number | null;
  poster_url: string | null;
  vu: boolean;
  categories: string[];
  director: string | null;
}

export interface PaginatedFilms {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: FilmListItem[];
}

export interface TaxonomyItem {
  id: number;
  name: string;
  film_count: number | null;
}

export interface TaxonomyList {
  dimension: string;
  items: TaxonomyItem[];
}

export interface GeographySearchResult {
  geography_id: number;
  label: string;
  continent: string | null;
  country: string | null;
  state_city: string | null;
  film_count: number;
}

export interface CountryItem {
  country: string;
  film_count: number;
}

export interface StatsResponse {
  total_films: number;
  seen: number;
  unseen: number;
  by_decade: { decade: number; count: number }[];
  top_categories: { name: string; count: number }[];
  top_countries: { name: string; count: number }[];
}

export interface FilterState {
  q: string;
  categories: string[];
  themes: string[];
  atmospheres: string[];
  characters: string[];
  character_contexts: string[];
  motivations: string[];
  messages: string[];
  cinema_types: string[];
  cultural_movements: string[];
  time_periods: string[];
  place_contexts: string[];
  location: string;
  language: string;
  year_min: number | null;
  year_max: number | null;
  director: string;
  vu: boolean | null;
  sort_by: "year" | "title" | "duration";
  sort_order: "asc" | "desc";
  page: number;
  per_page: number;
}
```

### C. API Client — `src/api/client.ts`

Create a typed fetch wrapper. Since Vite proxies `/api` to the backend, all URLs are relative.

```typescript
const BASE = '/api';

export async function fetchFilms(params: Record<string, any>): Promise<PaginatedFilms> { ... }
export async function fetchTaxonomy(dimension: string): Promise<TaxonomyList> { ... }
export async function fetchStats(): Promise<StatsResponse> { ... }
export async function searchGeography(q: string): Promise<GeographySearchResult[]> { ... }
```

Key:
- Build query strings from the filter state. For array params like `categories=Drama&categories=Thriller`, repeat the key (FastAPI expects this format for `list[str]` query params).
- Skip null/empty/default values to keep URLs clean.
- Handle errors gracefully (show toast or inline error).

### D. Custom Hooks — `src/hooks/`

**`useFilterState.ts`** — Central filter state management:
- Initialize from URL search params on mount
- Sync filter changes back to URL (using `useSearchParams` or `window.history.replaceState`)
- Provide setter functions: `toggleFilter(dimension, value)`, `removeFilter(dimension, value)`, `clearAllFilters()`, `setSearch(q)`, `setSort(by, order)`, `setPage(n)`
- Reset page to 1 whenever filters change

**`useFilms.ts`** — Film data fetching:
- Depends on filter state (re-fetches when filters change)
- Returns `{ films: PaginatedFilms | null, loading: boolean, error: string | null }`
- Debounce search query changes (300ms) before triggering fetch

**`useTaxonomy.ts`** — Taxonomy data fetching:
- Fetch all 11 displayed taxonomy dimensions on mount (can be parallel)
- Cache results (taxonomy values rarely change within a session)
- Returns `{ taxonomies: Record<string, TaxonomyItem[]>, loading: boolean }`
- The 11 dimensions to fetch: categories, themes, atmospheres, characters, character_contexts, motivations, messages, cinema_types, cultural_movements, time_periods, place_contexts

### E. Layout Components — `src/components/layout/`

**`Layout.tsx`** — Main layout shell:
- Fixed header at top (h-16)
- Sidebar on the left (w-72, scrollable, hidden on mobile)
- Main content area (flex-1, overflow-y-auto)
- Mobile: sidebar hidden, accessible via Sheet component triggered by a filter button in the header

**`Header.tsx`** — Top navigation bar:
- Left: app title/logo ("Film Database") + total films badge from stats
- Center: search Input with magnifying glass icon, clear button, debounced onChange
- Right: sort Select dropdown (Year, Title, Duration) + sort order Toggle (↑/↓)
- Mobile: add a filter icon Button that opens the sidebar Sheet

**`Sidebar.tsx`** — Filter sidebar:
- Scrollable list of FilterSection components (one per taxonomy dimension — 11 sections)
- Location autocomplete input (backed by `GET /api/geography/search?q=`)
- Language dropdown or autocomplete (backed by `GET /api/taxonomy/languages`)
- A "Seen" filter toggle (3-state: All / Seen only / Unseen only)
- Year range inputs (two small number Inputs: min year, max year)
- Director text Input (free-text, debounced)

### F. Filter Components — `src/components/filters/`

**`FilterSection.tsx`** — Collapsible section for one taxonomy dimension:
- Props: `title: string`, `dimension: string`, `items: TaxonomyItem[]`, `activeValues: string[]`, `onToggle: (value: string) => void`
- Header: dimension name + active count badge, click to collapse/expand
- Body: scrollable list of FilterChip components
- Default: first 2-3 sections expanded, rest collapsed

**`FilterChip.tsx`** — Individual taxonomy value chip:
- Props: `name: string`, `count: number | null`, `active: boolean`, `onClick: () => void`
- Display: `name (count)` — e.g., "Drama (2)"
- Active state: filled background (amber), inactive: outline/ghost
- Use shadcn Badge component with variant switching

**`ActiveFilters.tsx`** — Bar showing all currently applied filters:
- Render above the film grid, only visible when at least one filter is active
- Each active filter: Badge showing `"Dimension: value"` with an X button to remove
- "Clear all" button at the end
- Include search term, year range, director, location, language, vu in addition to taxonomy filters

### G. Film Components — `src/components/films/`

**`FilmGrid.tsx`** — Responsive poster grid:
- CSS Grid: `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4`
- Renders FilmCard components from the items array
- Shows Skeleton cards while loading
- Shows "No films found" message when items is empty and not loading
- Shows total count: "Showing X of Y films"

**`FilmCard.tsx`** — Individual film poster card:
- Props: `film: FilmListItem`
- Poster image (2:3 aspect ratio using `aspect-[2/3]`): use `poster_url` or a placeholder gradient
- Below poster: title (truncated to 2 lines), year, director name
- Category badges (first 2-3 categories as small badges)
- "Seen" indicator: small green dot or eye icon overlay on poster corner if `vu === true`
- Hover: `hover:scale-105 transition-transform` + shadow increase
- Clickable: for now, link to `/films/{film_id}` (detail page will be built in step 7 — just have the route ready, can show a placeholder page)

**`Pagination.tsx`** — Page navigation:
- Props: `page: number`, `totalPages: number`, `onPageChange: (page: number) => void`
- Previous/Next buttons (disabled at boundaries)
- Page number buttons with ellipsis for large ranges
- "Page X of Y" display
- Scroll to top on page change

### H. App & Routing — `src/App.tsx`

Use `react-router-dom` for routing:

```bash
npm install react-router-dom
```

Routes:
- `/` → redirect to `/browse`
- `/browse` → Main browse page (the grid + filters view built in this step)
- `/films/:id` → Film detail page (placeholder for step 7 — just show "Film Detail — coming soon" with a back button)

The browse page component assembles: Layout with Sidebar + Header + ActiveFilters + FilmGrid + Pagination.

### I. Dark Theme & Styling

Configure shadcn/ui for a dark film-database aesthetic. Set the theme in the shadcn CSS variables:

```css
:root {
  /* Dark theme as default */
  --background: 0 0% 6%;          /* #0f0f0f */
  --foreground: 0 0% 98%;         /* #fafafa */
  --card: 0 0% 10%;               /* #1a1a1a */
  --card-foreground: 0 0% 98%;
  --muted: 0 0% 15%;
  --muted-foreground: 240 5% 65%;
  --accent: 38 92% 50%;           /* amber #f59e0b */
  --accent-foreground: 0 0% 6%;
  --primary: 38 92% 50%;          /* amber */
  --primary-foreground: 0 0% 6%;
  --border: 0 0% 18%;
  --ring: 38 92% 50%;
}
```

Body background: `bg-background`, text: `text-foreground`. The overall feel should be like a premium film library app (think Letterboxd or Criterion Channel) — dark, poster-centric, typographically clean.

### J. Important Technical Notes

1. **API array params:** FastAPI expects repeated query params for lists: `?categories=Drama&categories=Thriller` (NOT `?categories=Drama,Thriller`). Build the query string accordingly.

2. **TMDB poster URLs:** The `poster_url` field already contains the full URL (e.g., `https://image.tmdb.org/t/p/w500/...`). Just use it directly in `<img src>`.

3. **Hierarchical themes:** The taxonomy API returns items like `"art"`, `"art: music"`, `"art: cinema"`. In the filter sidebar, you could display these grouped under their parent (but flat display with all items is also fine for v1). The parent items already have aggregated counts.

4. **Initial load:** On first load with no URL params, show all films sorted by year descending. Taxonomy data should be fetched once on app startup.

5. **Error handling:** If the API is unreachable (backend not running), show a clear error message: "Cannot connect to the API. Make sure the backend is running on port 8000."

6. **No authentication:** This is a personal, single-user application. No login required.

7. **Per-page default:** Use `per_page=24` as default (divisible by 2, 3, 4, 6 — works well with all grid column counts).

### Validation

After all files are created:

1. `cd frontend && npm install && npm run dev` → starts on http://localhost:3000 without errors
2. Backend must be running: `uvicorn backend.app.main:app --reload` (on port 8000)
3. Browse page shows the 3 seeded films with poster images
4. Filter sidebar shows all 11 taxonomy dimensions with correct counts
5. Clicking a category chip filters the grid and adds an active filter chip
6. Removing a filter chip restores the grid
7. "Clear all" removes all filters
8. Search bar works (type "Kubrick" → shows 2001: A Space Odyssey)
9. Sort by title/year works
10. Pagination controls work (test with per_page=2 in URL: `/browse?per_page=2`)
11. URL updates reflect filter state (copy URL, paste in new tab → same view)
12. Browser back/forward buttons navigate filter history
13. Mobile view: sidebar collapses, filter button opens drawer
14. Loading skeletons appear during API calls
15. "No films found" displays when filters match nothing
16. Clicking a film card navigates to `/films/{id}` (placeholder page OK)
17. Location autocomplete returns geography results when typing
18. Language filter works

Do NOT run the server yourself. Do NOT run `npm install` or `npm run dev`. Just ensure the code is correct and all imports resolve. The user will install and test manually.

---
