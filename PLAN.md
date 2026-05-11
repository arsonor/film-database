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
| 17c | Stats Dashboard — Taxonomy enhancements (% heatmap fix + 2 new heatmaps + per-person tags + cross-tab) | ✅ DONE | 5 sections: Categories % heatmap, cinema-movements heatmap, messages % heatmap, person filmography tag breakdown, atmosphere×category cross-tab |

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

*(see git history for details)*

---

## Step 17c: Stats Dashboard — Taxonomy enhancements

### Goal
Extend the Taxonomy tab with deeper analytics. Five additions, all Pro/Admin-only (mirrors the existing Taxonomy tab tier gating).

#### 1. Fix existing Category × decade heatmap → use percentages

The current heatmap shows raw film counts which inflates totals (a film tagged with 3 categories counts 3 times in a decade) and makes decades incomparable (the 1970s have more total films than the 1920s, so absolute counts always look heavier on the right side).

**New formula**: `count of films in (category C, decade D) / total films released in decade D × 100`.

This answers "what % of 1980s films were Drama?" instead of "how many genre tags were applied to 1980s Dramas?". The denominator is `COUNT(DISTINCT film_id) WHERE first_release_date IS IN decade`, **not** `SUM(category counts)` — we want the share of films that have this genre, not the share of genre-tags.

Frontend cell label changes from `45` to `12%`. Tooltip: "Drama · 1980s · 12% of decade (45 films out of 380)".

#### 2. New: Cinema movements × decade heatmap (count-based)

A second heatmap directly below the categories one, scoped to a curated subset of `cinema_type` values that have strong temporal patterns:

```
['silent', 'expressionism', 'hollywood golden age', 'neo-realism', 'noir',
 'new wave', 'new hollywood', 'neo-noir', 'black and white',
 'blockbuster', 'art house', 'franchise']
```

This is the only heatmap that **stays count-based** — because few films get a movement tag at all (most films aren't part of any movement), percentages would be misleading ("5% of 1960s films are New Wave" sounds small but is actually historically dominant). Counts make the eras visible.

Rows must be ordered by `sort_order` (chronological by movement era), not alphabetically, so the diagonal pattern of cinema history is visible.

Subtitle: "Number of films tagged with each movement, per decade. Use this to see when each movement dominated."

#### 3. New: Messages × decade heatmap (% within decade)

Third heatmap, all 18 message values, percentage-based (same formula as #1), with `HAVING decade_total >= 20` so we don't show empty cells for decades with too few films (1900s, 1910s).

Filter out any message value with `total_count < 5` across the whole DB (avoids showing rows that are nearly empty everywhere).

Subtitle: "% of films per decade conveying each message. Notice when feminist films emerge, when ecological themes appear..."

#### 4. New: Most common tags for a director / composer

An interactive widget that lets the user search-select a person (director, composer, or actor) and shows their characteristic tags as compact ranked lists.

**UX**:
- A role toggle (Director / Composer / Actor), default Director
- An autocomplete-search input listing only people with `≥ 3 films` in that role (avoids bloating the dropdown with people who appeared in one film)
- After selection: 4 ranked lists side-by-side or stacked
  - **Top 8 themes** (excluding "parent: sub" subtypes for cleanliness)
  - **Top 5 atmospheres**
  - **Top 5 character types**
  - **Top 3 messages**
- Each entry shows tag name + film count (e.g., "war (12)")
- A small subtitle: "Based on N films by {name}"
- A reset button to clear selection

**Ranking**: raw count for v1. We can add IDF-weighting later if it proves needed, but for popular themes like "social" and "war" raw count is already meaningful at the per-person level.

#### 5. Atmosphere × Category cross-tab heatmap

A compact heatmap (12 categories × ~23 atmospheres) showing the share of films in each genre that have each atmosphere. Reveals patterns like "Comedy → feel good", "Horror → disturbing/violent", "Drama → depressive/sad".

Formula: `films(category=C, atmosphere=A) / films(category=C) × 100`. So each row sums to roughly the average number of atmospheres per film in that genre (typically 1–3).

Subtitle: "% of films in each genre matching each atmosphere. A genre's signature mood profile."

Atmospheres ordered by `sort_order`. Categories sorted alphabetically.

### Tier visibility

All five additions live inside the existing **Taxonomy tab**, which is already gated to Pro/Admin. No new tier logic needed.

### Backend changes

Extend `/api/stats/dashboard` payload, **`taxonomy` block**, with new fields:

```python
{
  # existing fields kept (top_themes, category_distribution, top_atmospheres):
  "top_themes": [...],
  "category_distribution": [...],
  "top_atmospheres": [...],

  # CHANGED: shape kept, semantics swapped to %.
  "category_by_decade_heatmap": [
    {"category": "Drama", "decade": 1980, "film_count": 45,
     "decade_total": 380, "pct": 11.84}
  ],

  # NEW: cinema-types heatmap (count-based, curated subset)
  "cinema_movements_by_decade": [
    {"movement": "new wave", "decade": 1960, "count": 24, "sort_order": 207}
  ],

  # NEW: messages heatmap (% within decade)
  "message_by_decade_heatmap": [
    {"message": "feminist", "decade": 2010, "film_count": 18,
     "decade_total": 410, "pct": 4.39, "sort_order": 101}
  ],

  # NEW: atmosphere × category cross-tab
  "atmosphere_by_category": [
    {"category": "Comedy", "atmosphere": "feel good", "film_count": 120,
     "category_total": 480, "pct": 25.0, "atmosphere_sort_order": 101}
  ]
}
```

For the per-person tag breakdown, **new endpoint** (not in the dashboard payload, since user picks person interactively):

```
GET /api/stats/person-tags?person_id=<id>&role=<director|composer|actor>
→ {
  "person": {"person_id": 42, "name": "Akira Kurosawa", "film_count": 27},
  "top_themes": [{"name": "war", "count": 8}, ...],   # top 8
  "top_atmospheres": [{"name": "epic", "count": 6}, ...],   # top 5
  "top_characters": [{"name": "samurai", "count": 5}, ...],   # top 5
  "top_messages": [{"name": "humanist", "count": 4}, ...]   # top 3
}
```

Protected by Pro/Admin tier (return 403 otherwise). Use existing `tier_config` pattern.

Also a small **person search endpoint** for the autocomplete:

```
GET /api/stats/people-with-films?role=<director|composer|actor>&q=<search>
→ [{"person_id": 1, "name": "...", "film_count": 27}]
```

Returns top 30 matches by name ILIKE %q% with `HAVING film_count >= 3`. Pro/Admin only.

### Frontend changes

**Modified files:**
- `frontend/src/components/stats/CategoryDecadeHeatmap.tsx` — generalized to handle either count or percentage display, accept new prop `valueType: "count" | "percent"` and `getCellValue`/`getTooltip` callbacks. Rename to `DecadeHeatmap.tsx` (since it's now reused for 3 different dimensions). Existing import in `TaxonomyTab.tsx` updated.
- `frontend/src/components/stats/TaxonomyTab.tsx` — add the 5 new sections.
- `frontend/src/types/api.ts` — extend `TaxonomyPayload`, add `PersonTagsResponse`, `PersonSearchResult`.
- `frontend/src/api/client.ts` — add `getPersonTags()`, `searchPeopleWithFilms()`.

**New files:**
- `frontend/src/components/stats/PersonTagsWidget.tsx` — the interactive person→tags widget (role toggle + autocomplete + 4 ranked lists).
- `frontend/src/components/stats/AtmosphereCategoryHeatmap.tsx` — separate component (different axis structure: rows = categories, cols = atmospheres, both labels are short text).

### Files summary

**Modified backend (1):**
- `backend/app/routers/stats.py` — extend `/api/stats/dashboard` taxonomy block, add 2 new endpoints (`/api/stats/person-tags`, `/api/stats/people-with-films`).

**Modified frontend (4):** see above.

**New frontend (2):** see above.

### Out of scope (deferred)

- IDF-weighted ranking for per-person tags (raw counts ship in 17c).
- Tag co-occurrence force-directed graph (deferred, separate ticket if ever).
- Heatmaps for themes / atmospheres / characters as standalone (too many rows; the cross-tab and per-person widget cover this need indirectly).
- "Rare films/tag combinations" — redundant with the browse page's AND mode, which lets users build their own rare combinations interactively.

