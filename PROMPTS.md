# Claude Code Prompts — Step-by-step

## Step 1 Prompt — PostgreSQL Schema Creation ✅ DONE

*(see git history for original prompt)*

---

## Step 2 Prompt — TMDB Integration Module ✅ DONE

*(see git history for original prompt)*

---

## Step 3 Prompt — Claude Enrichment Module ✅ DONE

*(see git history for original prompt)*

---

## Step 4 Prompt — Seed 3 Reference Films ✅ DONE

*(see git history for original prompt)*

---

## Step 4.5 Prompt — Fix: Awards + Streaming Platform Support ✅ DONE

*(see git history for original prompt)*

---

## Step 5 Prompt — Backend API (FastAPI) ✅ DONE

*(see git history for original prompt)*

### Step 5 Summary
- 12 files created: database.py, models, 3 schema files, 3 routers, main.py, package inits
- 3 routers: films (list+filter+detail+create+update+stats), taxonomy (13 dimensions), persons (search+detail)
- Fixes applied: removed nested db.begin() (session auto-begins), added hierarchical theme count aggregation
- Also updated: seed_taxonomy.sql (sport sub-themes), taxonomy_config.py (sync)

---

## Step 5.5 Prompt — API Enhancements: Geography, Language & Missing Filters ✅ DONE

*(see git history for original prompt)*

### Step 5.5 Summary
- 2 new files: geography.py router (search + countries endpoints), geography.py schemas
- 3 modified files: films.py (added location, language, character_contexts, place_contexts filter params), taxonomy.py (added "languages" dimension with is_original filtering), main.py (geography router)
- Location filter searches across continent + country + state_city (replaces old country-only filter, backward compat kept)
- Language filter uses is_original = TRUE to filter by original language

---

## Step 6 Prompt — Frontend: Browse, Search & Filter ✅ DONE

*(see git history for original prompt)*

### Step 6 Summary
- Full frontend app: Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui
- Dark theme (charcoal #0f0f0f, amber #f59e0b accent, Letterboxd/Criterion aesthetic)
- 2 pages: BrowsePage (main grid+filters), FilmDetailPage (placeholder for step 7)
- 3 layout components: Layout, Header (search+sort), Sidebar (16 filter controls, Sheet on mobile)
- 3 film components: FilmGrid (responsive 2-6 cols, skeletons), FilmCard (poster+metadata+seen), Pagination
- 3 filter components: FilterSection (collapsible), FilterChip (amber toggle), ActiveFilters (removable chips bar)
- 3 hooks: useFilterState (URL-synced), useFilms (debounced fetch), useTaxonomy (11 dimensions cached)
- Also: scripts/refresh_posters.py (TMDB CDN refresh), fixed La Haine tmdb_id (3405→406)

---

## Step 6.5 Prompt — Taxonomy Refinements + Filter UX Fixes ✅ DONE

*(see git history for original prompt)*

### Step 6.5 Summary
- Migration `database/migrations/006_sort_order.sql`: added sort_order columns to theme_context and time_context, merged themes (trauma+accident → trauma/accident, technology+artificial_intelligence → AI/technology), removed survival from motivations, set sort_order values for thematic groupings and chronological time periods
- Seed data: added Documentary category, added Historical: event subcategory, updated sort_order in seed_taxonomy.sql
- Backend `films.py`: replaced OR logic with AND logic (HAVING COUNT) for all taxonomy filters, added parent expansion for hierarchical dims (themes, categories), special composite-key handling for categories filter, added studios filter param
- Backend `taxonomy.py`: added studios dimension, SORTED_DIMENSIONS set for sort_order-based ordering, categories now returns "Parent: sub" display format, added HIERARCHICAL_DIMENSIONS for count aggregation
- Frontend: removed Director filter from Sidebar/ActiveFilters/FilterState/API client, replaced year inputs with DualRangeSlider component, added Studios dropdown, added group separators in FilterSection for themes/time_periods based on sort_order gaps
- Updated taxonomy_config.py to sync merged theme names

---

## Step 7 Prompt — Film Detail View + Edit ✅ DONE

*(see git history for original prompt)*

### Step 7 Summary
- Full detail page: cinematic hero (backdrop gradient, poster, meta, category badges, director links), seen/unseen toggle (PATCH `/films/{id}/vu`), external links (TMDB, IMDb, Allociné, Wikipedia)
- Cast: horizontal scrollable PersonCard components with TMDB photos, clickable → `/browse?q=Name`
- Crew: grouped by role (Director, Writer, Cinematographer, Composer, etc.)
- All taxonomy sections with inline editing via EditableTagSection (view/edit toggle, autocomplete add, remove tags, save/cancel)
- Awards table (trophy icons), streaming badges, related films, similar films placeholder
- 7 new components: PersonCard, SectionHeading, EditableTagSection, ExternalLinks, AwardsTable, SimilarFilmsCarousel, useFilmDetail hook
- 3 modified files: types/api.ts (8 new interfaces), api/client.ts (3 new functions), lib/utils.ts (3 new helpers)
- Bug fixes: tag dropdown `.slice(0,15)` cap removed + `max-h` increased; person tmdb_ids fixed via name-matching against TMDB movie credits
- New script: `refresh_person_photos.py` (matches by name, fixes tmdb_id + photo_url, `--diagnose`/`--restore`/`--dry-run`/`--verbose` modes)

---

## Step 8 Prompt — Add Film Workflow ✅ DONE

*(see git history for original prompt)*

### Step 8 Summary
- Backend: `add_film.py` router with GET `/add-film/search` and POST `/add-film/enrich` (graceful failure with enrichment_failed flag). Registered in main.py.
- Backend: `schemas/add_film.py` with TMDBSearchResult, TMDBSearchResponse, EnrichRequest, EnrichmentPreview
- Frontend: `AddFilmPage.tsx` 3-step wizard (Search → Enrich → Review → Save → redirect)
- Frontend: Header "+" button, `/add` route, searchTMDB/enrichFilm/saveFilm in api/client.ts
- Enrichment quality: rewritten system prompt, new taxonomy values (migration 007), underscore renames (migration 008)
- Fixed Mulholland Drive reference example (missing comma)

---

## Step 8.5 Prompt — Auto-link Franchise Sequels via TMDB Collection ✅ DONE

*(see git history for original prompt)*

### Step 8.5 Summary
- Migration 009: `tmdb_collection_id` column on film table + index
- `tmdb_service.py`: captures `belongs_to_collection` from TMDB response
- `tmdb_mapper.py`: extracts `tmdb_collection_id` into film dict
- `films.py` create endpoint: stores collection_id + auto-links siblings via `film_sequel`
- `schema.sql`: updated for fresh installs
- New scripts: `backfill_collection_ids.py` (backfill existing films + auto-link), `refresh_streaming.py` (refresh streaming platforms from TMDB with unmapped provider reporting)

---

## Step 8.6 Prompt — Editable Categories, Financials, Awards + Person Data ✅ DONE

*(see git history for original prompt)*

### Step 8.6 Summary
- Frontend: `EditableFinancials.tsx` (new), editable `AwardsTable` (won/nominated toggle + X remove), `EditableTagSection` for categories in Classification section
- Backend: `awards: list[dict] | None` added to `FilmUpdate`, clear-and-reinsert in `update_film()`, gender column added to `_find_or_create_person()` INSERT + COALESCE
- Pipeline: `tmdb_mapper.py` now passes `gender` via `TMDB_GENDER_MAP` in both `_map_cast()` and `_map_crew()` output dicts
- New script: `backfill_person_details.py` (fetches `/person/{tmdb_id}` for all persons missing data, updates gender + date_of_birth + date_of_death + nationality)

---

## Step 9 — Bulk Ingestion (~2500 films)

No Claude Code prompt needed — this step uses the existing scripts built in steps 2-3. See PLAN.md for the full 4-stage procedure.

---

## Step 10 / 10.5 / 10.6 — UX Improvements, Taxonomy Admin, Delete Film ✅ DONE

*(see git history for original prompts)*

---

## Step 11 Prompt — Deployment + Admin Auth ✅ DONE

*(see git history for original prompts)*

### Step 11 Summary
- Backend: `auth.py` with `require_admin` dependency (bearer token vs `ADMIN_SECRET_KEY`, dev fallback), CORS from env, `/api/auth/login` + `/api/auth/check` endpoints, `Depends(require_admin)` on all POST/PUT/PATCH/DELETE endpoints
- Frontend: `AuthContext.tsx` (localStorage token, validate on mount via `/api/auth/check`), `LoginPage.tsx` (dark theme, password field, redirect on success)
- Frontend: `client.ts` gains `getAuthHeaders()` + `VITE_API_URL` env support, all write calls include auth headers
- Frontend: admin-only gating in Header (Add Film, Tags, Login/Logout buttons), BrowsePage (vu toggle), FilmDetailPage (edit controls, delete, seen toggle), TaxonomyAdminPage + AddFilmPage (redirect if !isAdmin)
- Deployment: `Procfile` for Render, Supabase for DB, Vercel for frontend CDN

---

## Step 12: Taxonomy restructure — merge dimensions, add sort_order grouping, rebalance tags

*(see git history for original prompts)*

---

## Step 13 Prompt — Performance Optimization (Deployed)

*(see git history for original prompts)*

---

## Step 14: Advanced 'click on tag' behaviour

No particular prompt

---

## Step 15a Prompt — Supabase Auth + User Roles + vu Migration

*(see git history for original prompts)*

---

## Step 15b Prompt — Personal Tracking UI + My Collection + Nav Menu

*(see git history for original prompts)*

---

## Step 15c Prompt — Tier-Gated Taxonomy Access

*(see git history for original prompts)*

---

## Step 16a Prompt — Recommender: "Refine in Browse" Button

Step 16a Summary
Backend: GET /api/taxonomy/tag-frequencies (24h cache, mutation-invalidated) — kept for use by future 16b/16c logic.
Frontend: "Refine in Browse →" button in Similar Films section header. Pro/Admin only. Click loads all tags from the current film into /browse in OR mode (per-dimension), letting the user manually deselect/AND-toggle from a complete starting state. Smart-selection approach (selectDistinctiveTags) was prototyped and discarded — applying all tags in OR mode tested better in practice because the user is already the best judge of which tags matter for that specific film.

---

## Step 16b Prompt — Recommender: Similar Films Algorithm (In-DB)

**Goal:** New endpoint `GET /api/films/{id}/similar?limit=N` returning the top-N most similar films using IDF-weighted Jaccard across 9 taxonomy dimensions plus structural bonuses.

### Algorithm

**IDF-weighted Jaccard per dimension, summed across 9 dimensions, plus structural bonuses.**

For source film S and candidate C, per-dimension d:
- per_dim_score(d) = Σ_{t ∈ T_S^d ∩ T_C^d} idf(t) / Σ_{t ∈ T_S^d ∪ T_C^d} idf(t)
- total = Σ_d W_d × per_dim_score(d) + bonuses

**Initial dimension weights** (tunable):
atmospheres 1.4 · themes 1.3 · motivations 1.1 · messages 1.0 · cinema_types 1.0 · characters 0.9 · categories 0.7 · place_contexts 0.6 · time_periods 0.5

**Bonuses**:
- Same director (any overlap): +0.10
- Same studio + same release decade: +0.03
- Quality nudge: +0.05 × normalized weighted_score

---

## Step 16c Prompt — Recommender: SimilarFilmsCarousel UI

**Goal:** Replace the placeholder `SimilarFilmsCarousel` with the real recommendation UI driven by the 16b endpoint, with the "Refine in Browse →" button (16a) integrated into the section header.

---

## Step 17a-Stats Dashboard API & UI

*(see git history for original prompts)*
---

## Step 17c-Taxonomy stats enhancements

*(see git history for original prompts)*
---

## Step 17d-Backend Prompt — Geography stats data

```
Read PLAN.md (Step 17d section, paying attention to the Backend changes payload shape and the ISO mapping note), then this prompt.

Read these files for context before changing anything:
- backend/app/routers/stats.py (existing dashboard endpoint, parallel-query pattern, tier resolution — mirror what's done for taxonomy)
- backend/app/routers/geography.py (existing search/countries endpoints, free-text country name patterns)
- backend/app/tier_config.py
- backend/app/auth.py
- database/migrations/020_collection_and_production_country.sql (shows production_country + film_production_country structure)
- database/schema.sql (skim geography + film_set_place)

## Task: Populate `geography` block of the dashboard payload + add 2 new endpoints

### 1. Create `backend/app/data/country_name_to_iso.py`

A static dict mapping common English country names → ISO 3166-1 alpha-2 codes. Include the ~80 most common ones plus variants:

```python
# Map (free-text country names found in `geography.country`) → ISO alpha-2 code.
# Includes common variants/aliases. Lookup should be case-insensitive (.lower() both sides).

COUNTRY_NAME_TO_ISO: dict[str, str] = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "france": "FR",
    "germany": "DE",
    "west germany": "DE",
    "east germany": "DE",
    "italy": "IT",
    "spain": "ES",
    "portugal": "PT",
    "belgium": "BE",
    "netherlands": "NL",
    "the netherlands": "NL",
    "holland": "NL",
    "luxembourg": "LU",
    "switzerland": "CH",
    "austria": "AT",
    "ireland": "IE",
    "denmark": "DK",
    "sweden": "SE",
    "norway": "NO",
    "finland": "FI",
    "iceland": "IS",
    "poland": "PL",
    "czech republic": "CZ",
    "czechia": "CZ",
    "slovakia": "SK",
    "hungary": "HU",
    "romania": "RO",
    "bulgaria": "BG",
    "greece": "GR",
    "croatia": "HR",
    "serbia": "RS",
    "slovenia": "SI",
    "bosnia and herzegovina": "BA",
    "north macedonia": "MK",
    "albania": "AL",
    "turkey": "TR",
    "ukraine": "UA",
    "russia": "RU",
    "soviet union": "RU",
    "ussr": "RU",
    "belarus": "BY",
    "estonia": "EE",
    "latvia": "LV",
    "lithuania": "LT",
    "georgia": "GE",
    "armenia": "AM",
    "china": "CN",
    "hong kong": "HK",
    "taiwan": "TW",
    "japan": "JP",
    "south korea": "KR",
    "korea": "KR",
    "north korea": "KP",
    "india": "IN",
    "pakistan": "PK",
    "bangladesh": "BD",
    "sri lanka": "LK",
    "nepal": "NP",
    "thailand": "TH",
    "vietnam": "VN",
    "cambodia": "KH",
    "laos": "LA",
    "myanmar": "MM",
    "burma": "MM",
    "indonesia": "ID",
    "malaysia": "MY",
    "philippines": "PH",
    "singapore": "SG",
    "mongolia": "MN",
    "iran": "IR",
    "iraq": "IQ",
    "israel": "IL",
    "palestine": "PS",
    "lebanon": "LB",
    "syria": "SY",
    "jordan": "JO",
    "saudi arabia": "SA",
    "united arab emirates": "AE",
    "uae": "AE",
    "qatar": "QA",
    "kuwait": "KW",
    "yemen": "YE",
    "egypt": "EG",
    "morocco": "MA",
    "algeria": "DZ",
    "tunisia": "TN",
    "libya": "LY",
    "south africa": "ZA",
    "nigeria": "NG",
    "kenya": "KE",
    "ethiopia": "ET",
    "ghana": "GH",
    "senegal": "SN",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "rwanda": "RW",
    "uganda": "UG",
    "tanzania": "TZ",
    "zimbabwe": "ZW",
    "mali": "ML",
    "burkina faso": "BF",
    "democratic republic of the congo": "CD",
    "congo": "CG",
    "angola": "AO",
    "mozambique": "MZ",
    "canada": "CA",
    "mexico": "MX",
    "cuba": "CU",
    "jamaica": "JM",
    "haiti": "HT",
    "dominican republic": "DO",
    "puerto rico": "PR",
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "venezuela": "VE",
    "peru": "PE",
    "bolivia": "BO",
    "ecuador": "EC",
    "uruguay": "UY",
    "paraguay": "PY",
    "guatemala": "GT",
    "honduras": "HN",
    "nicaragua": "NI",
    "costa rica": "CR",
    "panama": "PA",
    "australia": "AU",
    "new zealand": "NZ",
    "papua new guinea": "PG",
}


def country_name_to_iso(name: str | None) -> str | None:
    """Returns ISO 3166-1 alpha-2 code for a free-text country name, or None.

    Case-insensitive lookup against the static map.
    """
    if not name:
        return None
    return COUNTRY_NAME_TO_ISO.get(name.strip().lower())
```

### 2. Extend `geography` block in `/api/stats/dashboard`

In `stats.py`, when the user is Pro or Admin, populate `geography` block instead of returning `null`. Use the existing parallel-query pattern (one coroutine per sub-query, gathered with `asyncio.gather()`).

#### 2a. `production_countries` (top to bottom by count)

```sql
SELECT pc.country_code AS iso,
       pc.country_name AS country,
       COUNT(DISTINCT fpc.film_id) AS film_count
FROM production_country pc
JOIN film_production_country fpc ON pc.country_id = fpc.country_id
GROUP BY pc.country_code, pc.country_name
ORDER BY film_count DESC, country
```

Return shape: `[{"iso", "country", "film_count"}]`.

#### 2b. `set_place_countries` (by country aggregated, ISO-mapped in Python)

```sql
SELECT g.country, COUNT(DISTINCT fsp.film_id) AS film_count
FROM geography g
JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
WHERE g.country IS NOT NULL
GROUP BY g.country
ORDER BY film_count DESC, g.country
```

In Python: walk the results, apply `country_name_to_iso(row.country)` to get ISO. **Aggregate by ISO** (multiple free-text variants may map to the same code, e.g., "USSR" and "Soviet Union" both → RU). Drop rows where ISO is None (unmapped, will be excluded from the choropleth). Return `[{"iso", "country", "film_count"}]` with country = the canonical English name (use the production_country.country_name lookup if available, fall back to the original free-text).

#### 2c. `set_place_treemap` (hierarchical)

```sql
SELECT g.continent, g.country, g.state_city, g.geography_id,
       COUNT(DISTINCT fsp.film_id) AS film_count
FROM geography g
JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
WHERE g.continent IS NOT NULL
GROUP BY g.continent, g.country, g.state_city, g.geography_id
ORDER BY g.continent, g.country, g.state_city
```

Return shape: `[{"continent", "country", "state_city", "geography_id", "film_count"}]`.

#### 2d. `production_country_total` / `set_place_country_total`

Total distinct countries with at least one film:

```sql
-- production
SELECT COUNT(DISTINCT country_id) FROM film_production_country;
-- set place (count distinct countries from geography, free-text)
SELECT COUNT(DISTINCT country) FROM geography
WHERE country IS NOT NULL
AND geography_id IN (SELECT geography_id FROM film_set_place);
```

Return shape: integers.

#### 2e. `most_international_film`

```sql
SELECT fpc.film_id, f.original_title AS title,
       COUNT(*) AS country_count,
       array_agg(pc.country_code ORDER BY pc.country_code) AS countries
FROM film_production_country fpc
JOIN film f ON fpc.film_id = f.film_id
JOIN production_country pc ON fpc.country_id = pc.country_id
GROUP BY fpc.film_id, f.original_title
ORDER BY country_count DESC, f.original_title
LIMIT 1
```

Return shape: `{"film_id", "title", "country_count", "countries": [iso, ...]}` or `null` if no data.

### 3. NEW endpoint `GET /api/stats/films-by-country`

Query params:
- `type: str` (`production` or `set_place`, required)
- `iso: str` (ISO alpha-2, required)
- `limit: int = 10` (max 30)

Tier check: Pro/Admin only, 403 otherwise.

**For `type=production`:**

```sql
SELECT f.film_id, f.original_title AS title, f.poster_url,
       EXTRACT(YEAR FROM f.first_release_date)::int AS year,
       f.weighted_score
FROM film f
JOIN film_production_country fpc ON f.film_id = fpc.film_id
JOIN production_country pc ON fpc.country_id = pc.country_id
WHERE pc.country_code = :iso
ORDER BY f.weighted_score DESC NULLS LAST, f.first_release_date DESC
LIMIT :limit
```

**For `type=set_place`:**

Resolve ISO → country name via reverse lookup of `COUNTRY_NAME_TO_ISO` (i.e., find all free-text variants that map to this ISO), then query:

```sql
SELECT DISTINCT f.film_id, f.original_title AS title, f.poster_url,
       EXTRACT(YEAR FROM f.first_release_date)::int AS year,
       f.weighted_score
FROM film f
JOIN film_set_place fsp ON f.film_id = fsp.film_id
JOIN geography g ON fsp.geography_id = g.geography_id
WHERE LOWER(g.country) = ANY(:country_names)
ORDER BY f.weighted_score DESC NULLS LAST, f.first_release_date DESC
LIMIT :limit
```

Where `:country_names` is the list of lowercase free-text variants for this ISO (e.g., for `iso=US`: `['united states', 'united states of america', 'usa', 'us']`).

Return shape: `[{film_id, title, poster_url, year, weighted_score}]`.

### 4. Pydantic schemas

Add to `stats.py` (or `schemas/stats.py`):

```python
class ProductionCountryCell(BaseModel):
    iso: str
    country: str
    film_count: int

class SetPlaceCountryCell(BaseModel):
    iso: str
    country: str
    film_count: int

class SetPlaceTreemapCell(BaseModel):
    continent: str
    country: str | None
    state_city: str | None
    geography_id: int
    film_count: int

class MostInternationalFilm(BaseModel):
    film_id: int
    title: str
    country_count: int
    countries: list[str]

class GeographyPayload(BaseModel):
    production_countries: list[ProductionCountryCell]
    set_place_countries: list[SetPlaceCountryCell]
    set_place_treemap: list[SetPlaceTreemapCell]
    production_country_total: int
    set_place_country_total: int
    most_international_film: MostInternationalFilm | None

class FilmByCountry(BaseModel):
    film_id: int
    title: str
    poster_url: str | None
    year: int | None
    weighted_score: float | None
```

Update `DashboardResponse.geography` from `None`-only to `GeographyPayload | None`.

### 5. Verification

```bash
curl -H "Authorization: Bearer <pro-jwt>" http://localhost:8000/api/stats/dashboard | jq '.geography.production_country_total, .geography.set_place_country_total, .geography.most_international_film, .geography.production_countries[0:3], .geography.set_place_treemap[0:3]'

curl -H "Authorization: Bearer <pro-jwt>" "http://localhost:8000/api/stats/films-by-country?type=production&iso=US&limit=5" | jq '.'

curl -H "Authorization: Bearer <pro-jwt>" "http://localhost:8000/api/stats/films-by-country?type=set_place&iso=FR&limit=5" | jq '.'

# As free user: geography should be null
curl -H "Authorization: Bearer <free-jwt>" http://localhost:8000/api/stats/dashboard | jq '.geography'
```

Dashboard payload still responds in <2s for pro tier (queries are parallel).
```

---

## Step 17d-Frontend Prompt — Geography tab UI

```
Read PLAN.md (Step 17d section), then this prompt.

Read these files for context before changing anything:
- frontend/src/components/stats/GeographyTab.tsx (current placeholder, will be replaced)
- frontend/src/components/stats/LockedTabPlaceholder.tsx (used for non-pro tiers)
- frontend/src/components/stats/StatCard.tsx (reused for top stat cards)
- frontend/src/components/stats/Section.tsx (consistent section wrapping)
- frontend/src/components/stats/PosterRow.tsx (existing pattern, reuse for the country films panel)
- frontend/src/components/stats/chartTheme.ts
- frontend/src/types/api.ts (extend types)
- frontend/src/api/client.ts (add getFilmsByCountry)
- frontend/src/context/AuthContext.tsx (useAuth hook, tier)
- frontend/src/lib/tierAccess.ts

## Task: Implement the Geography tab with two world maps + treemap + click-to-films panel

### 0. Install dependency + download world topojson

```bash
cd frontend
npm install react-simple-maps@3.0.0 d3-geo@3.1.0
npm install -D @types/react-simple-maps @types/d3-geo
```

Download the world topojson file (110m resolution, ~120 KB) and save it at `frontend/public/world-110m.json`. The standard file is hosted at:
- https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json

Commit this file to the repo (it's tiny and avoids a CDN dependency at runtime).

### 1. Extend types in `frontend/src/types/api.ts`

```typescript
export interface ProductionCountryCell {
  iso: string;
  country: string;
  film_count: number;
}

export interface SetPlaceCountryCell {
  iso: string;
  country: string;
  film_count: number;
}

export interface SetPlaceTreemapCell {
  continent: string;
  country: string | null;
  state_city: string | null;
  geography_id: number;
  film_count: number;
}

export interface MostInternationalFilm {
  film_id: number;
  title: string;
  country_count: number;
  countries: string[];
}

export interface GeographyPayload {
  production_countries: ProductionCountryCell[];
  set_place_countries: SetPlaceCountryCell[];
  set_place_treemap: SetPlaceTreemapCell[];
  production_country_total: number;
  set_place_country_total: number;
  most_international_film: MostInternationalFilm | null;
}

export interface FilmByCountry {
  film_id: number;
  title: string;
  poster_url: string | null;
  year: number | null;
  weighted_score: number | null;
}
```

Update `DashboardStats.geography` type from `null` to `GeographyPayload | null`.

### 2. Add API function in `frontend/src/api/client.ts`

```typescript
export async function getFilmsByCountry(
  type: "production" | "set_place",
  iso: string,
  limit = 10,
): Promise<FilmByCountry[]> {
  const res = await fetch(
    `${BASE}/stats/films-by-country?type=${type}&iso=${iso}&limit=${limit}`,
    { headers: { ...getAuthHeaders() } },
  );
  if (!res.ok) throw new ApiError(res.status, "Failed to load films for country");
  return res.json();
}
```

### 3. Create `frontend/src/lib/colorScale.ts`

A helper for mapping a film count to a color intensity (0–1 alpha). Counts span 1–3000+, so use a **log scale** rather than linear to make small markets visible:

```typescript
// Maps a count to a 0..1 intensity, log-scaled for visibility across orders of magnitude.
export function intensity(count: number, maxCount: number): number {
  if (count <= 0) return 0;
  if (maxCount <= 1) return 1;
  // log scale: small counts already get significant intensity
  return Math.log(count + 1) / Math.log(maxCount + 1);
}

export function amberShade(intensity: number): string {
  // Map 0..1 intensity to an amber HSL color, with low end staying visible.
  if (intensity === 0) return "#1f1f1f"; // dark gray for no-data countries
  const lightness = 50 - intensity * 30; // 50% → 20%
  const opacity = 0.3 + intensity * 0.7; // 0.3 → 1.0
  return `hsla(38, 92%, ${lightness}%, ${opacity})`;
}

// Build legend buckets for the color scale (used in the legend below the map)
export function legendBuckets(maxCount: number): Array<{ label: string; intensity: number }> {
  const buckets = [1, 10, 50, 200, 1000];
  return buckets
    .filter((b) => b <= maxCount * 2)
    .map((count) => ({
      label: count >= 1000 ? `${count}+` : `${count}`,
      intensity: intensity(count, maxCount),
    }));
}
```

### 4. Create `frontend/src/components/stats/WorldMap.tsx`

Generic choropleth component using react-simple-maps. Props:

```typescript
interface WorldMapProps {
  data: { iso: string; country: string; film_count: number }[];
  onCountryClick: (iso: string, country: string) => void;
  selectedIso?: string | null;
}
```

Implementation:

- Load `/world-110m.json` once (use `useEffect`, cache the result with `useMemo`).
- Build a `Map<iso2, film_count>` from `data` for O(1) lookup.
- Render `ComposableMap` with `projection="geoMercator"` or `geoEqualEarth` (Equal Earth looks better for a world view). Use `width=900 height=400` with `ResponsiveContainer`-like wrapper for responsiveness.
- Inside `Geographies`, render one `Geography` per country. Look up the film count from the map (note: react-simple-maps + world-atlas uses **numeric ISO codes** like `"840"` for US, not alpha-2. You'll need to convert. The world-atlas geojson properties include `name`, which is the English country name — use that against the same `COUNTRY_NAME_TO_ISO` mapping, **OR** add an `id_iso2` mapping in this component. Simpler: use the country `name` from the geojson, normalize via a small client-side ISO map matching the backend's COUNTRY_NAME_TO_ISO).
- Fill: `amberShade(intensity(count, max))`. No data → dark gray.
- Stroke: thin slate gray border between countries.
- Hover: change cursor to pointer, slight stroke highlight.
- Tooltip on hover: floating div with country name + film count.
- Click: call `onCountryClick(iso, country)`.
- Selected country (matching `selectedIso`) gets a thicker amber-yellow stroke.

Include a legend below the map: a horizontal row of `legendBuckets()` rendered as small colored squares with their label.

**Add a small client-side `iso3ToIso2` or `countryName → iso2` helper in this component file or import it.** Best path: maintain a static `WORLD_ATLAS_NAME_TO_ISO2` in the component file mirroring the backend mapping (since the world-atlas geojson uses simple country names).

### 5. Create `frontend/src/components/stats/CountryFilmsPanel.tsx`

The click-triggered panel showing top-10 films for the selected country. Props:

```typescript
interface CountryFilmsPanelProps {
  iso: string;
  country: string;
  type: "production" | "set_place";
  onClose: () => void;
}
```

Implementation:
- On mount and on prop change: call `getFilmsByCountry(type, iso, 10)`, store in state.
- Loading state: skeleton/spinner.
- Render a card with header (country flag emoji + country name + "×" close button), then a vertical list of films (poster left, title + year right). Click a film → navigate to `/films/{film_id}`.
- Use the existing flag emoji helper if present (from `lib/nationalityFlags.ts` or similar) — if absent, just show the ISO code in a small monospace badge.

### 6. Create `frontend/src/components/stats/SetPlaceTreemap.tsx`

Wrapper around Recharts `Treemap`. Transforms the flat `set_place_treemap` data into the hierarchical structure Recharts wants:

```typescript
interface SetPlaceTreemapProps {
  data: SetPlaceTreemapCell[];
}
```

Transform: group by continent, then country, then leave cities as leaves. Recharts Treemap takes `{name, size, children}`. Build a 3-level tree.

Render:
```tsx
<ResponsiveContainer width="100%" height={500}>
  <Treemap
    data={transformed}
    dataKey="size"
    nameKey="name"
    stroke="#0f0f0f"
    fill="#f59e0b"
    isAnimationActive={false}
  >
    <Tooltip ... />
  </Treemap>
</ResponsiveContainer>
```

On click on a leaf (city), navigate to `/browse?location=<geography_id>`. Recharts Treemap's `onClick` gives access to the original data node, so `geography_id` can be embedded into the node.

Use log-scaled sizes if visual disparity is too big (cities with 5 films should still be visible alongside cities with 200).

### 7. Replace `GeographyTab.tsx`

Full implementation. Layout (vertical):

```tsx
import { useAuth } from "@/context/AuthContext";
import { useState } from "react";

export function GeographyTab({ data }: { data: GeographyPayload | null }) {
  const { tier } = useAuth();
  const [selectedProd, setSelectedProd] = useState<{ iso: string; country: string } | null>(null);
  const [selectedSet, setSelectedSet] = useState<{ iso: string; country: string } | null>(null);

  if (data === null) {
    if (tier === "anonymous") {
      return <LockedTabPlaceholder reason="signup" tabName="Geography" />;
    }
    return <LockedTabPlaceholder reason="upgrade" tabName="Geography" />;
  }

  return (
    <div className="space-y-8">
      {/* Stat cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard value={data.production_country_total} label="Countries produced in" />
        <StatCard value={data.set_place_country_total} label="Countries set in" />
        {data.most_international_film && (
          <StatCard
            value={`${data.most_international_film.country_count} countries`}
            label="Most international film"
            sublabel={data.most_international_film.title}
          />
        )}
      </div>

      {/* Production map */}
      <Section
        title="Where films are produced"
        subtitle="Each country shaded by the number of films co-produced there. Click a country for its top 10 films."
      >
        <WorldMap
          data={data.production_countries}
          onCountryClick={(iso, country) => setSelectedProd({ iso, country })}
          selectedIso={selectedProd?.iso ?? null}
        />
        {selectedProd && (
          <CountryFilmsPanel
            iso={selectedProd.iso}
            country={selectedProd.country}
            type="production"
            onClose={() => setSelectedProd(null)}
          />
        )}
      </Section>

      {/* Set place map */}
      <Section
        title="Where films take place"
        subtitle="Same map, different question: which countries are the films *set* in?"
      >
        <WorldMap
          data={data.set_place_countries}
          onCountryClick={(iso, country) => setSelectedSet({ iso, country })}
          selectedIso={selectedSet?.iso ?? null}
        />
        {selectedSet && (
          <CountryFilmsPanel
            iso={selectedSet.iso}
            country={selectedSet.country}
            type="set_place"
            onClose={() => setSelectedSet(null)}
          />
        )}
      </Section>

      {/* Treemap */}
      <Section
        title="Locations breakdown"
        subtitle="Continent → country → city. Click a city to browse its films."
      >
        <SetPlaceTreemap data={data.set_place_treemap} />
      </Section>
    </div>
  );
}
```

Update the parent (`StatsPage.tsx`) to pass `data.geography` as the prop.

### 8. Verification

Log in as Pro/Admin, visit `/stats?tab=geo`:
- Stat cards show counts (e.g. "78 countries produced in", "95 countries set in")
- Production world map renders, US/UK/France brightly shaded, smaller markets dimly visible. Click US → panel opens with top 10 American productions.
- Set-place world map shows different shading pattern.
- Treemap renders 5-6 continents at top level, click into one → countries, click into one → cities.
- Click a city → navigates to /browse with the location filter applied.

Log in as Free → see "Upgrade to Pro" placeholder.
Log out → see "Sign up free" placeholder.

### Important notes

- Match dark theme: map ocean = `#0f0f0f` (page background), country fill = amber-scaled, country stroke = subtle slate gray `#334155`.
- The world topojson goes in `/public/world-110m.json` so Vite serves it as a static asset.
- Don't use d3-scale or chroma libraries unless absolutely needed — our color helper in `lib/colorScale.ts` is enough.
- Mobile responsiveness: world map renders narrow but legible at 380px viewport, treemap height=350 instead of 500 on mobile.
- Don't break TaxonomyTab, FinancialsTab, PeopleTab, QuickStatsTab — only GeographyTab is touched.
- React Query: dashboard query already cached; the new `getFilmsByCountry` endpoint should use a small in-memory cache or just refetch on country click (results are small).
```

---



