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
| 17c | Stats Dashboard — Taxonomy enhancements | ✅ DONE | Heatmaps, per-person tags, cross-tabs |
| 17d | Stats Dashboard — Geography tab (world map + set-place treemap) | ✅ DONE | Choropleth, country click panel, treemap, country count card |
| 18 | Game mode — "Tag It" | ✅ DONE | Daily + free play, narrow down films by tags, 3 lives, jokers, shareable scores |
| 19 | Game mode — "Chain It" + Game Hub + Stats page | ✅ DONE | Chain films through shared tags, game selection hub, unified stats + history |
| 20 | Game mode — "Guess It" | ✅ DONE | Eliminate films from a smart list by revealing tags, 3 lives, early guess risk/reward |
| 21a | Taxonomy v2 — DB migration + seed rewrite | ✅ DONE | Migration 026 applied locally: 9 dims → 7, 326 tags, 118 456 associations preserved |
| 21b | Taxonomy v2 — Backend | 🔜 NEXT | taxonomy_config + enricher rewrite, routers, schemas, tier config, review_tag, export_taxonomy |
| 21c | Taxonomy v2 — Frontend | ⬜ TODO | Sidebar with named sub-dimension groups, Film page taxonomy section, Add Film review |
| 22 | Taxonomy v2 — Deferred surfaces | ⬜ TODO | Recommender weights, dashboard Taxonomy tab, 3 games, drop motivation/message tables |

---

## Steps 1–20: Core Build + Features (completed)

*(see git history for step details)*

---

## Step 21: Taxonomy v2 — 7 Dimensions

### Goal

Implement the new taxonomy defined in the project document `Taxonomy dimensions & tags.txt` (source of truth, doc at the root of the project). The 9 dimensions become 7 (Motivations and Messages are dissolved into Genre, Theme and Atmosphere), tags are renamed/moved/merged/added, and every remaining dimension gains **named sub-dimensions** whose labels and tag ordering must be preserved and displayed. All existing tag↔film associations (4048 films) must be preserved through the migration.

The 7 dimensions (singular naming, in this display order): **Genre, Theme, Time Period, Place, Atmosphere, Character, Cinema Type**.

### Key design decisions

1. **Genre sub-genres are flat rows in `category`** with `historic_subcategory_name = NULL` (the legacy composite mechanism stays in the code but inert). Main genres occupy sort_order block 100–199; sub-genre groups occupy blocks 200–899. "Is a main genre" = `sort_order < 200`. Film cards and the detail-page hero show main genres only; the Genre taxonomy section shows everything.
2. **Sub-dimension names are encoded via sort_order blocks** (one block of 100 per group, consistent with the existing `Math.floor(sort_order/100)` separator logic) **plus a static label map**: new frontend module `frontend/src/lib/taxonomyGroups.ts` mapping `dimension → [{ block, label, parent? }]`. `FilterSection` renders these labels as group headers in the sidebar. No schema change needed for labels.
3. **`motivation_relation` / `message_conveyed` tables are emptied but NOT dropped** in Step 21. The recommender, dashboard and games still reference them; keeping empty tables lets those features degrade gracefully (empty contributions) until Step 22 updates them and drops the tables.
4. **Junction data migration** uses the pattern: ensure target row exists → `INSERT INTO target_junction SELECT ... ON CONFLICT DO NOTHING` → delete source lookup row (cascade cleans the source junction). Merged tags (mafia + organized crime → mafia/organized crime; odyssey + quest → odyssey/quest; dreamlike + surreal → dreamlike/surreal; message political → theme political) naturally deduplicate via ON CONFLICT.
5. **Enricher**: `taxonomy_config.py` is fully rewritten (7 dimensions, main vs sub genre lists, reference examples re-tagged), and the prompt gains the explicit Time Period year-range table from the new document.

### Scope split

- **21a — Database**: `database/migrations/026_taxonomy_v2.sql` (renames, moves, merges, new tags, sort_order rewrite, tag_description updates), full rewrite of `seed_taxonomy.sql`, verification script `database/verify_taxonomy_v2.sql`. Run locally first; sync to Supabase only after 21b is deployed-ready.
- **21b — Backend**: `taxonomy_config.py`, `claude_enricher.py`, `routers/taxonomy.py`, `routers/films.py`, `schemas/film.py`, `tier_config.py`, `scripts/review_tag.py`, `database/tags_definition.md`, plus `scripts/export_taxonomy.py` (see note below).
- **21c — Frontend**: `types/api.ts`, `lib/utils.ts`, new `lib/taxonomyGroups.ts`, `lib/tierAccess.ts`, `FilterSection.tsx`, `FilmDetailPage.tsx`, `AddFilmPage.tsx` (+ generic components that adjust automatically via `ARRAY_FILTER_KEYS`).

### Explicitly deferred to Step 22 (must not break in Step 21)

- `services/recommender.py` (still queries film_motivation/film_message → empty, contributes 0 to similarity)
- `routers/stats.py` + dashboard Taxonomy tab (message heatmaps go empty)
- `routers/game.py` + `components/game/dimensions.ts` (motivations/messages dimensions return no tags; games run on the 7 live dimensions)
- Dropping `motivation_relation`, `message_conveyed`, `film_motivation`, `film_message`
- Re-tuning tier sort_order gates after real usage (21b ships a first calibration)

### 21a outcome (applied 2026-08-11, local DB only)

- `database/migrations/026_taxonomy_v2.sql` ran in one transaction; all in-migration assertions passed.
- Final tag counts: Genre 55, Theme 96, Time Period 22, Place 29, Atmosphere 25, Character 59, Cinema Type 40 (326 total). The counts quoted in the Step 21a prompt (category 62, character 48) were estimates; these are the recomputed values and the ones 21b/21c must target.
- Associations: 119 756 film↔tag pairs before → 118 456 after, reconciling exactly (−442 discarded `world-saving` rows, −858 merge-overlap deduplications for mafia/organized crime, odyssey/quest, dreamlike/surreal and the two `political` tags).
- `motivation_relation` / `message_conveyed` / `film_motivation` / `film_message` are empty but present.
- Added a partial unique index `uq_category_name_no_subcategory ON category(category_name) WHERE historic_subcategory_name IS NULL` (in the migration and in `schema.sql`). Without it the table-level `UNIQUE (category_name, historic_subcategory_name)` uses NULLS DISTINCT semantics, so `ON CONFLICT` never fires for flat Genre rows and re-running the seed would duplicate all 55 of them.
- **`scripts/export_taxonomy.py` is now stale**: it still emits `motivation_relation` / `message_conveyed` seed sections, the old `ON CONFLICT (category_name, historic_subcategory_name)` target, and a `taxonomy_config.py` shape (`VALID_MOTIVATIONS`, `VALID_MESSAGES`, no main/sub genre split) that 21b replaces. Running it before 21b updates it would clobber both hand-written files. Fix it as part of 21b.

### Risks / notes

- Old bookmarked Browse URLs containing `motivations=` / `messages=` params are silently ignored (parser is key-driven) — acceptable.
- "Refine in Browse" (recommender, deferred) may emit motivations/messages URL params until Step 22; they are ignored by the new filter state — no crash.
- `/api/stats` `top_categories` and the list endpoint's category badges must restrict to `sort_order < 200` or sub-genres pollute the counts/cards.
- Order of migration statements matters (renames before moves where names overlap; 'political' merge is junction-migrate + delete, not rename).
- Deployment sequence: migrate local DB → 21b → 21c → full local test → `sync_to_supabase.ps1` + deploy backend/frontend together (old backend tolerates the new DB, so a short deploy gap is safe).

---

## Step 22: Taxonomy v2 — Deferred Surfaces (recommender, dashboard, games)

*(to be planned after Step 21 is validated)*
