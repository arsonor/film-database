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
| 23 | Enrichment pipeline hardening + prompt caching | ✅ DONE | Cacheable prompt prefix, Sonnet 5, prompt dedup, 3 Add Film bugs, TMDB genre seeds |
| 24 | Tag weighting foundation + re-tag harness | 🔜 NEXT | `weight` column, `defining` enricher output, retag_films.py — no production run |
| 25 | Re-tag execution — sample pass, then full run | ⬜ TODO | snapshot → generate → diff → apply over all 4048 films |
| 26 | Weight-aware surfaces | ⬜ TODO | Recommender weighting, uniqueness + differentiator queries, "defining only" browse, games |

---

## Steps 1–21: Core Build + Features (completed)

*(see git history for step details)*

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

---

## Step 23: Enrichment Pipeline Hardening + Prompt Caching

### Why now

The taxonomy is settled (v2 + tweaks). The next big job is **re-tagging the
~2500 films imported under the old thin prompt** (Steps 24–25). That job is
gated on the enrichment pipeline being cheap, correct and non-lossy — which it
currently isn't. This step fixes the pipeline itself and changes no taxonomy.

### The economics being fixed

Every enrichment call currently sends ~15,400 tokens of **byte-identical**
static content (system prompt + 7 dimension lists + the 42 KB
`tags_definition.md` + 3 reference examples + output skeleton) plus only ~400
tokens of film-specific data, and re-pays full input price on all of it.

Current published rates: **Sonnet 5 $2/$10 per MTok** (standard — the scheduled
September increase was cancelled), Haiku 4.5 $1/$5. Cache reads bill at 0.1×
input; 5-minute cache writes at 1.25×. Batch API is −50% and stacks with caching.

> **⚠ Superseded — see "Step 23 outcome" below.** Both the rates and the token
> estimate in this section are wrong. $2/$10 is an *introductory* Sonnet 5 rate
> ending **2026-08-31** (standard: $3/$15), and the static prefix measures
> **20 423** tokens on Sonnet 5's tokenizer, not ~15 400. Budget Step 25 from
> the outcome section's figures, not from the table below.

Projected cost of re-enriching all 4048 films:

| Setup | Est. |
|---|---|
| As-is (`claude-sonnet-4-6`, no cache, sequential) | ~$177 |
| Sonnet 5 + prompt caching | ~$64 |
| Sonnet 5 + caching + Batch API | **~$32** |

So Step 23 buys roughly a 5× cost reduction and, more importantly, makes
iterating on the prompt affordable enough to run trial passes over a sample
before committing to the full re-tag.

### Scope

**A. Cacheable prompt structure** (`claude_enricher.py`)

Split the prompt into a constant prefix and a per-film suffix, then mark two
cache breakpoints (system block, static prefix block). The static prefix is
built **once in `__init__`** rather than rebuilt per film — today the 42 KB
guide is re-concatenated on every call, and again on every retry.

This also fixes a recency problem: `## Film Metadata` currently sits ~15k tokens
*before* the output instruction. It moves to the end, immediately before the
final instruction.

**B. Model default** → Sonnet 5, via an env-overridable constant rather than a
hardcoded default, so the re-tagging runs can A/B Sonnet vs Haiku without a code
edit.

**C. Prompt dedup + calibration**

- Awards guidance appears twice (system prompt *and* the `### Awards &
  Nominations` block), near-verbatim. Source rules and the "[NEW] prefix" rule
  likewise appear twice. Keep one copy of each — the one in the taxonomy section,
  which carries the valid-value lists.
- **Remove `"Do not force tags. An empty list is better than a wrong tag."`** It
  pulls toward sparseness, and the observed failure mode on the bulk import is
  *under*-tagging, not over-tagging. Restraint is now enforced per-tag and far
  more precisely by `tags_definition.md`. Keep a narrow version scoped only to
  Geography / Source / Awards, where an empty result is genuinely often correct.
- **Confidence anchoring.** All three reference examples are canonical films and
  legitimately score 0.85–0.95 — the values aren't dishonest, but they're the
  only calibration signal in the prompt, so the model reproduces that band for
  obscure films too, which makes
  `get_low_confidence_films(threshold=0.6)` nearly inert. Fix by adding an
  explicit calibration scale to the system prompt and a one-line note that the
  examples are well-known films, rather than by faking lower numbers.

**D. Three Add Film bugs**

1. **Genre edits are silently discarded.** `ReviewScreen.handleSave` writes six
   dimensions back into `updatedEnrichment` but not `categories` — those go to
   `preview.categories` instead, while `create_film` reads genres *only* from
   `enrichment["categories"]`, which still holds Claude's original list. Adding
   or removing a genre on the review screen has no effect on what is saved. In
   the `enrichment_failed` path, `enrichment` is `{}`, so the TMDB genres shown
   on screen are saved as **zero genres**.
2. **New B&W films are recorded as colour.** `update_film` syncs `film.color`
   from the `black and white` cinema_type tag; `create_film` does not, and
   `TMDBMapper` always emits `color: True`. Migration 019 backfilled the
   historical rows but is a one-shot — every film added since is wrong again
   until re-run.
3. **`historic_subcategories` is dead weight.** Produced by the mapper, merged
   by `add_film.py`, ignored by `create_film`. Remove it end to end.

**E. TMDB genre seeds** — `map_tmdb_genre_to_category` computes a `note` for
War/Crime/Mystery/Animation/Documentary and a `subcategory` for Western, and
**nothing consumes either**. Under v2 those map onto real tags (`war`, `crime`,
`investigation`, `western` are Genre sub-genres; `animation` is a Cinema Type).
Wire them into the mapper output so they seed the review screen and, critically,
so the `enrichment_failed` fallback isn't empty.

**F. Cost instrumentation** — log `cache_read_input_tokens` /
`cache_creation_input_tokens` per call and refresh the stale pricing constants
in `claude_enrichment_runner.py` (currently "Sonnet 4" at $3/$15).

### Explicitly out of scope

- No taxonomy change of any kind.
- No re-tagging run — Steps 24/25.
- No change to `_validate_enrichment` semantics, the junction-insert logic, or
  any tier/filter behaviour.
- Merge policy for Step 25 (union vs replace vs cohort-scoped) stays undecided.

### Success criteria

- Two consecutive enrichments in one process report
  `cache_read_input_tokens ≈ 15k` on the second — the measurable proof the
  prefix is stable and the breakpoints are placed correctly.
- Editing a genre on the Add Film review screen changes what lands in
  `film_genre`.
- A film enriched with `black and white` is created with `film.color = FALSE`.
- With enrichment forced to fail, a TMDB "Animation"/"Western" film still
  arrives at the review screen with `animation` / `western` pre-filled.
- Cost per film, logged, drops to roughly a third of the pre-change figure.


---

## Step 23 outcome (applied 2026-08-14)

### Headline: the cache works

Two enrichments in one process, `claude-sonnet-5`:

| | call 1 | call 2 |
|---|---|---|
| `cache_creation_input_tokens` | 20 423 | 0 |
| `cache_read_input_tokens` | 0 | **20 423** |
| `input_tokens` (full rate) | ~210 | **210** |

**Cost per film: $0.0582 → $0.0125** (~4.7x). Extrapolated to 4048 films:
~$236 before, **~$51** now, **~$25** with the Batch API's -50% on top.

### Three things the Step 23 prompt did not anticipate

1. **`temperature=0.3` is a hard 400 on Sonnet 5** —
   `invalid_request_error: temperature is deprecated for this model`. Verified
   live before writing any code. Removed from all three call sites
   (`claude_enricher.py`, and both request builders in
   `claude_batch_enrichment.py`). Without this every call would have failed.
2. **PLAN.md's Sonnet 5 pricing is optimistic.** $2/$10 per MTok is an
   *introductory* rate ending **2026-08-31**; standard is $3/$15. A re-tag run
   in September costs ~$76 uncached-batch (~$38 batched), not ~$51/~$25.
   `MODEL_PRICES` carries a comment to flip when it lapses.
3. **The prefix is 20 423 tokens, not ~15 400.** Sonnet 5 uses the new
   tokenizer (~1.33x the old count for the same text), so the estimate measured
   on Sonnet 4.6 was low. Prefix content is unchanged.

Also: **Sonnet 5 runs adaptive thinking when `thinking` is omitted** (Sonnet 4.6
did not), and `max_tokens` caps thinking + response *together* — which would
have risked truncating the JSON and added unbudgeted output cost. The enricher
now sends `thinking: {"type": "disabled"}` explicitly, overridable via
`CLAUDE_ENRICHMENT_THINKING=adaptive`.

### What shipped

- **A.** `_static_prefix` built once in `__init__` (taxonomy + tag guide +
  examples + output skeleton); `_build_film_block()` per film, last, uncached,
  followed by the closing instruction. Two `cache_control` breakpoints. The
  JSON-retry rebuilds *only* the film block, so the cached bytes never drift.
  Cache usage logged on every call.
- **B.** `DEFAULT_ENRICHMENT_MODEL = os.getenv("CLAUDE_ENRICHMENT_MODEL",
  "claude-sonnet-5")`; `claude-sonnet-5` verified live against the installed
  SDK (anthropic 0.86.0). `.env.example` documents both new vars.
- **C.** Awards + Source blocks deleted from the system prompt (duplicated by
  the taxonomy section), `[NEW]` trimmed to a cross-reference, "Do not force
  tags" replaced with the Geography/Source/Awards-scoped version, confidence
  calibration bands added.
- **D1.** `categories` added to `updatedEnrichment` in `ReviewScreen.handleSave`.
- **D2.** `create_film` now mirrors `update_film`'s colour sync, after the
  junction loop.
- **D3.** `historic_subcategories` removed from `tmdb_mapper`, `schemas/add_film`,
  `add_film.py` and `types/api.ts`. The `category.historic_subcategory_name`
  column and its `IS NULL` guards are untouched, as specified.
- **E.** `_map_genres` now returns `(categories, cinema_types)` and routes the
  previously-dead `note`/`subcategory` fields into real v2 tags. Seeds are
  validated against `VALID_CATEGORIES` / `VALID_CINEMA_TYPES` at import.
- **F.** Per-model price table (`# Rates verified 2026-08-14`) with cache
  read/write multipliers; `ClaudeEnricher.usage_totals` accumulates real token
  counts; the runner prints a running total and cache hit-rate.

### Verification

- Cache proof above; prompt integrity confirmed (all 7 dimension lists, Genre
  main/sub rules, year-range table, tag guide, `courtroom`/`spaceship` present;
  **no film-specific leakage** into the prefix).
- TMDB seeds: `Western -> [Historical, western]`, `War+Drama -> [Historical,
  Drama, war]`, `Crime+Mystery+Thriller -> [Thriller, crime, investigation]`,
  `Animation -> cinema_types=[animation]`, `Documentary` not duplicated.
- D1+D2 exercised against the local DB: edited genres (`Drama`, `courtroom`)
  reach `film_genre`, and `film.color = FALSE` for a `black and white` film.
- `grep historic_subcategor` returns only the `category` column references.
- Backend imports clean; `tsc --noEmit` clean; `npm run build` succeeds.

### Residual gap (not fixed — out of scope)

A TMDB film whose only genres are `Animation` and/or `Family` still seeds
**zero** categories, because both map to `None` in `GENRE_TO_CATEGORY`. It does
get `animation` as a cinema type. Closing this means editing
`GENRE_TO_CATEGORY`, which Step 23 forbids.

---

## Step 24: Tag Weighting Foundation + Re-tag Harness

### Decision record

The v2 taxonomy moved, merged or created enough tags that a tag-by-tag backfill
of the 38 zero-association tags via `review_tag.py` was rejected as too slow and
too narrow. **The whole library gets re-tagged from scratch**, and the run is
used as the opportunity to introduce **tag weighting**.

Martin's observation from playing Tag It: the library is systematically
*under*-tagged, and for the games over-tagging is the cheaper error. But
over-tagging degrades the recommender — Jaccard similarity gets noisier as tag
sets grow, and IDF only partly compensates. Weights resolve the tension: **tag
generously, then weight the recommender toward defining tags only.**

### Why two levels, not percentages

The original idea was a 0–100% score per tag. Rejected for v1 on the evidence
already in this project: every confidence score produced under the old prompt
clustered at 0.85–0.95, which is exactly why `get_low_confidence_films` was
inert. Fine-grained numeric self-assessment is not something to build a
recommender on. Coarse ordinal judgement is reliable; **defining vs secondary**
is it.

The column is `smallint` (100 = defining, 50 = secondary, NULL = unscored
legacy), so a third level or true percentages need no migration later — just a
re-run.

Second-order benefit, and possibly the main one: **asking for a defining subset
should make tagging more generous, not less.** It gives the model somewhere to
put "this applies but isn't central", which is the judgement that currently
makes it drop the tag entirely. The under-tagging problem and the weighting
feature have the same fix.

### What Claude is asked for, and what is computed

Two distinct things that were conflated in early drafts of this plan:

- **Defining tags** — a per-film, absolute judgement made by Claude: *would
  someone describing this film in two sentences mention this?* Roughly **20–25
  tags per film**, 30–50% of the total assigned.
- **Minimum identifying set** — the **3–4 tags that suffice to isolate the film**
  among 4048. A *derived subset* of the defining tags, computed in SQL in Step
  26. Never requested from the model: it is a relative property depending on the
  whole library, and a model seeing one film at a time would confabulate it.

Martin's worked examples are the second kind. Validated against the real v2 tag
lists (2026-08-14):

| Film | Defining / total | Minimum identifying set | Differentiator |
|---|---|---|---|
| 2001: A Space Odyssey | 25 / 51 (49%) | AI/technology, alien contact, contemplative/meditative | contemplative (strong) |
| La Haine | 25 / 46 (54%) | immigration, trio, black and white, set: Paris | immigration |
| Mulholland Drive | 23 / 45 (51%) | art: cinema, disturbed/madness, neo-noir | art: cinema ≈ neo-noir |

2001's identifying set is a subset of its 25 defining tags; `philosophical` and
`space` are equally defining but add no discriminating power. The full defining
lists live in the Step 24 prompt and go into `REFERENCE_EXAMPLES` verbatim —
Martin hand-validated them, and they are the calibration standard for all 4048
films.

Because all three are unusually dense canonical works, ~50% is an **upper**
bound, not the expected mean. The prompt states 30–50%; the sample pass
recalibrates it.

Two further patterns from the exercise, both worth preserving: **Time Period is
rarely defining** unless the period is the subject (La Haine's `single day` is
structural and counts; Mulholland Drive's `2000-2010's` is background and does
not), and **Genre skews secondary**.

Two rules that fall out of the identifying sets, both **query-side, not
prompt-side**: main genres are excluded from identification (only 12 of them, so
they carry no discriminating power — but they stay weighted, because the
recommender wants to know whether a film is primarily or incidentally a comedy),
and **diegetic `film_set_place` entries join in as pseudo-tags** (La Haine's
`set: Paris`). Neither needs a schema or enrichment change.

### Guardrails agreed for the run

1. **Snapshot tables** `<junction>_pre_retag` for all seven junctions, plus a
   `pg_dump`. Queryable rollback, so the diff is plain SQL.
2. **Sample pass first** — ~40 films Martin knows well, iterated until the
   definitions behave. At ~$0.013/film a full pass costs about $0.52, so the
   definitions can be tuned repeatedly before committing; the constraint is
   review time, not money.
3. **Time Period "Years & eras" is preserved.** The only sub-dimension Martin
   hand-corrected. Predicate: `time_context.sort_order < 100`. Time span and
   Seasons (≥ 100, currently zero associations) are accepted from the re-tag.
4. **Showing Claude the current tags was considered and rejected.** Models shown
   an existing answer ratify it — the thin tag set would come back with two or
   three additions and almost no removals, re-introducing the exact anchor Step
   23 removed. The known chronological period *is* injected into the film block,
   because it is factual context rather than an interpretive answer, and it
   genuinely helps Character/Place/Cinema Type.

### Decisions

- **`ghost/spirit` stays undefined, deliberately.** Martin confirmed the tag
  should cover mental projections and hallucinations of the dead, not only
  literal ghosts. Adding a definition would narrow it. Do not "fix" this later.
- **Derived tags** (`DERIVED_TAGS`: `franchise`, `no particular`) are computed
  from data, never model-assigned — and their rules are deliberately
  asymmetric: `franchise` is insert-only (a missing TMDB collection id is not
  proof a film stands alone, so absence is a loss-review signal), while
  `no particular` is inserted *and* removed (another place tag's presence is
  proof by definition). Union's no-delete rule protects model judgements;
  derived values are exempt. Do not harmonise the two.

### Scope of Step 24 (build only — no production run)

- **Migration 029**: `weight smallint` on the seven junctions + partial indexes
  for `weight = 100`.
- **Enricher**: a `defining` key in the output, a prompt section defining the
  two-sentence test, and an optional `extra_context` on `_build_film_block`.
  The Add Film path keeps working unchanged.
- **`scripts/retag_films.py`**: four separate commands — `snapshot`,
  `generate`, `diff`, `apply`. Sourced from the **database**, not
  `resolved_films.json`. Reuses `ClaudeEnricher`'s cached prefix rather than
  forking the prompt.
- **`scripts/claude_batch_enrichment.py` is deleted.** Its selection model
  (diff `resolved_films.json` against `enriched_films.json`) is structurally
  wrong for re-tagging — every film to re-tag is already in the "done" ledger,
  so `--submit` would find nothing. Its prompt is a pre-Step-23 fork with no tag
  guide at all. Only the Batch submit/status/collect plumbing is worth keeping,
  and that ports into `retag_films.py`.

### Apply-time merge policy

**Full replace on the seven tag dimensions**, with two exceptions:

- Time Period `sort_order < 100` rows are preserved.
- **Awards, Source and Geography are NOT applied.** The enricher still returns
  them and they are kept in the JSON for later use, but `film_set_place` feeds
  the Step 26 uniqueness work and awards may have been hand-corrected. Re-tag
  touches tags only.

### Success criteria

- `defining` validates as a subset of the tag lists; a violation is dropped and
  logged, never written.
- `generate` on 3 films shows a cache read of ~20.4k on calls 2 and 3.
- `diff` on those 3 films produces a per-tag and per-film report without
  touching the database.
- `apply --dry-run` reports the same numbers as `apply`, and `apply` on a single
  film sets `weight` on every row it writes.
- Add Film still works end to end, and its saved rows also carry weights.

### Verification (2026-08-19 — step complete)

- **Migration is `030_tag_weight.sql`, not 029** — `029_character_subdimensions.sql`
  already existed, so the numbering shifted by one. Applied to the local DB:
  `weight smallint` + CHECK + partial `weight = 100` index on all seven
  junctions; all 35,553 existing `film_theme` rows (and every other junction)
  are NULL. Mirrored into `schema.sql`.
- `snapshot` created all seven `_pre_retag` tables with exactly matching row
  counts (film_genre 23,090 · film_theme 35,553 · film_technique 10,801 ·
  film_character_context 20,321 · film_atmosphere 16,003 · film_period 4,571 ·
  film_place 8,150) and printed the pg_dump + restore procedures.
- `generate --all --limit 3` (Inception, LOTR 1–2; reference films auto-excluded
  by film_id 1/2/3): call 1 cache **write 21,886**, calls 2–3 cache **read
  21,886** each. The prefix grew from ~20.4k to ~21.9k tokens because of the
  `defining` additions (three examples + skeleton + prompt section). Validator
  fired live: an invalid `epic` cinema_type and its `defining` copy were dropped
  and logged, never written.
- **Observed defining ratio on the 3 test films: 40% / 50% / 57% (48.8%
  overall)** — at or just above the top of the provisional 30–50% band, which is
  consistent with these being dense canonical blockbusters. No prompt adjustment
  made; Step 25's sample pass judges it on ordinary films.
- Validator hand-tests: `defining` with an out-of-list tag → dropped + logged;
  `defining` missing entirely → normalised to the empty 7-dim shape;
  `defining` as a list → reset; `_empty_enrichment` carries the empty shape.
- `diff` produced `diff_report.md`/`.json` (cold-start section, 0 alarms,
  per-tag/per-dimension tables, weight distribution, movers, Time Period check
  clean) with the DB untouched. For a partial scope the per-tag counts are
  *projected library totals* (global before ± scope gains/losses), so alarms
  stay meaningful on sample runs.
- `apply --film-id 4` dry-run and `--commit` reported identical numbers
  (45 deleted / 56 inserted = 23 defining + 33 secondary); every written row
  carried a weight; the film's `sort_order < 100` period row (2000-2010's) was
  preserved with its legacy NULL weight; its 11 awards and 4 film_set_place
  rows untouched. Restored from `_pre_retag` and confirmed exact (EXCEPT-based
  set equality in both directions).
- Add Film end to end (create_film via ASGI with a `defining`-carrying
  enrichment): defining tags saved at weight 100, secondary at 50,
  `film.color = FALSE` synced from `black and white`. `update_film` writes NULL
  weights by design (a manual edit carries no defining judgement).
- `scripts/claude_batch_enrichment.py` deleted after porting its
  submit/status/collect plumbing into `retag_films.py --batch*`; the installed
  SDK (0.86.0) supports the 1-hour cache TTL, which the batch path uses.
  `MODEL_PRICES` + cost helpers moved to `scripts/_pricing.py`, imported by both
  the runner and the re-tag script. Backend imports clean.
- Note for Step 25: `scripts/data/retag/enriched.jsonl` currently holds the 3
  verification films — delete it (or rely on the fact that `apply` is scoped to
  the JSONL you generate) before starting the real sample pass. The TMDB payload
  cache under `scripts/data/retag/tmdb/` is worth keeping.

### Step 24.1 — Definition fixes + union apply mode (2026-08-20, complete)

Fixes driven by the three-film sample diff; no production run, nothing applied.

- **Prompt**: restraint gates removed (philosophy block rewritten around "the
  weighting step records centrality", sub-genre and Themes gates relaxed, the
  named film dropped from the defining/secondary example). `franchise` is no
  longer model-assigned — `DERIVED_TAGS` in `taxonomy_config.py`, filtered from
  the prompt, stripped at debug level by the validator, derived at apply time
  from `film.tmdb_collection_id` (insert `weight NULL`; never deleted — absence
  of a collection id goes to the loss review as a `(derived)` signal).
- **tags_definition.md**: six new definitions (witch/wizard, super hero,
  elderly, sorcery, curse, violent), `no particular` moved under `### None` and
  made exclusive (validator enforces it too), Environments scope lead-in,
  `fight` decoupled from relational framing, `spy` covers corporate espionage,
  `gritty/realistic`/`realism` disentangled, franchise entry deleted.
- **Apply is now union by default**: insert gains with weights, update weights
  on re-proposed existing tags, delete nothing; existing tags the model did not
  propose keep `weight NULL` (never a fake 50). Removals are grouped by tag in
  `loss_review.md` and approved per tag via `apply --commit --remove-tag
  DIM:TAG` (scope-limited, one transaction). `--mode replace` retained. Diff
  gained in-scope before/after columns and sorts by in-scope movement when the
  scope is under 200 films.
- **Audit (report only)**: 91 of the 287 films tagged `no particular` also
  carry another place tag — the old pipeline made the same mistake. Cleanup
  migration is Martin's call.
- **Measured prefix delta: +818 tokens** (21,886 → 22,704; +3.7%), above the
  +320 estimate but under the +1000 stop threshold. ≈ +$0.17 across a 4048-film
  cached run at Sonnet 5 intro rates.
- **Three-film re-run**: `no particular` gone from all three (the model still
  emits it; the validator guard drops it every time). sorcery/curse/witch-wizard
  back on both LOTR films; supernatural retained; `gritty/realistic` no longer
  on the fantasy films; `mountains` back on Inception; franchise absent from
  model output. Still missing: `fight`/`spy` on Inception and `beach`
  (Inception) — the definition changes did not move the model on those. Genre
  mean 6.33 → 6.67 (baseline 9.67): the sub-genre gate relaxation recovered
  little. Defining share 46.5% overall; Genre (65%) and Cinema Type (63%) sit
  above the 30–50% band. Union dry-run: 78 gains, 89 weight updates, 30-tag
  loss review, nothing applied.

### Step 24.2 — Genre gate, stranded tags, derived `no particular` (2026-08-20, complete)

- **Duplicate Genre gate fixed**: `tags_definition.md` line 8 still carried the
  strict sub-genre rule 24.1 had relaxed in the taxonomy section; both entered
  the same prompt and the guide is framed as authoritative. The sweep found
  exactly one more dimension/group-level gate — the Time span lead-in
  ("Applied only when … a defining trait") — rewritten to route centrality
  through the defining marking. Everything else matching the gate phrases is
  per-tag precision, left alone (psychological, cityscape, ordinary,
  outcast/misfit, art house). The Vehicles lead-in is a threshold definition,
  not a gate.
- **`fight` cross-pointer experiment (on Atmosphere `violent`): negative** for
  its target case. `fight` returned on both fantasy films but still not on the
  espionage film — the model even emitted `spy` as a *Theme* there (invalid,
  stripped), so it sees the espionage content and classes it differently. Per
  the step: no more cross-pointers; whether `fight`/`spy` warrant a taxonomy
  move is Martin's later call. Union mode never removed either.
- **`no particular` is now derived** (second entry in `DERIVED_TAGS`): out of
  the prompt's Valid lists (filter generalised to all dimensions), stripped
  from model output, entry deleted from the guide, D1 exclusivity guard kept
  as a now-unreachable invariant. Derivation (zero place rows → insert weight
  NULL; any other place tag → remove it) implemented once per surface:
  `sync_no_particular_place` in `films.py` (create + update) and
  `_derive_no_particular` in `retag_films.py` (both apply modes).
- **Migration `031_no_particular_cleanup.sql` written but NOT run** (PROMPTS
  says 030; that number was already taken by tag_weight). Dry-run SELECT:
  **91 rows would be deleted** of 287; **17 films have zero place tags**
  (reported only — inserting for them is Martin's separate decision).
  Awaiting Martin's approval; local DB only.
- **Re-run (films 4/5/6)**: prefix delta **−11 tokens** vs 24.1 (22,704 →
  22,693, measured cache_write). Genre mean **6.67 → 7.00** (baseline 9.67);
  `war` returned on Fellowship, `chase/escape` on Two Towers; the espionage
  film's spy/crime/odyssey-quest still declined. `no particular` absent from
  all validated output. Defining share: Genre **65% → 57%** (falling toward
  the band as its count recovers), Cinema Type 62%, overall 46.4%. Zero
  alarms, zero Time Period violations. Union dry-run: 73 gains, 91 weight
  updates, 28-tag loss review, nothing applied.
- **Step 25 cost must be recomputed from this pass — output tokens now
  dominate (~73% of per-film cost).** Warm-cache per film ≈ 550 input + 22.7k
  cache-read + ~1,500 output ≈ **$0.021/film** at Sonnet 5 intro rates →
  ≈ $84 real-time / ≈ $42 via Batch API for 4048 films. At standard $3/$15
  (from 2026-09-01): ≈ $0.031/film → ≈ $127 / ≈ $63. Step 24's $0.013/film
  figure is stale.

---

## Step 25: Re-tag Execution

Runs the Step 24 harness for real. No new code beyond fixes the sample pass
exposes.

1. `snapshot` + `pg_dump`.
2. `generate --sample` on Martin's ~40 films — including films he considers
   *well* tagged today, plus structural edge cases (a silent film, a
   documentary, an animation, an anthology, something obscure with a thin TMDB
   overview). The failure mode invisible otherwise is the re-tag **degrading**
   recent good work. The three reference films are excluded by default. At
   ~$0.013/film a full 40-film pass costs ~$0.52, so iteration is free — the
   real budget is review time. `--sample-subset 15` iterates on a core group
   first.
3. Review the diff. Tune `tags_definition.md` and the prompt. Repeat.
4. `generate --all --batch` once the sample is satisfying.
5. `diff` → read the aggregate report **before** applying anything.
6. `apply`.

### The alarm signals in the diff

Tags are bucketed by their **before** count, because one rule cannot serve all
of them — the ~38 tags from migration 026 start at zero, so any naive growth
test fires on every one, and ratios are meaningless on small numbers.

- **Cold start** (before < 10): growth is the goal. Reported, not alarmed —
  except above ~800 films, which means the definition is far too loose.
- **Sparse** (10–49): reported only.
- **Established** (≥ 50): alarm on losing **>50%** of its films, or gaining
  **>2.5x and more than 100 films**. `fight` at 1341 going to 4000 must be
  caught before the DB is touched, not after.

And one health check on the weights: the defining share should land in the
**30–50%** band. Above 70% the distinction has collapsed; below 15% it is
over-strict. Both thresholds are provisional — the three reference films sit at
49/54/51% and are denser than average, so the sample pass is what actually
calibrates this.

The report leads with **cold-start coverage**, since "did the 38 new tags get
populated, and sensibly?" is one of the two questions the exercise exists to
answer.

### Cost and timing

~$25 batched at the introductory rate, ~$38 after it lapses on **2026-08-31**.
Not enough to rush the merge decision, but if the sample pass converges quickly
there is ~$13 in running before month end.

### Deferred to Step 26

Recommender weighting, the uniqueness/differentiator queries, a "defining only"
browse toggle (`fight` drops from 1341 films to perhaps 150 — a query an LLM
chat cannot answer verifiably and the sidebar can), and game integration.

Also deferred: a possible **adjudication pass** over just the films whose diff
is extreme, showing both versions and asking for a decision. ~200 films, not
4048 — and only worth building once the diff report exists.
