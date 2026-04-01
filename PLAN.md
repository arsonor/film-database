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
| 11 | Deployment + auth (Supabase + Render + Vercel) | 🔲 TODO | Admin auth, CORS from env, frontend auth context, deploy to cloud |

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

## Step 11: Deployment + Admin Auth (Supabase + Render + Vercel)

### Goal
Deploy the application publicly at a URL accessible from any device, with role-based access: public visitors get read-only browsing, admin (Martin) gets full editing capabilities.

### Architecture

| Layer | Local (dev) | Deployed (prod) |
|---|---|---|
| Database | PostgreSQL localhost:5432 | Supabase (free, 500 MB) |
| Backend | FastAPI localhost:8000 | Render Web Service (free) |
| Frontend | Vite dev server localhost:3000 | Vercel (free, static CDN) |

Single deployment. No separate "demo" app — one URL with auth-gated admin features.

### Sub-step 11a: Backend auth + deployment config

**New files:**
- `backend/app/auth.py` — `require_admin` dependency: reads `Authorization: Bearer <token>` header, compares to `ADMIN_SECRET_KEY` env var. Returns 401 if missing/invalid.
- `Procfile` — `web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

**Modified files:**
- `backend/app/main.py`:
  - CORS origins from env: `CORS_ORIGINS` (comma-separated), fallback `http://localhost:3000`
  - New `GET /api/auth/check` endpoint (requires admin → returns `{admin: true}`, else 401)
  - New `POST /api/auth/login` endpoint (accepts `{password}` body, compares to `ADMIN_SECRET_KEY`, returns `{token}` = the key itself)
- `backend/app/routers/films.py` — add `Depends(require_admin)` to: `POST /films`, `PUT /films/{id}`, `DELETE /films/{id}`, `PATCH /films/{id}/vu`, `POST /films/{id}/relations`, `DELETE /films/{id}/relations/{rid}`
- `backend/app/routers/add_film.py` — add `Depends(require_admin)` to: `GET /add-film/search`, `POST /add-film/enrich`
- `backend/app/routers/taxonomy.py` — add `Depends(require_admin)` to: `POST /taxonomy/{dim}`, `PUT /taxonomy/{dim}/{id}`, `POST /taxonomy/{dim}/merge`, `DELETE /taxonomy/{dim}/{id}`
- `.env.example` — add `ADMIN_SECRET_KEY`, `CORS_ORIGINS`

**Endpoint protection summary:**
- **Public (no auth):** all GET endpoints — `/api/films`, `/api/films/{id}`, `/api/films/search-local`, `/api/taxonomy/{dim}`, `/api/persons/*`, `/api/geography/*`, `/api/stats`
- **Admin (require_admin):** all POST/PUT/PATCH/DELETE + add-film workflow

### Sub-step 11b: Frontend auth + deployment config

**New files:**
- `frontend/src/context/AuthContext.tsx` — React context providing `isAdmin`, `token`, `login(password)`, `logout()`. Stores token in localStorage. On mount, calls `GET /api/auth/check` to validate stored token.
- `frontend/src/pages/LoginPage.tsx` — minimal login page at `/login`: single password field, calls `POST /api/auth/login`, on success stores token and redirects to `/browse`.

**Modified files:**
- `frontend/src/api/client.ts`:
  - `const BASE = import.meta.env.VITE_API_URL || "/api"` (env-based API URL for production)
  - New `getAuthHeaders()` helper: reads token from localStorage, returns `{Authorization: "Bearer <token>"}` or empty object
  - All write functions (POST/PUT/PATCH/DELETE) include auth headers
  - New `checkAuth()` and `loginAdmin(password)` API functions
- `frontend/src/App.tsx` — wrap in `<AuthProvider>`, add `/login` route to `<LoginPage />`
- `frontend/src/components/layout/Header.tsx`:
  - Import `useAuth` context
  - Wrap "Add Film" button and "Tags" button in `{isAdmin && ...}`
  - Add Login/Logout button (LogIn/LogOut icons from lucide-react)
- `frontend/src/pages/BrowsePage.tsx` — wrap FilmCard vu toggle in `isAdmin` check (pass `onToggleVu` prop only when admin)
- `frontend/src/components/films/FilmCard.tsx` — only render clickable eye icon if `onToggleVu` prop is provided; otherwise show nothing
- `frontend/src/pages/FilmDetailPage.tsx`:
  - Import `useAuth` context
  - Wrap all edit buttons (EditableTagSection edit mode, delete film button, EditableFinancials, AwardsTable edit) in `{isAdmin && ...}`
  - Seen/unseen toggle: functional only if `isAdmin`
- `frontend/src/pages/TaxonomyAdminPage.tsx` — redirect to `/browse` if `!isAdmin` (or show read-only view)
- `frontend/src/pages/AddFilmPage.tsx` — redirect to `/browse` if `!isAdmin`

### Phase C: Infrastructure setup & data migration (manual steps)

**C1. Export local database:**
```powershell
pg_dump -U postgres -d film_database --no-owner --no-acl -F c -f film_database_backup.dump
```

**C2. Supabase setup:**
1. Create account at supabase.com → new project → note the **direct connection** string (port 5432, Session mode)
2. Change scheme from `postgresql://` to `postgresql+asyncpg://` for SQLAlchemy
3. Import: `pg_restore -h <host> -p 5432 -U postgres.<ref> -d postgres --no-owner --no-acl film_database_backup.dump`

**C3. Render setup:**
1. Create Web Service → connect GitHub repo `arsonor/film-database`
2. Root directory: `.` | Build: `pip install -r backend/requirements.txt` | Start: reads `Procfile`
3. Environment variables: `DATABASE_URL`, `TMDB_API_KEY`, `ANTHROPIC_API_KEY`, `ADMIN_SECRET_KEY`, `CORS_ORIGINS`

**C4. Vercel setup:**
1. Import GitHub repo → root directory: `frontend` → framework: Vite
2. Environment variable: `VITE_API_URL=https://<render-app>.onrender.com/api`

**C5. Post-deploy verification:**
1. Public browsing works (poster grid, filters, film detail)
2. `/login` → enter admin password → admin UI appears
3. Can add film, edit tags, toggle seen, delete → all work
4. Logout → admin UI hidden, write API calls return 401

### Files summary

**New files (4):**
- `backend/app/auth.py`
- `Procfile`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`

**Modified files (11):**
- `backend/app/main.py`
- `backend/app/routers/films.py`
- `backend/app/routers/add_film.py`
- `backend/app/routers/taxonomy.py`
- `.env.example`
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/pages/BrowsePage.tsx` + `FilmCard.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/pages/TaxonomyAdminPage.tsx` + `AddFilmPage.tsx`