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
| 15a | Supabase Auth + user roles + vu migration | ✅ DONE | JWT auth, user_profile, user_film_status, migrate film.vu |
| 15b | Personal tracking UI + Collection + Nav menu | ✅ DONE | Favorites/watchlist/rating/notes, /collection page, header dropdown |
| 15c | Tier-gated taxonomy access | ✅ DONE | Dimension gating by tier, filter limits, OR/NOT gating, upgrade prompts |
| 16a | Recommender: "Refine in Browse" button | ✅ DONE | Smart tag preselection from a film's tags, IDF-ranked, tier-aware |
| 16b | Recommender: Similar Films algorithm (in-DB) | ✅ DONE | IDF-weighted Jaccard across 9 dims + structural bonuses, on-demand SQL |
| 16c | Recommender: SimilarFilmsCarousel UI | ✅ DONE | Replace placeholder, "Why?" tooltips, tier-gated 3/6/12 results |
| 17a | Stats Dashboard — Quick / Financials / People / Taxonomy (MVP) | ✅ DONE | New /stats page, 4 tabs, tier-gated, single bulk endpoint |
| 17b | Production-country + franchise data prep, sidebar overhaul, Top 20 franchises | ✅ DONE | tmdb_collection + film_production_country tables, backfill scripts, sidebar reorg, exact franchise filter |

---

## Steps 1–11: Core Build (completed)

*(see git history for step details)*

## Step 12: Taxonomy restructure ✅

  Merging characters_type + character_context, cinema_type + cultural_movement, moving Disaster to
  themes and dialogs to cinema, adding sort_order-based grouping to 7 dimensions, adding new theme
  values (curse, game), renaming gang → team/group/gang.

---

## Step 13: Performance Optimization (Deployed) ✅

  Backend: pool_size 5→10, asyncio.gather() for 18 parallel queries in get_film().
  Frontend: React Query caching (staleTime 30s browse, 60s detail, Infinity taxonomy).
  Infrastructure: Render moved from Oregon → Frankfurt (10ms vs 150ms to Supabase Paris).

---

## Step 14: Advanced 'click on tag' behaviour ✅

  Frontend: TagFilter type (include/exclude/mode), 3 chip states (off/include/exclude), right-click
  exclude, AND/OR toggle. Backend: _not and _mode query params for all 10 dimensions.

---

## Step 15a: Supabase Auth + User Roles + vu Migration ✅

  Supabase Auth (email/password + Google OAuth), user tiers (free/pro/admin), auto-profile creation,
  per-user film status (seen/favorite/watchlist/rating/notes), film.vu migrated to user_film_status.

---

## Step 15b: Personal Tracking UI + My Collection + Nav Menu ✅

*(see git history for details)*

---

## Step 15c: Tier-Gated Taxonomy Access

Restrict taxonomy filter access based on user tier. Anonymous and free users see all dimensions but can only interact with a subset. Pro users get full access. This creates the core value proposition for upgrading.

---

## Step 16: Recommender Engine (in-DB)

Two complementary surfaces driven by the same taxonomy-based similarity:
- **Carousel** ("Similar Films" section on each film page) — passive, top-N algorithm-curated.
- **Button** ("Refine in Browse →" inside the same section header) — active, drops the user on /browse with the most distinctive tags pre-selected so they can iterate manually.

### Step 16d (later, no separate ticket) — Tuning loop

Manual rating of top-12 results on 10 reference films, adjust weights and bonuses iteratively. Optional admin debug view exposing per-dimension contribution to score.

---

## Step 17a: Stats Dashboard — MVP (Quick + Financials + People + Taxonomy)

*(see git history for details)*

---

## Step 17b: Production-country + franchise data prep, sidebar overhaul, Top 20 franchises ✅

Prep work originally scheduled before the Geography tab (still "Coming soon"), repurposed once it landed. Three loosely related streams:

### 1. New data layers

- **Migration `020_collection_and_production_country.sql`** — three new tables:
  - `tmdb_collection (collection_id PK, collection_name, poster_path, backdrop_path)` — franchise lookup keyed by TMDB collection id (joins from existing `film.tmdb_collection_id`).
  - `production_country (country_id, country_code UNIQUE, country_name)` — ISO 3166-1 alpha-2 lookup, lazy-populated.
  - `film_production_country (film_id, country_id)` — junction.
- **`tmdb_mapper.py`** — now exposes `tmdb_collection_name/poster/backdrop` and a new `production_countries_full: [{code, name}]` field alongside the existing ISO-code list (the latter kept for back-compat with EnrichmentPreview).
- **`db_inserter.py`** — new `_upsert_collection` and `_insert_production_countries` helpers wired into the ingestion pipeline (steps 21 & 22). `film_production_country` added to the junction-clear list so re-imports stay consistent.
- **Backfill scripts**:
  - `scripts/backfill_tmdb_collections.py` — `/collection/{id}` for every distinct id, upsert into `tmdb_collection`.
  - `scripts/backfill_production_countries.py` — `/movie/{id}` for each film, lazy-populate `production_country`, insert junction rows. `--force` re-fetches everything; default skips films already linked.

### 2. Sidebar filter overhaul

- "Location" → **Film Set Location** (rename only).
- **Language** dropdown removed from the browse sidebar; replaced with a new **Production Country** dropdown showing full country names (e.g. "France (212)") sourced from the new junction. Sits directly under Film Set Location.
- "Studio" → **Production Studio**, moved above Origin/Adaptation.
- Origin/Adaptation now sits at the bottom of that block.
- Backend: new `production_country` query param on `/api/films` joining through `film_production_country`/`production_country`. Counted toward the per-tier filter quota.
- Backend: new `/api/taxonomy/production_countries` special dimension returning `[{id, name, film_count}]` ordered by film count, `HAVING > 0` so empty entries don't appear.
- Frontend: `FilterState.production_country` plus URL ser/deser in `useFilterState.ts`, chip in `ActiveFilters.tsx`.

### 3. Top 20 franchises section

- Backend: new `top_franchises` block in `/api/stats/dashboard` (Quick Stats), `HAVING COUNT(*) >= 2` so single-film "collections" don't appear, ordered by count desc. Returns `{collection_id, name, count, poster_path, backdrop_path}`.
- Frontend (`QuickStatsTab.tsx`): horizontal poster row with rank badges and TMDB collection posters (via `tmdbImageUrl`), using cleaned-up names (trailing word *"Collection"* stripped).
- Cards link to `/browse?tmdb_collection_id=<id>&tmdb_collection_name=<name>&sort_by=year&sort_order=asc` — exact filter, no fuzzy text match.
- Backend: `/api/films` accepts a new `tmdb_collection_id: int | None` param matching `f.tmdb_collection_id` exactly.
- Frontend: `FilterState.tmdb_collection_id` (id) and `tmdb_collection_name` (cosmetic, used only for the chip label). Both serialized to URL. Active-filter chip displays `Franchise: <name>` and clears both fields when removed.

### 4. Stale-data fixes shipped along the way

- `films.py` `PUT /api/films/{id}` now keeps `film.color` in sync with the `cinema_types` taxonomy: removing the `black and white` tag flips `color` back to `TRUE` and the hero-section B&W badge disappears, and vice versa. Caught after manually correcting Claude tag mistakes (e.g. *Burn After Reading*) didn't propagate.

### Notes on data shape limitations

- TMDB has no overarching "Marvel Cinematic Universe" or "DCEU" collection — they're split into many smaller sub-franchises (*Avengers*, *Iron Man*, *Captain America*, *Justice League*, etc.). Cumulative MCU/DC counts therefore don't appear in the top 20.
