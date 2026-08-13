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
| 21b | Taxonomy v2 — Backend | ✅ DONE | taxonomy_config + enricher rewrite, routers, schemas, tier config, review_tag, export_taxonomy |
| 21c | Taxonomy v2 — Frontend | ✅ DONE | Collapsible sub-dimension groups in sidebar, grouped Film page taxonomy, Add Film review |
| 22 | Taxonomy v2 — Deferred surfaces | ✅ DONE | Recommender weights, dashboard Taxonomy tab, 3 games, migration 027 drops motivation/message tables |
| 22.1 | Taxonomy tweaks (migration 028) | ✅ DONE | courtroom rename, submarine/spaceship, naval→military. Local + Supabase + deployed |

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

### 21b outcome (applied 2026-08-12)

- `taxonomy_config.py` rewritten: `VALID_GENRES_MAIN` (12) + `VALID_GENRES_SUB` (43) = `VALID_CATEGORIES` (55), all 7 lists verified **name-for-name and in order** against the live DB (55/40/29/22/96/59/25), motivations/messages deleted, `REFERENCE_EXAMPLES` re-tagged, plus a new `TIME_PERIOD_YEAR_RANGES` constant feeding the prompt.
- `claude_enricher.py`: 7 dimensions only; Genre section explains main vs sub and requires ≥1 main (a validation warning logs when none is present); Time Context section carries the year-range table + Time span/Seasons guidance.
- `films.py`: motivations/messages params, filters, detail queries and junction tuples removed; card/`top_categories` genre queries now use `c.sort_order < 200`; `dim_sort_table_map` gained `categories` and `time_periods` so the anonymous caps are enforced server-side. Detail-page tag lists now order by `sort_order` (they were alphabetical) so they match the sidebar grouping.
- Beyond the prompt's file list (all mechanical, needed to avoid breakage): `users.py` collection cards got the same `sort_order < 200` genre fix; `claude_batch_enrichment.py` would have raised `KeyError: 'motivations'` on the new `TAXONOMY_DIMENSIONS` — its prompt/validation were updated in step; `db_inserter.py` lost its two dead validation-map entries. `scripts/review_tag.py` also got `multi-sequence` → `chapters/multi-sequence`.
- `routers/taxonomy.py`: dissolved dimensions removed from all four sets; the `categories` add/rename branches now honour `sort_order` (previously ignored, which would have parked every new genre at the 999 default, outside the block layout).
- `export_taxonomy.py` de-staled: 7 dimensions, correct `ON CONFLICT (category_name) WHERE historic_subcategory_name IS NULL` target, main/sub genre split, sub-dimension group comments in both generated files, and `TIME_PERIOD_YEAR_RANGES`/`REFERENCE_EXAMPLES` preserved verbatim. Its generated seed was replayed against the local DB in a rolled-back transaction: valid SQL and fully idempotent (all `INSERT 0 0`).
- `tags_definition.md` reorganised into the 7 dimensions in display order, renames applied, moved tags relocated, `world-saving` deleted, merged stubs added. Open questions are flagged with `<!-- TODO Martin -->`: the `trafficking/fraud` wording (renamed but the definition still only covers fraud), and the undefined Time span tags / Seasons.
- Verified live against the migrated DB: `/api/taxonomy/themes` returns 96 tags in block order; `/api/taxonomy/messages` and `/motivations` → 400; migrated tags filter correctly (`themes=love` 1549, `categories=war` 642, `themes=philosophical` 1121, `atmospheres=dreamlike/surreal` 384); detail has no motivations/messages keys and shows sub-genres; cards show main genres only; anonymous caps hold (`categories=melodrama`, `time_periods=summer`, `atmospheres=poetic` all fall back to unfiltered while `Drama`/`WW2`/`violent` filter); `/similar`, `/stats`, `/stats/dashboard` and all 6 game setup endpoints return 200.

### 21c outcome (applied 2026-08-12)

- New `frontend/src/lib/taxonomyGroups.ts`: `MAIN_GENRES` + `isMainGenre`, `TAXONOMY_GROUPS` (block → label, with `parent` umbrellas), and a `groupItems` helper that splits any ordered list into consecutive sub-dimension runs. Verified against the live API: **every sort_order block present in all 7 dimensions has a label** — nothing falls back to the unlabelled path except `place_contexts` block 5 ("no particular"), which is intentionally label-less.
- **Sidebar is three-level collapsible** (Martin's refinement over the original prompt): dimension → sub-dimension → sub-sub-dimension, every level independently expand/collapse-able, each row carrying its tag count, an active-filter badge and a lock icon when the whole branch is tier-gated. Where a parent umbrella exists it becomes the collapsible sub-dimension and its blocks nest inside it: Genre → *Sub-genres* → 7 groups; Theme → *Human Relations* (4), *Personal / Inner conflict* (2), *Art, Sport & Entertainment* (3); Cinema Type → *Narrative techniques* (2). Everything **defaults to collapsed**; any branch holding an active filter is force-opened so a selection can never hide behind a collapsed header.
- **Film page taxonomy is grouped**: `EditableTagSection` takes an optional `taxonomyItems` prop and, in view mode, lays the film's tags out under their sub-dimension names in taxonomy order (edit mode stays flat). `FilmDetailPage` feeds it from the shared `useTaxonomy()` cache. Hero/mobile-hero badges show main genres only; the Genre section shows everything. Anonymous teaser now says "4 more dimensions".
- **Film page layout** (Martin's refinement): row 1 Time Period / Place / Geography (3-col), row 2 Genre + Theme (2-col — they carry the most tags), row 3 Atmosphere / Character / Cinema Type (3-col, same breakpoints as row 1 so the two align). Genre moved inside the `isAuthenticated` branch, so a full-width Genre section was added to the anonymous branch to avoid losing it for signed-out visitors.
- **Mobile-first sidebar pass** (the app is primarily aimed at phones): every control scales up below `lg` and tightens back to the previous density above it. Chips `min-h-38px / px-3 py-2 / text-sm` (from `px-2 py-1 / text-xs`), the touch-only ⓘ info button 16px in `p-1.5` (from 12px in `p-0.5`), sub-dimension rows `min-h-40px` with `mt-1.5` separation, dimension headers `min-h-48px / text-base font-semibold`, and all sidebar inputs/selects at `h-11 text-base` — 16px specifically, below which iOS Safari auto-zooms on focus. The shared `components/ui/select.tsx` `SelectItem` was bumped too, which benefits dropdowns app-wide.
- `types/api.ts` (7 dims + studios), `utils.ts` (singular labels), `tierAccess.ts` (mirrors backend `tier_config.py` exactly, incl. the new `categories: 199` / `time_periods: 99` anonymous caps), `AddFilmPage.tsx` (motivations/messages editors removed, singular labels).
- `tsc --noEmit` clean and `npm run build` succeeds. Project-wide grep shows no `motivations`/`messages` references left outside the Step 22 surfaces (`components/game/`, `components/stats/`, `SimilarFilmsCarousel`, `useDashboardStats`), which still compile untouched.
- Not visually verified in a browser — the Chrome extension was not connected during the session.

### Risks / notes

- Old bookmarked Browse URLs containing `motivations=` / `messages=` params are silently ignored (parser is key-driven) — acceptable.
- "Refine in Browse" (recommender, deferred) may emit motivations/messages URL params until Step 22; they are ignored by the new filter state — no crash.
- `/api/stats` `top_categories` and the list endpoint's category badges must restrict to `sort_order < 200` or sub-genres pollute the counts/cards.
- Order of migration statements matters (renames before moves where names overlap; 'political' merge is junction-migrate + delete, not rename).
- Deployment sequence: migrate local DB → 21b → 21c → full local test → `sync_to_supabase.ps1` + deploy backend/frontend together (old backend tolerates the new DB, so a short deploy gap is safe).

---

## Step 22: Taxonomy v2 — Deferred Surfaces (recommender, dashboard, games)

### Goal

Rewire the four surfaces Step 21 deliberately left untouched onto the 7 live
dimensions, then drop the dissolved tables. Everything below is applied to the
**local DB only** — Supabase is synced manually.

### 22a — Recommender (`services/recommender.py`)

- `_DIM_SQL` and `DIMENSION_WEIGHTS` down to the 7 live dimensions.
- **Weights rebalanced** for what the dimensions now contain:
  `themes 1.4` (was 1.3 — absorbed the 24 motivation tags and 9 message tags,
  now 96 tags and by far the most semantic), `atmospheres 1.3` (was 1.4),
  `categories 1.0` (was 0.7 — absorbed 43 sub-genres, which discriminate far
  better than the 12 main genres alone), `cinema_types 0.9` (was 1.0),
  `characters 0.9`, `place_contexts 0.6`, `time_periods 0.5` unchanged.
- **Latent bug fixed**: phases 1 and 3 unpacked their `asyncio.gather` results
  with hardcoded indices (`phase1[:9]`, `phase1[9]`, `phase3[11]`, …) that
  assumed exactly 9 dimensions. Dropping two dimensions would have silently
  read tag rows as the exclusion/director/studio/meta results. Now derived from
  `_N_DIMS = len(_DIM_KEYS)`.
- Similar-film cards: `c.historic_subcategory_name IS NULL` → `c.sort_order < 200`
  (main genres only, matching `FilmCard`).

### 22b — Dashboard Taxonomy tab (`routers/stats.py` + frontend)

- `message_by_decade_heatmap` → **`values_by_decade_heatmap`** and
  `message_by_movement` → **`values_by_movement`**, both driven by the theme
  block that absorbed the message dimension: *Values & Reflection*
  (`theme_context.sort_order` 200–299 — humanist, feminist, nostalgic,
  ecological, patriotic, anti establishment, traditionalist/way of life,
  philosophical, metaphysical). Same analytical intent, same cell shape
  (`theme`/`theme_sort_order` replace `message`/`message_sort_order`).
- New **`subgenre_by_decade_heatmap`** + a "Sub-genres" decade tab — the v2
  sub-genres are now first-class taxonomy and deserved a view. Sub-genres
  carried by fewer than 30 films are dropped (they would render as empty rows);
  rows are ordered by `sort_order` so the sub-dimension families stay contiguous.
- `CINEMA_MOVEMENT_NAMES` pruned: biopic / western / peplum / costume drama /
  black comedy / slasher / docufiction left `cinema_type` for Genre in 026 and
  would have returned nothing. Added `dogma`. `blaxploitation` (2 films) and
  `giallo` (4) are too sparse for a heatmap and were left out.
- **Main-genre restriction added** to `category_distribution`,
  `category_by_decade_heatmap` and `atmosphere_by_category` (they used
  `historic_subcategory_name IS NULL`, which after 026 matches *all* 55 genre
  rows — the pie chart and both heatmaps would have silently gained 43
  sub-genre rows). Same fix in the financials scatter's genre label and the
  personal "top genres among seen films" block.
- `PersonTagsResponse.top_messages` → **`top_genres` + `top_cinema_types`**
  (5 each). Cinema type turns out to be the sharpest filmography signature —
  Spielberg reads *blockbuster / CGI / new hollywood / franchise / popular
  culture*.

### 22c — Games (`routers/game.py` + `components/game/`)

- `DIMENSION_TABLE_MAP` and `_GUESS_DIM_LABELS` down to 7, reordered to the
  app-wide display order; labels aligned with `utils.ts` `dimensionLabel`.
- `n_dims >= 5` extracted to `MIN_TAGGED_DIMENSIONS`. Verified against the DB:
  all 4048 films have ≥5 of the 7 dimensions (11 have exactly 5, 350 have 6,
  3687 have all 7), so the eligibility gate is unchanged in practice.
- `_fetch_film_tags` orders by `sort_order` instead of alphabetically, so the
  Chain It tag list matches the sidebar/detail-page grouping.
- `components/game/dimensions.ts`: `GROUP_TITLES`, `TIME_PERIOD_GROUPS` and
  `timePeriodBucket` **deleted** — they were a stale second copy of the group
  labels. Replaced by `groupTitleFor()` / `groupBucket()` delegating to
  `lib/taxonomyGroups.ts`. The `time_periods` special case is gone for free:
  v2 lays that dimension out as blocks 0/1/2, so plain `Math.floor(so/100)`
  now yields the right group.

### 22d — Drop the dissolved tables

- `database/migrations/027_drop_dissolved_taxonomy.sql` — drops
  `film_motivation`, `film_message`, `motivation_relation`, `message_conveyed`,
  behind a guard that **aborts if any of the four still holds rows** (that would
  mean 026 was not applied and dropping would destroy real associations).
  Applied locally 2026-08-13.
- Removed from `schema.sql`, `models/__init__.py`, `tag_reviewer.py`,
  `db_inserter.py`, `verify_db.py`, `setup_db.py`, `seed_reference_films.py`,
  `test_enrichment_pipeline.py`, `export_taxonomy.py` and the leftover
  DEPRECATED comment block in `seed_taxonomy.sql`.
- `verify_taxonomy_v2.sql` section 2 now asserts the four relations are
  **absent** via `to_regclass` — a `count(*)` would fail at parse time on a
  dropped table.
- `scripts/data/reference_films_fallback.json` re-tagged to v2 from
  `taxonomy_config.REFERENCE_EXAMPLES` (it still carried the pre-026 tag names,
  so `seed_reference_films.py --offline` would have seeded a fresh DB with dead
  tags).

### Verification (2026-08-13, local DB)

- `verify_taxonomy_v2.sql`: **all checks PASS**, including the four dropped
  relations.
- Fresh-database path re-tested end to end on a scratch DB: `schema.sql` +
  `seed_taxonomy.sql` apply cleanly, 55 / 96 / 40 tags, no `film_motivation`.
- Backend boots; `/films/{id}/similar`, `/stats/dashboard`, `/game/daily`,
  `/game/random`, `/game/chain/daily`, `/game/chain/random`, `/game/guess/daily`,
  `/game/guess/random` all 200.
- `_build_taxonomy()` returns every block populated — 135 genre-decade rows,
  349 sub-genre-decade, 142 movement-decade, 97 values-decade, 285
  atmosphere×genre, 131 values×movement; `category_distribution` is 12 rows
  (main genres only).
- `/stats/person-tags` returns the 5 new blocks.
- `/game/chain/get-tags` returns the 7 dimensions in display + sort_order order.
- `tsc --noEmit` clean, `npm run build` succeeds.

### Notes / not done

- Not visually verified in a browser (Chrome extension not connected).
- `CLAUDE.md`'s "Classification Dimensions" section still describes the pre-v2
  9-dimension taxonomy, and `database/hovering_tag_info.md` still has
  MOTIVATIONS / MESSAGES sections. Both are hand-maintained source documents,
  left for Martin.
- Supabase not touched — sync + deploy backend/frontend together as usual, and
  run **026 then 027** in that order.

---

## Step 22.1: Taxonomy tweaks — migration 028

Three small taxonomy edits requested after Step 22 landed. Applied to local and
to Supabase on 2026-08-13, with the backend redeployed in between.

### Changes

1. **Genre** — `trial/judicial chronicle` renamed to **`courtroom`**. sort_order
   500 unchanged; a lookup-row `UPDATE` preserves all **179** film associations
   (`film_genre` references `category_id`, not the name).
2. **Place / Vehicles** — added **`submarine` (404)** and **`spaceship` (405)**
   after `ship` (403).
3. **Place / Buildings & institutions** — **`naval` removed**. All 38 films
   tagged `naval` were given `military` first (5 already had it, 33 gained it),
   so `military` went 132 → **165**. Deleting the lookup row cascaded the 38
   junction rows away. `castle` 208→207 and `hotel` 209→208 close the gap.

`place_context` goes 29 → **30** tags; `category` stays at 55.

The migration asserts, before the `DELETE`, that no film tagged `naval` is left
without `military` — it aborts rather than silently dropping coverage.

### Files touched

- `database/migrations/028_taxonomy_tweaks.sql` (new, guarded + post-assertions)
- `database/seed_taxonomy.sql` (both sections + the "29 tags" header)
- `database/verify_taxonomy_v2.sql` (place_context expected count 29 → 30)
- `backend/app/services/taxonomy_config.py` (`VALID_GENRES_SUB`,
  `VALID_PLACE_ENVIRONMENTS`)
- `backend/app/services/claude_enricher.py` — the Genre prompt used
  *"a courtroom drama gets `trial/judicial chronicle`"* as its worked example,
  which would have become self-contradictory; reworded to *"a trial-driven
  drama gets `courtroom`"*.
- `CLAUDE.md`, `database/tags_definition.md`,
  `database/Tags and taxonomy sort order.txt`,
  `database/Taxonomy dimensions & tags.txt` (+ a dated changelog entry)

`tags_definition.md` needed a real correction, not just a rename: `ship` was
defined as *"including all types of boat, and spaceship"*, which is wrong now
that `spaceship` stands alone. New/changed entries carry `<!-- TODO Martin -->`
markers for wording review, matching the 21b convention.

**No frontend change was required** — `taxonomyGroups.ts` only names the 12 main
genres and the block labels, and no component hardcodes a Place or sub-genre
tag name. Tier caps are unaffected (`place_contexts: 299` for free still means
Environments + Buildings; Vehicles stay above it).

### Verification (local)

- Migration ran in one transaction; `BEFORE: 179 / 38 / 132` →
  `AFTER: courtroom=179, military=165, place_context=30`.
- `taxonomy_config.py` re-checked name-for-name and in order against the live
  DB for all 7 dimensions (55/40/30/22/96/59/25) — exact match.
- `verify_taxonomy_v2.sql`: all checks PASS.
- Fresh-DB replay on a scratch database: `schema.sql` + `seed_taxonomy.sql`
  reproduce the same state (55 genres, 30 places, Vehicles block reads
  `car/bus, train, airplane, ship, submarine, spaceship`, no `naval`).
- Backend boots; `/films/{id}/similar`, `/game/daily`, `/game/guess/random`
  all 200.

### Deployment (2026-08-13)

Pushed → Render redeployed → `028_taxonomy_tweaks.sql` run against Supabase.
That order was chosen deliberately: neither `create_film` in `films.py` nor
`_insert_junction_by_name` in `db_inserter.py` auto-creates a missing lookup
row (both do a name lookup and skip on miss), so a config/DB mismatch can never
resurrect a deleted tag — the only cost of a gap is the Add Film flow silently
dropping a tag it can't resolve. Deploying first shrank that window to nothing.

Supabase after the migration reported the same BEFORE/AFTER numbers as local
(179 / 38 / 132 → courtroom 179, military 165, place_context 30);
`verify_taxonomy_v2.sql` all PASS; user data untouched (15 users, 1961
`user_film_status` rows, 265 game results).
