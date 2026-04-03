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