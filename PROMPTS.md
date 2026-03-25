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

## Step 6.5 Prompt — Taxonomy Refinements + Filter UX Fixes

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 6.5 specification (sections A through I). Then read ALL of the following files to understand the current codebase:

**Backend (what you'll modify):**
- `backend/app/routers/films.py` — Current filter logic (see `_taxonomy_filters` loop, `ANY(:param)` pattern, `director` param)
- `backend/app/routers/taxonomy.py` — Current taxonomy endpoint (see `DIMENSION_MAP`, `HIERARCHICAL_DIMENSIONS`, categories special handling, sort order)
- `backend/app/services/taxonomy_config.py` — Current valid taxonomy values (VALID_THEMES, VALID_MOTIVATIONS, VALID_CATEGORIES, etc.)
- `database/seed_taxonomy.sql` — Current seed data for all taxonomy tables
- `database/schema.sql` — Table definitions (category has `historic_subcategory_name` column; theme_context, time_context need new `sort_order` column)

**Frontend (what you'll modify):**
- `frontend/src/components/layout/Sidebar.tsx` — Current sidebar with Director filter (to remove) and year range inputs (to replace with slider)
- `frontend/src/types/api.ts` — Current FilterState, TAXONOMY_DIMENSIONS, ARRAY_FILTER_KEYS
- `frontend/src/hooks/useFilterState.ts` — Current filter state management
- `frontend/src/hooks/useTaxonomy.ts` — Current taxonomy fetching
- `frontend/src/components/filters/FilterSection.tsx` — Current filter section (needs group separators)
- `frontend/src/components/filters/ActiveFilters.tsx` — References to director filter (remove)
- `frontend/src/api/client.ts` — Current API client (director param to remove, studios param to add)

### Goal

Apply 9 refinements to the backend taxonomy data and frontend filter UX. These are corrections and improvements identified during real-world testing of the browse interface.

### 1. AND Logic Within Taxonomy Filters — Backend

**Current behavior:** Selecting multiple values within a taxonomy dimension (e.g., themes=social, themes=political) uses OR — shows films with social OR political.

**Wanted behavior:** AND — shows only films that have BOTH social AND political.

**Fix in `films.py`:** Replace the current `ANY(:param)` subquery pattern in the `_taxonomy_filters` loop with a `HAVING COUNT` pattern:

```python
for i, (values, junc_table, junc_fk, lookup_table, lookup_pk, lookup_name) in enumerate(_taxonomy_filters):
    if not values:
        continue
    param_key = f"tax_{i}"
    count_key = f"tax_{i}_count"
    where_clauses.append(
        f"""f.film_id IN (
            SELECT jt.film_id FROM {junc_table} jt
            JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
            WHERE lt.{lookup_name} = ANY(:{param_key})
            GROUP BY jt.film_id
            HAVING COUNT(DISTINCT lt.{lookup_name}) = :{count_key}
        )"""
    )
    params[param_key] = values
    params[count_key] = len(values)
```

### 2. Parent Expansion for Hierarchical Dimensions — Backend

**Problem:** Selecting "art" as a theme filter returns nothing because films are tagged with "art: cinema", not "art" directly. Same issue with "sport" and "Historical" category.

**Fix in `films.py`:** For the themes and categories filters, when building the subquery, also match child items by prefix. After the `_taxonomy_filters` loop processes values, detect parent values (values without `: `) and expand the WHERE clause:

For **themes** specifically (index in _taxonomy_filters is 1):
```python
# After building the standard subquery, check if any values are parent prefixes
parent_values = [v for v in values if ": " not in v]
if parent_values:
    # Expand WHERE to also match children: art → matches "art: cinema", "art: music", etc.
    # Replace the simple ANY clause with:
    where_clauses[-1] = f"""f.film_id IN (
        SELECT jt.film_id FROM {junc_table} jt
        JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
        WHERE lt.{lookup_name} = ANY(:{param_key})
           OR ({" OR ".join(f"lt.{lookup_name} LIKE :{param_key}_parent_{j}" for j in range(len(parent_values)))})
        GROUP BY jt.film_id
        HAVING COUNT(DISTINCT CASE 
            WHEN lt.{lookup_name} = ANY(:{param_key}) THEN lt.{lookup_name}
            {" ".join(f"WHEN lt.{lookup_name} LIKE :{param_key}_parent_{j} THEN '{pv}'" for j, pv in enumerate(parent_values))}
        END) = :{count_key}
    )"""
    for j, pv in enumerate(parent_values):
        params[f"{param_key}_parent_{j}"] = f"{pv}: %"
```

This is complex. A **simpler alternative** that still works: when a parent value is in the list, expand it by adding all its children to the values array BEFORE building the subquery. Query the DB or use a static list. Since we know the parents are "art" and "sport" for themes, and "Historical" for categories:

```python
# Simpler approach: expand parent values to include children
THEME_PARENTS = {"art", "sport"}
if dimension == "themes" and values:
    expanded = list(values)
    for v in values:
        if v in THEME_PARENTS:
            # Add all children — we know the pattern
            expanded_children = [item for item in all_theme_names if item.startswith(f"{v}: ")]
            expanded.extend(expanded_children)
    values = expanded
    # Now use standard ANY with the expanded list (but keep original count for AND logic)
```

Choose whichever approach is cleanest. The key requirement: selecting "art" must match films tagged with any "art: *" sub-theme. And for AND logic: if user selects "art" + "psychological", the film needs at least one art-related tag AND the "psychological" tag.

### 3. Categories: Add Documentary + Historical Subcategories — Seed + Backend

**Seed changes (`seed_taxonomy.sql`):**
- Add `('Documentary', NULL)` to the category INSERT
- Add `('Historical', 'event')` to the category INSERT

**Taxonomy config (`taxonomy_config.py`):**
- Add `"Documentary"` to VALID_CATEGORIES

**Taxonomy endpoint (`taxonomy.py`):** Replace the current categories handling (which hides subcategories with `WHERE historic_subcategory_name IS NULL`) with a query that shows all categories using the `"parent: sub"` display convention:

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

Add `"categories"` to `HIERARCHICAL_DIMENSIONS` so parent count aggregation works:
```python
HIERARCHICAL_DIMENSIONS = {"themes", "categories"}
```

**Categories filter in `films.py`:** The categories filter subquery currently matches on `category_name`. With the new display format `"Historical: biopic"`, the filter values may come as `"Historical: biopic"` or just `"Historical"`. The subquery needs to handle both:
- Values with `: ` → split and match `category_name = 'Historical' AND historic_subcategory_name = 'biopic'`
- Values without `: ` → match `category_name = 'Drama' AND historic_subcategory_name IS NULL` (base category)
- Parent expansion: `"Historical"` should also match all its subcategories (same as theme parent expansion)

**Important:** The categories filter is the FIRST entry in `_taxonomy_filters`. Since it has special column logic (`historic_subcategory_name`), it may need to be handled separately from the generic loop, or the loop needs to detect it and use a custom subquery.

### 4. Theme Merges + Sort Order — Schema + Seed + Backend

**Schema migration** — create `database/migrations/006_sort_order.sql`:
```sql
-- Add sort_order column for custom display ordering
ALTER TABLE theme_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
ALTER TABLE time_context ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;

-- Merge themes: trauma + accident → trauma/accident
UPDATE film_theme SET theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'trauma'
) WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'accident'
);
UPDATE theme_context SET theme_name = 'trauma/accident' WHERE theme_name = 'trauma';
DELETE FROM theme_context WHERE theme_name = 'accident';

-- Merge themes: technology + artificial_intelligence → AI/technology
UPDATE film_theme SET theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'technology'
) WHERE theme_context_id = (
    SELECT theme_context_id FROM theme_context WHERE theme_name = 'artificial_intelligence'
);
UPDATE theme_context SET theme_name = 'AI/technology' WHERE theme_name = 'technology';
DELETE FROM theme_context WHERE theme_name = 'artificial_intelligence';

-- Theme sort_order values (thematic groupings with gaps for separators)
UPDATE theme_context SET sort_order = CASE theme_name
    -- Group 1: Society
    WHEN 'social' THEN 100
    WHEN 'class struggle' THEN 101
    WHEN 'societal' THEN 102
    WHEN 'immigration' THEN 103
    WHEN 'political' THEN 104
    WHEN 'religion' THEN 105
    WHEN 'business' THEN 106
    WHEN 'censorship' THEN 107
    WHEN 'trial' THEN 108
    WHEN 'prison' THEN 109
    WHEN 'war' THEN 110
    WHEN 'tragedy' THEN 111
    WHEN 'apocalypse' THEN 112
    -- Group 2: Personal / Psychological
    WHEN 'trauma/accident' THEN 200
    WHEN 'psychological' THEN 201
    WHEN 'identity crisis' THEN 202
    WHEN 'disease' THEN 203
    WHEN 'amnesia' THEN 204
    WHEN 'death' THEN 205
    WHEN 'mourning' THEN 206
    WHEN 'addiction/drugs' THEN 207
    WHEN 'time passing' THEN 208
    WHEN 'evolution' THEN 209
    -- Group 3: Crime / Thriller
    WHEN 'investigation' THEN 300
    WHEN 'spy' THEN 301
    WHEN 'crime' THEN 302
    WHEN 'sex crime' THEN 303
    WHEN 'organized crime' THEN 304
    WHEN 'police violence' THEN 305
    WHEN 'corruption' THEN 306
    WHEN 'delinquency' THEN 307
    WHEN 'organized fraud' THEN 308
    WHEN 'mafia' THEN 309
    WHEN 'gangster' THEN 310
    WHEN 'serial killer' THEN 311
    WHEN 'chase/escape' THEN 312
    WHEN 'terrorism' THEN 313
    WHEN 'sect' THEN 314
    WHEN 'survival' THEN 315
    WHEN 'slasher' THEN 316
    -- Group 4: Sci-fi / Fantasy
    WHEN 'futuristic' THEN 400
    WHEN 'dystopia' THEN 401
    WHEN 'tales and legends' THEN 402
    WHEN 'supernatural' THEN 403
    WHEN 'sorcery' THEN 404
    WHEN 'alien contact' THEN 405
    WHEN 'paranormal' THEN 406
    WHEN 'time travel/loop' THEN 407
    WHEN 'virtual reality' THEN 408
    WHEN 'dream' THEN 409
    WHEN 'nonsense' THEN 410
    -- Group 5: Art & Sport
    WHEN 'art' THEN 500
    WHEN 'art: music' THEN 501
    WHEN 'art: cinema' THEN 502
    WHEN 'art: literature' THEN 503
    WHEN 'art: fashion' THEN 504
    WHEN 'art: painting' THEN 505
    WHEN 'art: sculpture' THEN 506
    WHEN 'art: theatre' THEN 507
    WHEN 'art: radio' THEN 508
    WHEN 'martial arts' THEN 509
    WHEN 'sport' THEN 520
    WHEN 'sport: individual' THEN 521
    WHEN 'sport: collective' THEN 522
    WHEN 'sport: tournament' THEN 523
    WHEN 'sport: motor' THEN 524
    -- Group 6: Miscellaneous
    WHEN 'nature' THEN 600
    WHEN 'AI/technology' THEN 601
    WHEN 'food/cooking' THEN 602
    WHEN 'party' THEN 603
    WHEN 'book' THEN 604
    ELSE 999
END;

-- Time period sort_order (chronological: future first, prehistoric last; seasons separate)
UPDATE time_context SET sort_order = CASE time_period
    WHEN 'future' THEN 1
    WHEN 'contemporary' THEN 2
    WHEN 'end 20th' THEN 3
    WHEN '30-year post-war boom' THEN 4
    WHEN 'WW2' THEN 5
    WHEN 'interwar' THEN 6
    WHEN 'WW1' THEN 7
    WHEN 'early 20th' THEN 8
    WHEN '19th' THEN 9
    WHEN 'modern age' THEN 10
    WHEN 'medieval' THEN 11
    WHEN 'antiquity' THEN 12
    WHEN 'prehistoric' THEN 13
    WHEN 'undetermined' THEN 14
    -- Seasons
    WHEN 'spring' THEN 100
    WHEN 'summer' THEN 101
    WHEN 'autumn' THEN 102
    WHEN 'winter' THEN 103
    ELSE 999
END;

-- Remove survival from motivations
DELETE FROM film_motivation WHERE motivation_id = (
    SELECT motivation_id FROM motivation_relation WHERE motivation_name = 'survival'
);
DELETE FROM motivation_relation WHERE motivation_name = 'survival';
```

**Taxonomy endpoint (`taxonomy.py`):** For dimensions with `sort_order` columns, ORDER BY `sort_order` instead of name. Add a set:
```python
SORTED_DIMENSIONS = {"themes", "time_periods"}
```
In the query builder, when `dimension in SORTED_DIMENSIONS`, use `ORDER BY lt.sort_order, lt.{name_col}` instead of `ORDER BY lt.{name_col}`.

**TaxonomyItem schema (`taxonomy.py` schemas):** Add optional `sort_order` field:
```python
class TaxonomyItem(BaseModel):
    id: int
    name: str
    film_count: int | None = None
    sort_order: int | None = None
```
Return `sort_order` from the query so the frontend can detect group boundaries.

### 5. Studios Filter — Backend + Frontend

**Backend — taxonomy.py:** Add to DIMENSION_MAP:
```python
"studios": ("studio", "studio_id", "studio_name", "production", "studio_id"),
```

**Backend — films.py:** Add `studios: list[str] | None = Query(None)` parameter. Add to `_taxonomy_filters`:
```python
(studios, "production", "studio_id", "studio", "studio_id", "studio_name"),
```

**Frontend — types/api.ts:** Add `studios: string[]` to FilterState and DEFAULT_FILTER_STATE. Add `"studios"` to ARRAY_FILTER_KEYS. Do NOT add to TAXONOMY_DIMENSIONS (studios uses a dropdown, not chips).

**Frontend — Sidebar.tsx:** Add a Studios dropdown (same pattern as Language). Fetch `GET /api/taxonomy/studios` in `useTaxonomy.ts`. Display as a Select with studio names + film counts. Only show studios with film_count > 0.

**Frontend — api/client.ts:** Include `studios` array in the query builder.

### 6. Remove Director Filter — Frontend

**Remove from Sidebar.tsx:** Delete the Director filter section (the `<div>` with "Director" label and Input).

**Remove from types/api.ts:** Remove `director: string` from `FilterState` and `DEFAULT_FILTER_STATE`.

**Remove from useFilterState.ts:** Remove director from URL param parsing and serialization.

**Remove from ActiveFilters.tsx:** Remove any director chip rendering.

**Remove from api/client.ts:** Remove director from the query builder params.

**Keep in films.py backend:** The `director` param stays in the backend for backward compatibility / API use, but the frontend no longer sends it.

### 7. Year Range Dual Slider — Frontend

Replace the two number inputs in Sidebar.tsx with a dual-handle range slider.

**Install:**
```bash
cd frontend && npm install react-slider
npm install -D @types/react-slider
```

**Implementation:** Create a `YearRangeSlider` component or inline it in Sidebar.tsx. Use `ReactSlider` with:
- `min={1900}`, `max={2030}` (or get from stats endpoint)
- `value={[yearMin, yearMax]}` (two handles)
- `onChange` updates local state, `onAfterChange` commits to filter state
- Display the selected range as text: "1990 — 2005"
- Style with Tailwind: dark track, amber handles/selected range

### 8. Theme/Time Group Separators — Frontend

The API now returns `sort_order` on each TaxonomyItem. In `FilterSection.tsx`, when rendering chips for themes or time_periods, detect group boundaries (where sort_order jumps by ≥50, i.e., different hundreds group) and insert a `<Separator />` (from shadcn/ui) between groups.

```tsx
{items.map((item, index) => {
    const prevOrder = index > 0 ? items[index - 1].sort_order : null;
    const showSeparator = prevOrder !== null && item.sort_order !== null 
        && Math.floor(item.sort_order / 100) !== Math.floor(prevOrder / 100);
    return (
        <>
            {showSeparator && <Separator className="my-1" />}
            <FilterChip ... />
        </>
    );
})}
```

### Important Technical Notes

1. **Migration order matters:** Run the migration SQL BEFORE updating seed_taxonomy.sql, because the migration renames/merges existing data. The updated seed_taxonomy.sql should reflect the final state (with merged theme names and sort_order values) for fresh installs.

2. **Don't break existing data.** The migration carefully moves `film_theme` rows before deleting merged themes. With only 3 reference films, this is low-risk, but the pattern must be correct for future bulk data.

3. **Categories filter is special.** It's the only dimension with a composite key (category_name + historic_subcategory_name). The generic `_taxonomy_filters` loop may need a special case for it, or handle it separately before the loop.

4. **The `sort_order` column defaults to 0** for any new values added later. The ORDER BY is `sort_order, name`, so new items with sort_order=0 will appear at the top. Consider using a high default (999) so unsorted items appear at the end.

5. **React Slider types:** `react-slider` has TypeScript types via `@types/react-slider`. Import as `import ReactSlider from 'react-slider'`.

6. **Keep the backend `director` param.** Only remove it from the frontend UI. The API stays backward-compatible.

### Validation

After all changes:

1. `psql -U postgres -d film_database -f database/migrations/006_sort_order.sql` — runs without errors
2. `uvicorn backend.app.main:app --reload` — starts without errors
3. `GET /api/taxonomy/categories` — shows Documentary, Historical, Historical: biopic, Historical: event, Historical: western, etc.
4. `GET /api/taxonomy/themes` — sorted by thematic groups with sort_order values, trauma/accident merged, AI/technology merged
5. `GET /api/taxonomy/time_periods` — future first, prehistoric near end, seasons last
6. `GET /api/taxonomy/studios` — returns studios with film counts
7. `GET /api/taxonomy/motivations` — survival is gone
8. `GET /api/films?themes=art` — returns films tagged with any art: sub-theme (Mulholland Drive)
9. `GET /api/films?categories=Historical` — returns films with any Historical subcategory
10. `GET /api/films?themes=social&themes=political` — returns only films with BOTH (AND logic)
11. Frontend: Director filter gone from sidebar
12. Frontend: Year range shows dual-handle slider
13. Frontend: Studios dropdown in sidebar
14. Frontend: Theme section shows separators between thematic groups
15. Frontend: Time periods in chronological order with seasons at end
16. All existing filters still work

Do NOT run the server or npm commands yourself. Just create/modify the files correctly. The user will run the migration and test manually.

---
