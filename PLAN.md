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

### Goal
New `/stats` page accessible from header navigation. Showcase the depth of the database with charts and rankings beyond what the browse-by-tag interface can convey. Tier-gated to drive upgrades.

### Tier visibility model

| Tier | Quick Stats | Geography | Financials | People | Taxonomy |
|---|---|---|---|---|---|
| Anonymous | ✅ (no seen/unseen) | 🔒 "Coming soon" | 🔒 "Sign up free" | 🔒 "Sign up free" | 🔒 "Sign up free" |
| Free | ✅ | 🔒 "Coming soon" | ✅ | 🔒 "Upgrade to Pro" | 🔒 "Upgrade to Pro" |
| Pro / Admin | ✅ + personal stats | 🔒 "Coming soon" (still gated/"soon") | ✅ | ✅ | ✅ |

Note: **Geography is `coming_soon` for everyone** in 17a (placeholder tab with "Coming soon" message). The world map / set-place treemap arrives in a future step.

### Navigation
- New `/stats` route
- Header link "Stats" added to main nav (visible to everyone, including anonymous), it's the 'Dashboard' presently marked as 'Soon' to unlock
- URL-driven tabs: `/stats?tab=quick|geo|financials|people|taxonomy` (default = quick)

### Architecture
- **Single bulk backend endpoint**: `GET /api/stats/dashboard?tier=<auto-from-token>` returns all data for tabs the user has access to. Locked tabs return `null` placeholders so the frontend can render the lock screen without an extra request.
- **Personal stats sub-payload**: `personal_stats` field is populated only for logged-in Pro/Admin users.
- **React Query** caching: `staleTime: 5 minutes` on the dashboard query (data doesn't change often).
- **Single page, internal tabs**: shadcn/ui `Tabs` component, no separate routes.

### Backend: `GET /api/stats/dashboard`

New router file `backend/app/routers/stats.py` with one endpoint that runs queries in parallel via `asyncio.gather()` (same pattern as `get_film()`).

Response shape (tier-aware — fields are `null` when locked):

```python
{
  "tier": "free",  # echoed back for frontend convenience
  "quick": {
    "total_films": 4027,
    "total_directors": 1240,
    "total_actors": 8532,
    "total_composers": 412,
    "by_decade": [{"decade": 1920, "count": 12}, ...],
    "duration_distribution": [
      {"bucket": "<60", "count": 5},
      {"bucket": "60-89", "count": 234},
      {"bucket": "90-119", "count": 1840},
      {"bucket": "120-149", "count": 1120},
      {"bucket": "150-179", "count": 380},
      {"bucket": "180+", "count": 193}
    ],
    "color_by_decade": [
      {"decade": 1920, "color": 1, "bw": 11},
      {"decade": 1930, "color": 3, "bw": 45},
      ...
    ],
    "top_studios": [{"name": "Warner Bros", "count": 187}, ...],  # top 20
    "most_awarded_films": [
      {"film_id": 42, "title": "Parasite", "poster_url": "...", "year": 2019, "wins": 14, "nominations": 38}
    ],  # top 20
    "by_source_type": [
      {"source_type": "original screenplay", "count": 2310},
      {"source_type": "novel", "count": 580},
      ...
    ]
  },
  "geography": null,  # always null in 17a ("Coming soon")
  "financials": {  # null for anonymous
    "top_grossing": [{film_id, title, poster_url, year, revenue}, ...],  # top 20
    "top_budgets": [...],  # top 20
    "most_profitable": [{..., budget, revenue, ratio}, ...],  # WHERE budget > 1_000_000, top 20
    "avg_budget_by_decade": [{"decade": 1980, "avg_budget": 18_500_000, "film_count": 67}, ...],
    "budget_revenue_scatter": [
      {"film_id": 1, "title": "...", "budget": ..., "revenue": ..., "category": "Drama"}
    ]  # all films with both budget+revenue > 0, capped at 500
  },
  "people": null,  # null for anonymous and free
  "taxonomy": null,  # null for anonymous and free
  "personal_stats": null  # populated only for logged-in pro/admin
}
```

**`people` payload (Pro/Admin only):**
```python
{
  "top_directors": [
    {"person_id": 1, "name": "Akira Kurosawa", "photo_url": "...",
     "nationality": "Japanese", "film_count": 27, "first_year": 1943, "last_year": 1993}
  ],  # top 15
  "top_actors": [...],  # top 15
  "top_composers": [...],  # top 15
  "top_director_nationalities": [{"nationality": "American", "count": 320}, ...],  # top 15
  "top_actor_nationalities": [...],  # top 15
  "gender_split": {
    "all": {"M": 6210, "F": 3845, "unknown": 412},
    "directors": {"M": 1080, "F": 145, "unknown": 15},
    "actors": {"M": 4520, "F": 3812, "unknown": 200}
  },
  "directors_gender_by_decade": [
    {"decade": 1980, "M": 110, "F": 8},
    ...
  ],
  "living_status": {
    "directors": {"living": 850, "deceased": 320, "unknown": 70},
    "actors": {"living": 4200, "deceased": 1340, "unknown": 992}
  },
  "directors_by_birth_decade": [{"birth_decade": 1940, "count": 180}, ...]
}
```

**`taxonomy` payload (Pro/Admin only):**
```python
{
  "top_themes": [{"name": "war", "count": 320}, ...],  # top 20 (excluding subtypes "parent: sub")
  "category_distribution": [{"name": "Drama", "count": 1840}, ...],  # all base categories
  "top_atmospheres": [{"name": "feel good", "count": 410}, ...],  # top 30 (for word cloud)
  "category_by_decade_heatmap": [
    {"category": "Drama", "decade": 1950, "count": 45},
    ...
  ]  # full grid: ~12 categories × ~12 decades = ~144 cells
}
```

**`personal_stats` payload (logged-in Pro/Admin only):**
```python
{
  "seen_count": 347,
  "unseen_count": 3425,
  "seen_pct": 9.2,
  "favorite_count": 89,
  "watchlist_count": 56,
  "rated_count": 220,
  "avg_rating": 7.4,
  "seen_by_decade": [{"decade": 1970, "count": 32}, ...],
  "top_seen_categories": [{"name": "Drama", "count": 110}, ...]  # top 10
}
```

### Backend SQL highlights

- **Duration distribution**: `CASE WHEN duration < 60 THEN '<60' WHEN duration < 90 THEN '60-89' ... END`
- **Color by decade**: `GROUP BY decade, color`, frontend reshapes into stacked
- **Most awarded films**: `JOIN award`, `COUNT(*) FILTER (WHERE result='won')` and `COUNT(*) FILTER (WHERE result='nominated')`, `ORDER BY wins DESC, nominations DESC LIMIT 20`
- **Most profitable**: `(revenue::float / NULLIF(budget,0))` with `WHERE budget > 1_000_000 AND revenue > 0`
- **Active years per person**: `MIN/MAX(EXTRACT(year FROM first_release_date))` from `crew JOIN film` or `casting JOIN film`
- **Category by decade heatmap**: `GROUP BY c.category_name, decade WHERE c.historic_subcategory_name IS NULL`
- **Categories scatter**: pick first category alphabetically per film via `(SELECT MIN(category_name) FROM ...)` correlated subquery (pragmatic, avoids row multiplication in scatter data)

### Frontend: new files

- `frontend/src/pages/StatsPage.tsx` — main page, tab orchestration, reads `?tab=` from URL
- `frontend/src/components/stats/QuickStatsTab.tsx`
- `frontend/src/components/stats/GeographyTab.tsx` — just a "Coming soon" message in 17a
- `frontend/src/components/stats/FinancialsTab.tsx`
- `frontend/src/components/stats/PeopleTab.tsx`
- `frontend/src/components/stats/TaxonomyTab.tsx`
- `frontend/src/components/stats/StatCard.tsx` — reusable card showing big number + label + optional sublabel
- `frontend/src/components/stats/LockedTabPlaceholder.tsx` — reusable lock screen with CTA ("Sign up free" or "Upgrade to Pro")
- `frontend/src/components/stats/PersonRankCard.tsx` — photo + name + nationality flag + film count + active years (used in PeopleTab for directors/actors/composers)
- `frontend/src/components/stats/CategoryDecadeHeatmap.tsx` — custom SVG grid heatmap
- `frontend/src/components/stats/AtmosphereWordCloud.tsx` — simple sized-text cloud (no library, just font-size scaled by count)
- `frontend/src/hooks/useDashboardStats.ts` — React Query wrapper around `GET /api/stats/dashboard`
- `frontend/src/lib/nationalityFlags.ts` — static map of nationality string → flag emoji ("French" → "🇫🇷", etc.) for ~50 common ones

### Frontend: modified files

- `frontend/src/App.tsx` — add `/stats` route
- `frontend/src/components/layout/Header.tsx` — add "Stats" nav link
- `frontend/src/api/client.ts` — add `getDashboardStats()` function
- `frontend/src/types/api.ts` — add `DashboardStats` and sub-types

### Charting library

Use **Recharts** (already a Vite-friendly default, MIT-licensed, lightweight, declarative). To install:
```bash
npm install recharts
```

Charts used:
- `BarChart` (top studios, top awarded, by decade, duration distribution, top themes, gender by decade, etc.) — most charts
- `PieChart` (source types, gender split, living/deceased)
- `ScatterChart` (budget vs revenue)
- `LineChart` (avg budget by decade)
- Custom SVG (heatmap, word cloud) — too specific for Recharts

### Visual design
- Match existing dark theme (charcoal `#0f0f0f` bg, amber `#f59e0b` accent)
- Tab content area uses cards with `border` and `bg-card` (consistent with existing detail page)
- Charts inherit color from CSS variables; primary chart color = amber, secondary = slate gray
- Person cards in PeopleTab navigate to `/browse?q=<encoded name>` on click

### Excluded from 17a (deferred to later sub-steps)

- **Top 20 franchises** — needs a `tmdb_collection` lookup table (collection names) populated via a backfill script. Will be added when 17b/Geography lands.
- **Geography (full tab)** — world heatmap, set-place treemap (deferred to **17b**).
- **Carousel/year-slider gallery** for People (deferred to **17c**).
- **Category × decade heatmap** — included in 17a but kept simple (custom SVG, no D3).
- **Production country** — not yet a clean concept (would need new `film_production_country` table). Explicitly out of scope for 17a.
- **Other taxonomy ideas** (co-occurrence network, rare gems, atmosphere×category cross-tab) — deferred.
- **Personal stats deep dive** (genre distribution charts, completionism rings) — 17a includes only the basics; expand later.

### Files summary

**New backend files (1):**
- `backend/app/routers/stats.py`

**Modified backend files (2):**
- `backend/app/main.py` — register new router
- `backend/app/routers/films.py` — (optional) remove old `/api/stats` endpoint or keep as alias

**New frontend files (~12):**
- `pages/StatsPage.tsx`
- `components/stats/{QuickStatsTab,GeographyTab,FinancialsTab,PeopleTab,TaxonomyTab,StatCard,LockedTabPlaceholder,PersonRankCard,CategoryDecadeHeatmap,AtmosphereWordCloud}.tsx`
- `hooks/useDashboardStats.ts`
- `lib/nationalityFlags.ts`

**Modified frontend files (4):**
- `App.tsx` (route)
- `components/layout/Header.tsx` (nav link)
- `api/client.ts` (API call)
- `types/api.ts` (types)

**New dependency:**
- `recharts` (~95 KB gzipped)


