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
| 8 | Add Film workflow | ✅ DONE | TMDB search → Claude enrich → review → save, enrichment prompt improvements, new taxonomy values |
| 8.5 | Auto-link franchise sequels | ✅ DONE | TMDB collection → film_sequel auto-creation, backfill script, refresh_streaming script |
| 8.6 | Editable fields + person data | ✅ DONE | Editable categories/financials/awards, person gender in pipeline, backfill_person_details script |
| 9 | Bulk ingestion (~2500 films) | ✅ DONE | Parse Films_list.docx, batch TMDB + Claude + DB insert |
| 10 | UX: empty tags, year inputs, studio search, film relations | ✅ DONE | Editable related films with posters, collapsible sidebar |
| 10.5 | Film detail layout + Taxonomy admin page | ✅ DONE | Production in hero, related films with posters, /admin/taxonomy CRUD, export script |
| 10.6 | Delete film, seen toggle on grid, backfill optimization, README | ✅ DONE | DELETE endpoint + trash button, FilmCard vu toggle, filtered backfill script, README.md |
| 11 | Deployment + auth (Supabase + Render + Vercel) | ✅ DONE | Admin auth, CORS from env, frontend auth context, deploy to cloud |
| 12 | Taxonomy restructure | ✅ DONE | merge dimensions, add sort_order grouping, rebalance tags |
| 13 | Performance optimization (deployed) | ✅ DONE | Parallel DB queries, React Query caching, region fix |
| 14 | Advanced 'click on tag' behaviour | ✅ DONE | Addition of 'Exclude' and 'Or' on multi-select |
| 15a | Supabase Auth + user roles + vu migration | 🔲 TODO | JWT auth, user_profile, user_film_status, migrate film.vu |
| 15b | Personal film status UI | 🔲 TODO | Per-user seen/favorites/watchlist, My Collection page |

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

## Step 8: Add Film Workflow ✅

- Backend: `add_film.py` router with GET `/add-film/search` and POST `/add-film/enrich`
- Frontend: `AddFilmPage.tsx` 3-step wizard (Search → Enrich → Review → Save)
- Enrichment quality: rewritten system prompt, new taxonomy values (migration 007), underscore renames (migration 008)

## Step 8.5: Auto-link Franchise Sequels via TMDB Collection ✅

- Migration 009: `tmdb_collection_id` column + auto-linking in `create_film()`
- New scripts: `backfill_collection_ids.py`, `refresh_streaming.py`

## Step 8.6: Editable Fields + Person Data ✅

- Frontend: `EditableTagSection` for categories, `EditableFinancials` component, editable `AwardsTable` (won/nominated toggle + remove)
- Backend: awards in `FilmUpdate` + clear-and-reinsert in `update_film()`, gender in `_find_or_create_person()`
- Pipeline: `tmdb_mapper.py` passes gender (TMDB_GENDER_MAP) in cast/crew dicts
- New script: `backfill_person_details.py` (gender, birth/death dates, nationality from TMDB /person/{id})

---

## Step 9: Bulk Ingestion (~2500 films)

*(see PLAN.md git history for details)*

## Step 10: UX improvements ✅

- Show empty taxonomy sections with "No tags yet" so tags can be added to any dimension
- Add min/max year number inputs alongside the range slider for precise filtering
- Replace studio dropdown with searchable input + scrollable results list
- Add RelatedFilmsSection component with search-to-link UI (sequel, remake, spinoff, etc.)
- Backend: search-local endpoint, POST/DELETE film relations endpoints
- Collapsible sidebar toggle in header (PanelLeftOpen/Close icons)

## Step 10.5: Film Detail Layout + Taxonomy Admin Page ✅

### Film detail page layout changes
- **Production info** (studios, source, financials) moved into hero area as compact lines
- **EditableFinancials** reworked to inline pencil + compact edit form
- **Related Films** moved between Synopsis and Cast, now shows poster thumbnails sorted by year
- Backend: related films query returns `poster_url`, ordered by `first_release_date ASC`

### Taxonomy admin page (`/admin/taxonomy`)
- Full CRUD admin interface for all 11 taxonomy dimensions
- **Add**: new value with optional sort_order
- **Rename**: inline edit with Enter/Escape support
- **Merge**: select target → confirmation → reassign all films, delete source (handles junction table conflicts)
- **Delete**: safety check with film count, force option for in-use values
- Categories special handling: composite key (`category_name` + `historic_subcategory_name`)
- Navigation: Tags icon in header bar

### Export script (`scripts/export_taxonomy.py`)
- Reads all taxonomy tables from DB, regenerates `database/seed_taxonomy.sql` and `backend/app/services/taxonomy_config.py`
- Preserves `REFERENCE_EXAMPLES` block from existing config
- `--dry-run` flag for preview
- Workflow: edit in UI → DB updates immediately → run export before committing

## Step 10.6: Delete Film, Seen Toggle on Grid, Backfill Optimization, README ✅

- **Delete film**: `DELETE /api/films/{film_id}` endpoint + trash icon on detail page with confirmation dialog, redirects to browse after deletion (CASCADE handles all related data)
- **Seen/unseen toggle on browse grid**: FilmCard eye icon is now a clickable button with optimistic update; seen = green eye always visible, unseen = grey eye-off appears on hover
- **Backfill optimization**: `backfill_person_details.py` now only processes directors, composers, and top-6 cast (instead of all persons); handles 429 rate limits with retry, 404 gracefully, commits in batches of 100
- **README.md**: Project overview, features, tech stack, project structure, how-to-run guide with common commands, taxonomy dimensions table

---

## Step 11: Deployment + Admin Auth (Supabase + Render + Vercel) ✅

- Backend: `auth.py` with `require_admin` dependency (bearer token vs `ADMIN_SECRET_KEY` env var, dev fallback allows all)
- Backend: CORS origins from env, `/api/auth/login` + `/api/auth/check` endpoints, `Depends(require_admin)` on all write endpoints
- Frontend: `AuthContext` (localStorage token, auto-validate on mount), `LoginPage`, `getAuthHeaders()` in API client
- Frontend: admin-only UI gating (Add Film, Tags, edit controls, vu toggle, delete) — public = read-only browse
- Deployment: `Procfile` for Render, `VITE_API_URL` env for Vercel, Supabase for DB
- Infrastructure: Supabase (DB) + Render (backend) + Vercel (frontend CDN)

## Step 12: Taxonomy restructure — merge dimensions, add sort_order grouping, rebalance tags

  This covers: merging characters_type + character_context into single "characters" dimension, merging
  cinema_type + cultural_movement, moving Disaster to themes and dialogs to cinema, adding
  sort_order-based grouping to 7 dimensions, adding new theme values (curse, game), renaming gang →
  team/group/gang. Full-stack update across migration, schema, backend, frontend, enrichment pipeline,
  and scripts.

---

## Step 13: Performance Optimization (Deployed)

Backend (Part A):
  - database.py: pool_size 5 → 10
  - films.py: added asyncio import, engine import, _parallel_query() helper; rewrote get_film() to run
  all 18 taxonomy/relation queries via asyncio.gather() after the initial film lookup

  Frontend (Part B):
  - Installed @tanstack/react-query
  - App.tsx: wrapped in QueryClientProvider (staleTime 30s, gcTime 5min, no refetchOnWindowFocus)
  - useFilms.ts: React Query with 300ms debounced filters
  - useFilmDetail.ts: React Query with 60s staleTime, exposes refetch
  - useTaxonomy.ts: React Query with staleTime: Infinity
  - FilmDetailPage.tsx: vu toggle uses queryClient.setQueryData for optimistic update +
  invalidateQueries(["films"]) on success; delete invalidates films cache; handleSaved callback
  invalidates films list on any tag edit
  - AddFilmPage.tsx: invalidates films cache after saving a new film

---

## Step 14: Advanced 'click on tag' behaviour

Frontend:
  - types/api.ts: New TagFilter type ({ include: string[], exclude: string[], mode: "or" | "and" }).
  FilterState dimensions changed from string[] to TagFilter.
  - FilterChip.tsx: 3 visual states — off (default), include (blue/primary), exclude (red +
  strikethrough + ban icon). Right-click = exclude (desktop), long-press 500ms = exclude (mobile).
  - FilterSection.tsx: Passes tagFilter to chips, shows AND/OR toggle pill when 2+ tags are included.
  - ActiveFilters.tsx: Excluded tags shown with red styling + ban icon + strikethrough.
  - useFilterState.ts: New excludeFilter() and setFilterMode() callbacks. URL serialization: dim=val
  for includes, dim_not=val for excludes, dim_mode=and when AND.
  - client.ts: buildFilmParams emits the new param format.
  - Sidebar, Layout, BrowsePage: Plumbed through the new onExcludeFilter and onSetFilterMode props.

  Backend:
  - list_films(): Added _not and _mode query params for all 10 dimensions.
  - OR mode (default): WHERE name = ANY(:values) — no GROUP BY/HAVING, just match any.
  - AND mode: existing HAVING COUNT logic preserved.
  - NOT: WHERE film_id NOT IN (SELECT ... WHERE name = ANY(:excluded)).

---

## Step 15a: Supabase Auth + User Roles + vu Migration

### Goal
Replace the current `ADMIN_SECRET_KEY` bearer-token auth with Supabase Auth (email/password + Google OAuth). Introduce a user role model (`free`/`pro`/`admin`) and per-user film status. Migrate the global `film.vu` column to per-user `user_film_status.seen`.

### Database changes (Migration 011)

New tables:
```sql
CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY,                    -- matches Supabase auth.users.id
    email TEXT NOT NULL,
    display_name TEXT,
    tier TEXT NOT NULL DEFAULT 'free',       -- 'free' | 'pro' | 'admin'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_film_status (
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id) ON DELETE CASCADE,
    seen BOOLEAN DEFAULT FALSE,
    favorite BOOLEAN DEFAULT FALSE,
    watchlist BOOLEAN DEFAULT FALSE,
    rating SMALLINT CHECK (rating >= 1 AND rating <= 10),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, film_id)
);
```

Migration script (run after Martin's admin user_profile row is created):
1. Create tables above
2. INSERT Martin's user_profile row with tier='admin' (UUID from Supabase dashboard after first login)
3. Migrate `film.vu`: INSERT INTO user_film_status (user_id, film_id, seen) SELECT :admin_uuid, film_id, TRUE FROM film WHERE vu = TRUE
4. ALTER TABLE film DROP COLUMN vu
5. Update `schema.sql` for fresh installs (remove `vu` from film, add new tables)

### Backend changes

**New dependency**: `python-jose[cryptography]` in `requirements.txt`

**New env vars** (on Render):
- `SUPABASE_JWT_SECRET` — from Supabase dashboard > Settings > API > JWT Secret
- `SUPABASE_URL` — the Supabase project URL (for admin operations if needed later)

**Rewrite `auth.py`**:
- `verify_supabase_token(token)`: decode JWT using `python-jose`, verify with `SUPABASE_JWT_SECRET`, extract `sub` (user UUID)
- `get_current_user(authorization)`: optional dependency — returns `UserInfo(id, email, tier)` or `None` for anonymous
- `require_authenticated(user)`: raises 401 if no user
- `require_admin(user)`: raises 403 if user.tier != 'admin'
- On first token verification for a user, auto-create `user_profile` row if it doesn't exist yet (tier='free' default) — this avoids needing a separate registration API endpoint

**Update all router dependencies**:
- Admin endpoints: replace `Depends(require_admin)` with the new `Depends(require_admin)` (same name, new implementation that checks JWT + tier)
- New user endpoints: use `Depends(require_authenticated)`

**Remove from `main.py`**:
- `POST /api/auth/login` — no longer needed (Supabase handles login)
- `GET /api/auth/check` — replaced by `GET /api/auth/me` that returns user profile
- `LoginRequest` model — removed

**New endpoints**:
- `GET /api/auth/me` — returns current user profile (id, email, display_name, tier) or 401
- `GET /api/users/me/films/{film_id}/status` — get user's seen/favorite/watchlist for a film
- `PUT /api/users/me/films/{film_id}/status` — update seen/favorite/watchlist
- `GET /api/users/me/films?filter=seen|favorite|watchlist` — list user's films with status (for future My Collection page)

**Update `list_films` and `get_film`**:
- `vu` filter and `vu` field in responses must now be per-user: if a user is logged in, join `user_film_status` to include their `seen` status; if anonymous, return `seen: false` everywhere
- The `FilmListItem` and `FilmDetail` schemas replace `vu: bool` with `user_status: { seen: bool, favorite: bool, watchlist: bool } | null`
- The `PATCH /films/{id}/vu` endpoint is replaced by `PUT /api/users/me/films/{id}/status`

### Frontend changes

**New dependency**: `@supabase/supabase-js` in `package.json`

**New env vars** (on Vercel):
- `VITE_SUPABASE_URL` — Supabase project URL
- `VITE_SUPABASE_ANON_KEY` — Supabase anon/public key (safe for frontend)

**New file `src/lib/supabase.ts`**:
- Creates and exports the Supabase client instance
- Exposes helper functions for auth operations

**Rewrite `AuthContext.tsx`**:
- Replace localStorage token with Supabase session management
- `supabase.auth.onAuthStateChange()` listener to track login/logout
- Expose `user` (id, email, tier), `isAdmin`, `isAuthenticated`, `signIn`, `signUp`, `signInWithGoogle`, `signOut`
- On auth state change: send token to backend via `GET /api/auth/me` to sync user profile and get tier

**Rewrite `LoginPage.tsx`** → `AuthPage.tsx`:
- Combined login + register page (toggle between modes)
- Email/password form
- "Sign in with Google" button (one-click via `supabase.auth.signInWithOAuth({ provider: 'google' })`)
- Redirect to `/browse` on success
- Dark theme, consistent with existing design

**Update `api/client.ts`**:
- `getAuthHeaders()` now gets the token from `supabase.auth.getSession()` instead of localStorage
- Make this async: `async function getAuthHeaders(): Promise<Record<string, string>>`
- All authenticated API calls become async for the header retrieval (minor refactor since `fetch` is already async)

**Update `types/api.ts`**:
- `FilmListItem` and `FilmDetail`: replace `vu: boolean` with `user_status: UserFilmStatus | null`
- New `UserFilmStatus` type: `{ seen: boolean, favorite: boolean, watchlist: boolean, rating: number | null }`

**Update components**:
- `FilmCard.tsx`: seen toggle reads from `user_status?.seen`, calls new status endpoint
- `FilmDetailPage.tsx`: seen toggle calls new status endpoint, uses `queryClient.setQueryData` for optimistic update
- `Header.tsx`: show user menu (email + logout) when authenticated, "Sign in" button when anonymous
- `BrowsePage.tsx`: `vu` filter now only visible to authenticated users (it filters their personal seen status)

### Supabase dashboard configuration
- Enable Email provider (Settings > Authentication > Providers)
- Enable Google provider (requires Google Cloud Console OAuth credentials)
- Set Site URL to the Vercel frontend URL
- Add redirect URLs for both localhost:3000 (dev) and the Vercel domain

### Files modified
- `database/migrations/011_user_auth.sql` — new tables + vu migration
- `database/schema.sql` — updated for fresh installs
- `backend/requirements.txt` — add `python-jose[cryptography]`
- `backend/app/auth.py` — full rewrite (JWT verification + role dependencies)
- `backend/app/main.py` — remove old auth endpoints, add new `/api/auth/me`
- `backend/app/routers/films.py` — user_status join in list/detail, remove PATCH vu endpoint
- `backend/app/routers/users.py` — new router for user film status endpoints
- `backend/app/schemas/film.py` — UserFilmStatus type, update FilmListItem/FilmDetail
- `frontend/package.json` — add `@supabase/supabase-js`
- `frontend/src/lib/supabase.ts` — new Supabase client
- `frontend/src/context/AuthContext.tsx` — full rewrite
- `frontend/src/pages/AuthPage.tsx` — new (replaces LoginPage.tsx)
- `frontend/src/api/client.ts` — async getAuthHeaders via Supabase session
- `frontend/src/types/api.ts` — UserFilmStatus, update vu → user_status
- `frontend/src/components/films/FilmCard.tsx` — user_status.seen instead of vu
- `frontend/src/pages/FilmDetailPage.tsx` — new status endpoint for seen toggle
- `frontend/src/components/layout/Header.tsx` — user menu for authenticated users
- `frontend/src/App.tsx` — replace /login route with /auth
