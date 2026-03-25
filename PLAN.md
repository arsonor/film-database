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
| 6.5 | Taxonomy refinements + filter UX fixes | 🔄 IN PROGRESS | AND logic, sort_order, theme merges, Historical subcategories, studios, dual-slider |
| 7 | Film detail view + edit | 🔲 TODO | Full detail panel, tag editing |
| 8 | Add Film workflow | 🔲 TODO | TMDB search → Claude enrich → save |
| 9 | Recommendation engine (in-DB) | 🔲 TODO | Tag similarity scoring |
| 10 | Claude-powered recommendations | 🔲 TODO | External film suggestions |
| 11 | Bulk ingestion (~2500 films) | 🔲 TODO | Parse Films_list.docx, batch process |
| 12 | Dashboard & stats | 🔲 TODO | Analytics, charts, coverage |

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

---

## Step 6.5: Taxonomy Refinements + Filter UX Fixes

### Problem
After testing the frontend with real data, several taxonomy and UX improvements are needed:

1. **AND logic:** Multi-selecting filters within a dimension should require ALL selected values (AND), not just any of them (OR).
2. **Parent theme expansion:** Selecting "art" should match films tagged with "art: cinema", "art: music", etc. Same for "sport". Same for "Historical" matching "Historical: biopic", etc.
3. **Categories:** Add "Documentary" as a new base category. Add "Historical: event" as a new subcategory. Expose Historical subcategories in the sidebar using the "parent: sub" convention.
4. **Themes:** Merge "trauma" + "accident" → "trauma/accident". Merge "technology" + "artificial_intelligence" → "AI/technology". Add a `sort_order` column to control display order with thematic groupings.
5. **Time periods:** Add `sort_order` column. Chronological order (future → prehistoric) + seasons separately.
6. **Motivations:** Remove "survival" (already in themes).
7. **Studios filter:** Add studios as a new filter dimension (taxonomy endpoint + film list filter param + frontend dropdown).
8. **Remove Director filter:** Redundant with main search bar.
9. **Year range:** Replace two input boxes with a dual-handle range slider.

### A. Schema Migration — `database/migrations/006_sort_order.sql`

Add `sort_order` column to taxonomy tables that need custom ordering:

```sql
ALTER TABLE theme_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
ALTER TABLE time_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
```

### B. Seed Data Changes — `database/seed_taxonomy.sql`

**Categories:**
- Add `('Documentary', NULL)`
- Add `('Historical', 'event')`

**Themes — merges:**
- Rename `trauma` → `trauma/accident` (UPDATE in migration)
- Delete `accident` (migrate any film_theme rows first)
- Rename `technology` → `AI/technology` (UPDATE in migration)
- Delete `artificial_intelligence` (migrate any film_theme rows first)

**Themes — sort_order values** (thematic groupings):
```
Group 1 - Society (sort_order 100-199):
  social(100), class struggle(101), societal(102), immigration(103), political(104), 
  religion(105), business(106), censorship(107), trial(108), prison(109), 
  war(110), tragedy(111), apocalypse(112)

Group 2 - Personal/Psychological (200-299):
  trauma/accident(200), psychological(201), identity crisis(202), disease(203), 
  amnesia(204), death(205), mourning(206), addiction/drugs(207), 
  time passing(208), evolution(209)

Group 3 - Crime/Thriller (300-399):
  investigation(300), spy(301), crime(302), sex crime(303), organized crime(304), 
  police violence(305), corruption(306), delinquency(307), organized fraud(308), 
  mafia(309), gangster(310), serial killer(311), chase/escape(312), 
  terrorism(313), sect(314), survival(315), slasher(316)

Group 4 - Sci-fi/Fantasy (400-499):
  futuristic(400), dystopia(401), tales and legends(402), supernatural(403), 
  sorcery(404), alien contact(405), paranormal(406), time travel/loop(407), 
  virtual reality(408), dream(409), nonsense(410)

Group 5 - Art & Sport (500-599):
  art(500), art: music(501), art: cinema(502), art: literature(503), 
  art: fashion(504), art: painting(505), art: sculpture(506), art: theatre(507), 
  art: radio(508), martial arts(509),
  sport(520), sport: individual(521), sport: collective(522), 
  sport: tournament(523), sport: motor(524)

Group 6 - Misc (600-699):
  nature(600), AI/technology(601), food/cooking(602), party(603), book(604)
```

**Time periods — sort_order values:**
```
Chronological (sort_order 1-20):
  future(1), contemporary(2), end 20th(3), 30-year post-war boom(4), WW2(5), 
  interwar(6), WW1(7), early 20th(8), 19th(9), modern age(10), 
  medieval(11), antiquity(12), prehistoric(13), undetermined(14)

Seasons (sort_order 100-103):
  spring(100), summer(101), autumn(102), winter(103)
```

**Motivations:**
- Remove `survival`

### C. Taxonomy Config — `backend/app/services/taxonomy_config.py`

Sync all changes: add Documentary, add Historical: event, rename merged themes, remove survival from motivations, add studios references.

### D. Backend: Filter Logic — `backend/app/routers/films.py`

**AND logic (HAVING COUNT):** Replace the current `ANY(:param)` subquery with:
```sql
f.film_id IN (
    SELECT jt.film_id FROM {junc_table} jt
    JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
    WHERE lt.{lookup_name} = ANY(:{param_key})
    GROUP BY jt.film_id
    HAVING COUNT(DISTINCT lt.{lookup_name}) = :{param_key}_count
)
```
Pass `params[f"{param_key}_count"] = len(values)` alongside the array.

**Parent expansion for hierarchical dimensions (themes, categories):**
When filtering themes/categories, if a selected value has no `: ` in it AND children exist with that prefix, expand the match:
```sql
WHERE lt.{lookup_name} = ANY(:{param_key})
   OR lt.{lookup_name} LIKE ANY(
       SELECT unnest(:{param_key_parents}) || ': %'
   )
```
Build `param_key_parents` from values that are known parent prefixes (no `: ` in them).

**Categories filter — special handling:** Categories uses `category_name` + `historic_subcategory_name`. The taxonomy now returns display names like `"Historical: biopic"`. The filter needs to handle this format:
- If the filter value contains `: `, split it and match both columns: `category_name = 'Historical' AND historic_subcategory_name = 'biopic'`
- If the filter value has no `: `, match base category: `category_name = 'Historical' AND historic_subcategory_name IS NULL`
- Parent expansion: selecting `"Historical"` should also match all subcategories

**Studios filter:** Add `studios: list[str] | None = Query(None)` param. Subquery through `production` junction + `studio` lookup:
```sql
f.film_id IN (
    SELECT pr.film_id FROM production pr
    JOIN studio s ON pr.studio_id = s.studio_id
    WHERE s.studio_name = ANY(:studios)
    GROUP BY pr.film_id
    HAVING COUNT(DISTINCT s.studio_name) = :studios_count
)
```

**Remove `director` param** from the endpoint signature and filter logic.

### E. Backend: Taxonomy Endpoint — `backend/app/routers/taxonomy.py`

**Categories:** Replace the simple `WHERE historic_subcategory_name IS NULL` filter with a query that returns all categories using the `"parent: sub"` display convention:
```sql
SELECT lt.category_id, 
       CASE 
           WHEN lt.historic_subcategory_name IS NOT NULL 
           THEN lt.category_name || ': ' || lt.historic_subcategory_name
           ELSE lt.category_name
       END AS display_name,
       COUNT(jt.film_id) AS film_count
FROM category lt
LEFT JOIN film_genre jt ON lt.category_id = jt.category_id
GROUP BY lt.category_id, lt.category_name, lt.historic_subcategory_name
ORDER BY lt.category_name, lt.historic_subcategory_name NULLS FIRST
```

Add `"categories"` to `HIERARCHICAL_DIMENSIONS` for parent count aggregation.

**Studios:** Add `"studios"` to `DIMENSION_MAP`:
```python
"studios": ("studio", "studio_id", "studio_name", "production", "studio_id"),
```

**Sort order:** For dimensions with `sort_order` columns (themes, time_periods), change ORDER BY from `lt.{name_col}` to `lt.sort_order, lt.{name_col}`. Add a set `SORTED_DIMENSIONS = {"themes", "time_periods"}` and conditionally use the sort_order column.

### F. Frontend: Remove Director Filter

Remove the Director filter section from `Sidebar.tsx`. Remove `director` from `FilterState`, `DEFAULT_FILTER_STATE`, and the API client query builder. Clean up `useFilterState.ts`, `ActiveFilters.tsx`, and `Header.tsx` if director is referenced.

### G. Frontend: Year Range Dual Slider

Replace the two year input boxes in `Sidebar.tsx` with a dual-handle range slider.

Install a lightweight slider library:
```bash
cd frontend && npm install react-slider
```

Or build a custom dual-range component with two HTML `<input type="range">` elements and Tailwind styling. The range should span 1900–2030 (or dynamically from min/max years in the DB). Two draggable handles for min and max year. Display the selected range values above or below the slider.

### H. Frontend: Studios Filter

Add a Studios dropdown in the sidebar (same pattern as Language dropdown). Fetch `GET /api/taxonomy/studios` on mount. Display as a Select component with studio names + film counts.

Add `studios` to `FilterState` as `string[]`, to `TAXONOMY_DIMENSIONS`, `ARRAY_FILTER_KEYS`, and the API client query builder.

### I. Frontend: Theme/Time Grouping Display

The taxonomy endpoint now returns items sorted by `sort_order`. Themes have gaps between groups (100s, 200s, 300s...). The frontend `FilterSection` component should detect these group boundaries and insert a visual separator (a thin `<hr>` or `<Separator>` from shadcn/ui) between groups.

Logic: iterate through items, when `sort_order` jumps by ≥50 (i.e. different hundreds group), insert a separator. The `TaxonomyItem` type needs a new optional field `sort_order: number | null` from the API.

### Validation

After implementation:
1. Server starts without errors
2. `GET /api/taxonomy/categories` — shows Historical subcategories and Documentary
3. `GET /api/taxonomy/themes` — sorted by thematic groups, trauma/accident merged, AI/technology merged
4. `GET /api/taxonomy/time_periods` — chronological order, seasons at end
5. `GET /api/taxonomy/studios` — returns studios with film counts
6. `GET /api/taxonomy/motivations` — survival is gone
7. `GET /api/films?themes=art` — returns films tagged with any art sub-theme
8. `GET /api/films?categories=Historical` — returns films with any Historical subcategory
9. `GET /api/films?themes=social&themes=political` — returns only films with BOTH themes (AND)
10. `GET /api/films?studios=Metro-Goldwyn-Mayer` — filters by studio
11. Frontend: Director filter removed from sidebar
12. Frontend: Year range shows a dual-handle slider
13. Frontend: Studios dropdown appears in sidebar
14. Frontend: Theme section shows visual separators between groups
15. Frontend: Time periods show in chronological order, seasons separated

---

## Environment Setup

### PostgreSQL
```bash
createdb -U postgres film_database
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
```

### Python
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Seed Data
```bash
python scripts/seed_reference_films.py --offline
python scripts/verify_db.py
```

### API Keys (.env)
- `DATABASE_URL=postgresql+asyncpg://postgres:postgre26@localhost:5432/film_database`
- `TMDB_API_KEY` — https://www.themoviedb.org/settings/api
- `ANTHROPIC_API_KEY` — for Claude enrichment
