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
| 17d | Stats Dashboard — Geography tab (world map + set-place treemap) | 🔲 TODO | Production-country choropleth, country click → top films panel, set-place treemap (continent→country→city), country count stat card |

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

## Step 17c: Stats Dashboard — Taxonomy enhancements ✅

*(see git history for details)*

---

## Step 17d: Stats Dashboard — Geography tab (world map + set-place treemap)

### Goal
Replace the "Coming soon" placeholder with a fully interactive Geography tab. Two map visualisations side-by-side answering different questions: **where films were produced** (industry geography) and **where films take place** (set-place geography). Pro/Admin only — the existing tier gating in the Taxonomy tab is the model.

### Sections

#### 1. Stat cards row (top)

Three compact `StatCard`s:
- **Countries produced in** — distinct production countries with at least 1 film
- **Countries set in** — distinct set-place countries with at least 1 film
- **Most international film** — the film with the most production countries (e.g., "7 countries: The Lord of the Rings")

#### 2. World map — Production countries (choropleth)

A full-width interactive world map. Each country shaded by its film count using an amber scale. Hover → tooltip with country name + count. Click → right side-panel opens showing the **top 10 films co-produced by that country** (poster + title + year, sorted by `weighted_score DESC NULLS LAST`).

Legend: a horizontal color scale below the map ("1 — 50 — 500+ films") with non-linear bucketing because counts span 4 orders of magnitude (US has thousands, smaller markets have 1-5).

Countries with 0 films are shown in muted dark gray (not invisible — so the user can still see the world outline).

#### 3. World map — Set place countries (choropleth)

Same component, different data. Below the production map. Hover/click work the same way; click shows top 10 films *set* in that country.

The two maps are stacked vertically (not side-by-side) so each gets full width — small choropleths are unreadable.

#### 4. Set-place treemap (continent → country → city)

A Recharts `Treemap` showing the hierarchical breakdown of set-place data. Top-level rectangles = continents (sized by film count), each containing country rectangles, each containing city rectangles. Two clicks to drill down (default Recharts behaviour).

This complements the country map by adding the **city level** which isn't shown on a world map.

Click on a city rectangle → navigate to `/browse?location=<geography_id>` so the user can see those films.

### Data sources

**Already in DB (from Step 17b):**
- `production_country` (country_code = ISO alpha-2, country_name = English)
- `film_production_country` (film_id, country_id)

**Already in DB (existing):**
- `geography` (continent, country, state_city) — free-text English
- `film_set_place` (film_id, geography_id)

### Important: ISO code mapping for set-place

The production map already has ISO codes (`production_country.country_code`). The set-place data does **not** — `geography.country` is free-text. To put set-place data on a world map, we need to map those text names to ISO alpha-2 codes.

**Approach**: build a static mapping table in the backend `backend/app/data/country_name_to_iso.py` covering the ~80 most common country names that appear in the dataset (e.g., "United States" → "US", "France" → "FR", "South Korea" → "KR"). Names that don't match the table fall back to free-text lookup against `production_country.country_name` (case-insensitive). Unmatched countries are silently dropped from the choropleth (the treemap still shows them since the treemap doesn't need ISO codes).

Alternatively (cleaner long-term): add `country_code VARCHAR(2)` to `geography` and backfill it via a migration. Either approach works; the static map is faster to implement and good enough since the country names in `geography` are mostly standard.

**Decision for 17d**: ship with the static map (no schema change). If unmatched countries become a problem, do the migration in 17e or later.

### Backend changes

Extend `/api/stats/dashboard` payload, **`geography` block** (currently `null`):

```python
{
  "geography": {
    "production_countries": [
      {"iso": "US", "country": "United States", "film_count": 1842}
    ],
    "set_place_countries": [
      {"iso": "FR", "country": "France", "film_count": 312}
    ],
    "set_place_treemap": [
      {
        "continent": "Europe",
        "country": "France",
        "state_city": "Paris",   # or null at country level
        "geography_id": 42,
        "film_count": 89
      }
    ],
    "production_country_total": 78,
    "set_place_country_total": 95,
    "most_international_film": {
      "film_id": 521,
      "title": "The Lord of the Rings: ...",
      "country_count": 7,
      "countries": ["US", "NZ", "DE", ...]
    }
  }
}
```

**Two new endpoints** for the click-on-country interaction (not in the dashboard payload, fetched lazily):

```
GET /api/stats/films-by-country?type=production&iso=US&limit=10
→ [{film_id, title, poster_url, year, weighted_score}]

GET /api/stats/films-by-country?type=set_place&iso=FR&limit=10
→ [{film_id, title, poster_url, year, weighted_score}]
```

Both Pro/Admin only.

### Frontend changes

**Library choice: `react-simple-maps`** (~70 KB gzipped, declarative, React-native). Pairs well with a small world topojson file (~120 KB) hosted in `frontend/public/world-110m.json` for fastest load.

**New files:**
- `frontend/src/components/stats/WorldMap.tsx` — generic choropleth component. Props: `data`, `onCountryClick`, `colorScale`, `legendBuckets`.
- `frontend/src/components/stats/SetPlaceTreemap.tsx` — Recharts Treemap wrapper.
- `frontend/src/components/stats/CountryFilmsPanel.tsx` — the click-triggered side panel showing top-10 films for the clicked country.
- `frontend/src/lib/colorScale.ts` — helper for non-linear color buckets (matching the choropleth legend).
- `frontend/public/world-110m.json` — the topojson world map (one-time download, ~120 KB).

**Modified files:**
- `frontend/src/components/stats/GeographyTab.tsx` — replace `LockedTabPlaceholder` with full implementation, with internal tier check (Pro/Admin only — show LockedTabPlaceholder for everyone else).
- `frontend/src/types/api.ts` — add `GeographyPayload`, `ProductionCountryCell`, etc.
- `frontend/src/api/client.ts` — add `getFilmsByCountry()`.

### Tier visibility

The Geography tab moves from `coming_soon` to the full Pro/Admin gating. Same model as the existing Taxonomy tab:
- Anonymous + Free: see `LockedTabPlaceholder reason="upgrade"` or `"signup"` respectively
- Pro/Admin: see the full geography content

Update the tier resolution in `backend/app/routers/stats.py` accordingly — the `geography` block should be `null` for anonymous and free, populated for Pro and admin.

### Files summary

**Modified backend (2):**
- `backend/app/routers/stats.py` — populate `geography` block in dashboard for Pro/Admin, add 2 new endpoints.
- `backend/app/data/country_name_to_iso.py` (NEW) — static mapping table.

**Modified frontend (3):** `GeographyTab.tsx`, `types/api.ts`, `api/client.ts`.

**New frontend (4):** `WorldMap.tsx`, `SetPlaceTreemap.tsx`, `CountryFilmsPanel.tsx`, `lib/colorScale.ts`.

**New dependency:** `react-simple-maps` (~70 KB gzipped).

**New asset:** `world-110m.json` (~120 KB, served from /public).

### Out of scope (deferred)

- Schema migration to add `country_code` to `geography` table (the static mapping table is enough for now).
- Per-decade animation of the world map ("watch cinema spread across the globe"). Cool but expensive in code.
- Set-place city heatmap on the map itself (cities aren't on a choropleth; the treemap covers this).


