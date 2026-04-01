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

## Step 11a Prompt — Backend Auth + Deployment Config

```
Read CLAUDE.md, then PLAN.md (Step 11, sub-step 11a), then PROMPTS.md (this prompt).

Read the following files before making changes:
- backend/app/main.py
- backend/app/routers/films.py
- backend/app/routers/add_film.py
- backend/app/routers/taxonomy.py
- .env.example

## Task: Add admin authentication + deployment configuration to the backend

### 1. Create `backend/app/auth.py`

Create a FastAPI dependency `require_admin` that:
- Reads the `Authorization` header from the request
- Expects format: `Bearer <token>`
- Compares the token to `ADMIN_SECRET_KEY` environment variable
- If missing, malformed, or non-matching: raise HTTPException(401, "Unauthorized")
- If `ADMIN_SECRET_KEY` is not set in env (development fallback): allow all requests (so local dev works without setting a key)

Use `from fastapi import Header, HTTPException` and `os.getenv`.

### 2. Modify `backend/app/main.py`

A) Replace hardcoded CORS origins with environment-based config:
```python
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
origins = [o.strip() for o in origins if o.strip()]
```
Use this list in `allow_origins`.

B) Add two auth endpoints directly on the app (not in a separate router, keep it simple):

`POST /api/auth/login`:
- Accepts JSON body `{"password": "..."}`
- Compares password to `ADMIN_SECRET_KEY` env var
- If match: return `{"token": password}` (the secret key IS the bearer token)
- If no match: return 401
- If `ADMIN_SECRET_KEY` not set: return 401 with message "Admin auth not configured"

`GET /api/auth/check`:
- Uses `Depends(require_admin)`
- Returns `{"admin": true}`
- If not authenticated, the dependency returns 401 before this runs

Import `require_admin` from `backend.app.auth`.

### 3. Protect write endpoints in `backend/app/routers/films.py`

Add `admin: None = Depends(require_admin)` parameter to these endpoint functions:
- `toggle_vu` (PATCH)
- `create_film` (POST)
- `update_film` (PUT)
- `delete_film` (DELETE)
- `add_film_relation` (POST)
- `delete_film_relation` (DELETE)

Do NOT add auth to: `list_films` (GET), `search_local_films` (GET), `get_film` (GET), `get_stats` (GET).

Import: `from backend.app.auth import require_admin`

### 4. Protect write endpoints in `backend/app/routers/add_film.py`

Add `admin: None = Depends(require_admin)` to:
- `search_tmdb` (GET — uses TMDB API key, admin-only)
- `enrich_film` (POST — uses Claude API key, admin-only)

Import: `from backend.app.auth import require_admin`

### 5. Protect write endpoints in `backend/app/routers/taxonomy.py`

Add `admin: None = Depends(require_admin)` to:
- `add_taxonomy_value` (POST)
- `rename_taxonomy_value` (PUT)
- `merge_taxonomy_values` (POST)
- `delete_taxonomy_value` (DELETE)

Do NOT add auth to: `get_taxonomy` (GET).

Import: `from backend.app.auth import require_admin`

### 6. Create `Procfile` at project root

Single line:
```
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

### 7. Update `.env.example`

Add these lines:
```
# Admin auth (set a strong random string for production)
ADMIN_SECRET_KEY=

# CORS (comma-separated origins, for production add your Vercel domain)
CORS_ORIGINS=http://localhost:3000
```

### Verification

After implementation, test locally:
1. Start backend with `uvicorn backend.app.main:app --reload`
2. `GET /api/films` should work without auth (200)
3. `POST /api/films` without auth header should return 401 (when ADMIN_SECRET_KEY is set in .env)
4. Without ADMIN_SECRET_KEY in .env, all endpoints should work (dev fallback)
```

---

## Step 11b Prompt — Frontend Auth + Deployment Config

```
Read CLAUDE.md, then PLAN.md (Step 11, sub-step 11b), then PROMPTS.md (this prompt).

Read the following files before making changes:
- frontend/src/api/client.ts
- frontend/src/App.tsx
- frontend/src/components/layout/Header.tsx
- frontend/src/pages/BrowsePage.tsx
- frontend/src/components/films/FilmCard.tsx
- frontend/src/pages/FilmDetailPage.tsx
- frontend/src/pages/TaxonomyAdminPage.tsx
- frontend/src/pages/AddFilmPage.tsx
- frontend/src/types/api.ts

## Task: Add frontend auth context, login page, and conditional admin UI

### 1. Modify `frontend/src/api/client.ts`

A) Replace `const BASE = "/api"` with:
```typescript
const BASE = import.meta.env.VITE_API_URL || "/api";
```

B) Add auth token helper:
```typescript
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("admin_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}
```

C) Update ALL existing fetch calls that use POST, PUT, PATCH, DELETE methods to include auth headers. For every `fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, ...})`, merge in `...getAuthHeaders()` into the headers object. Same for PUT, PATCH, DELETE calls.

Specifically update these functions: `addTaxonomyValue`, `renameTaxonomyValue`, `mergeTaxonomyValues`, `deleteTaxonomyValue`, `deleteFilm`, `updateFilm`, `toggleVu`, `enrichFilm`, `addFilmRelation`, `deleteFilmRelation`, `saveFilm`.

D) Add two new API functions:
```typescript
export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/auth/check`, {
      headers: { ...getAuthHeaders() },
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function loginAdmin(password: string): Promise<string> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, "Login failed");
  }
  const data = await res.json();
  return data.token;
}
```

### 2. Create `frontend/src/context/AuthContext.tsx`

Create a React context with provider that:
- Stores state: `isAdmin` (boolean), `token` (string | null), `loading` (boolean)
- On mount: checks localStorage for `admin_token`, if found calls `checkAuth()` to validate. Sets `isAdmin = true` if valid, clears token if invalid.
- Provides `login(password: string)` function: calls `loginAdmin(password)`, stores token in localStorage, sets `isAdmin = true`
- Provides `logout()` function: removes token from localStorage, sets `isAdmin = false`
- Exports `AuthProvider` component and `useAuth()` hook

While `loading` is true (initial auth check), show nothing or a minimal spinner to avoid UI flash.

### 3. Create `frontend/src/pages/LoginPage.tsx`

Minimal login page matching the app's dark theme:
- Centered card with "Admin Login" heading
- Single password input field
- Submit button "Login"
- On submit: call `login()` from auth context, on success navigate to `/browse`, on error show inline error message
- If already admin (`isAdmin` from context), redirect to `/browse` immediately
- Use existing shadcn/ui components (Button, Input) and the app's dark theme styling
- Import Layout component to wrap the page (consistent header/footer)

### 4. Modify `frontend/src/App.tsx`

- Import and wrap everything inside `<AuthProvider>` (inside BrowserRouter)
- Add route: `<Route path="/login" element={<LoginPage />} />`
- Import LoginPage

### 5. Modify `frontend/src/components/layout/Header.tsx`

- Import `useAuth` from the auth context
- Import `LogIn` and `LogOut` icons from lucide-react
- Get `{ isAdmin, logout }` from `useAuth()`
- Wrap the "Add Film" button (`<Plus>` icon) in `{isAdmin && ...}` — hide when not admin
- Wrap the "Tags" button (`<Tags>` icon) in `{isAdmin && ...}` — hide when not admin
- Add a new button:
  - If `isAdmin`: show LogOut icon button, onClick calls `logout()`
  - If not admin: show LogIn icon button, onClick navigates to `/login`
- Place the login/logout button at the right end of the header controls

### 6. Modify `frontend/src/pages/BrowsePage.tsx`

- Import `useAuth` from auth context
- Get `{ isAdmin }` from `useAuth()`
- When passing the `onToggleVu` callback to FilmCard, only pass it if `isAdmin` is true. If not admin, pass `undefined`.
- This means FilmCard needs to handle `onToggleVu` being optional.

### 7. Modify `frontend/src/components/films/FilmCard.tsx`

- Make the `onToggleVu` prop optional (`onToggleVu?: (filmId: number, vu: boolean) => void`)
- If `onToggleVu` is undefined: render the eye icon as a static visual indicator (no click handler, no hover effect), OR hide the eye icon entirely for public visitors
- If `onToggleVu` is provided: keep current behavior (clickable with optimistic update)

### 8. Modify `frontend/src/pages/FilmDetailPage.tsx`

- Import `useAuth` from auth context
- Get `{ isAdmin }` from `useAuth()`
- Wrap ALL edit-related UI in `{isAdmin && ...}`:
  - The delete film button (trash icon)
  - EditableTagSection: pass a `readOnly={!isAdmin}` prop or wrap the edit toggle in `isAdmin`
  - EditableFinancials: same approach
  - AwardsTable edit mode: same approach
  - Seen/unseen toggle button: make it functional only when `isAdmin`, otherwise display-only
- Public visitors should see all film data (taxonomy tags, awards, financials) but with NO edit controls

### 9. Modify `frontend/src/pages/TaxonomyAdminPage.tsx`

- Import `useAuth` and `useNavigate`
- If `!isAdmin` and not loading: redirect to `/browse` using `useEffect` + `navigate`
- This prevents public users from accessing the admin taxonomy page even by typing the URL

### 10. Modify `frontend/src/pages/AddFilmPage.tsx`

- Import `useAuth` and `useNavigate`
- If `!isAdmin` and not loading: redirect to `/browse` using `useEffect` + `navigate`
- This prevents public users from accessing the add film page

### Important notes

- The app's existing dark theme uses charcoal #0f0f0f background with amber #f59e0b accent. The login page should match.
- The localStorage key for the token should be `admin_token`.
- The `AuthProvider` must be inside `BrowserRouter` (because LoginPage uses `useNavigate`).
- Don't break any existing functionality — the app should work exactly as before when logged in as admin.
- When not logged in, the app should be a clean read-only browsing experience with no visible admin controls.
```
