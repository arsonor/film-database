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
- Backend: `add_film.py` router with GET `/add-film/search` (TMDB dual-locale search + dedup + already_in_db flag) and POST `/add-film/enrich` (TMDB details + French data + watch providers → TMDBMapper → ClaudeEnricher, graceful failure with enrichment_failed flag). Registered in main.py.
- Backend: `schemas/add_film.py` with TMDBSearchResult, TMDBSearchResponse, EnrichRequest, EnrichmentPreview (with enrichment_failed flag)
- Frontend: `AddFilmPage.tsx` 3-step wizard — Search (title + year, TMDB results grid with posters, "already in database" badges) → Enriching (animated loading with rotating progress messages) → Review (full editable preview with InlineTagEditor per taxonomy dimension, streaming, awards) → Save via existing POST `/api/films` → redirect to `/films/{new_id}`
- Frontend: Header "+" / "Add Film" button, `/add` route in App.tsx, searchTMDB/enrichFilm/saveFilm in api/client.ts, TMDBSearchResult/EnrichmentPreview in types/api.ts
- Enrichment quality improvements: rewritten claude_enricher.py system prompt with tag selection philosophy (tags must characterize the film as a whole, not incidental details), explicit time period rules (no contemporary+end 20th for post-2000), place/environment centrality rules, empty dimensions allowed, inline notes per taxonomy section
- New taxonomy values via migration 007: soldier, military, ship, communication, invasion, patriotic, history revisited, traditionalist/way of life, costume
- Underscore-to-space renames via migration 008: class struggle, identity crisis, police violence, black and white, non linear narrative, slow cinema, unreliable narrator, femme fatale, anti establishment
- Fixed Mulholland Drive reference example in taxonomy_config.py (missing comma between "amnesia" and "investigation")
- All three synced: seed_taxonomy.sql + taxonomy_config.py + migrations

---

## Step 8.5 Prompt — Auto-link Franchise Sequels via TMDB Collection

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 8.5 specification (sections A through D). Then read ALL of the following files:

**Backend — files to modify:**
- `backend/app/services/tmdb_service.py` — `get_film_details()` method return dict (add `belongs_to_collection` field)
- `backend/app/services/tmdb_mapper.py` — `map_film_to_db()` method, the `film` dict it builds (add `tmdb_collection_id`)
- `backend/app/routers/films.py` — `create_film()` endpoint: the INSERT INTO film statement + auto-link logic after all junction inserts
- `database/schema.sql` — film table CREATE statement (add `tmdb_collection_id` column + index for fresh installs)

**Already created (do NOT recreate):**
- `database/migrations/009_collection_id.sql` — adds `tmdb_collection_id INTEGER` column + index to existing film table

**Read for context:**
- `backend/app/schemas/film.py` — FilmCreate, FilmDetail schemas (no changes needed)
- `frontend/src/pages/FilmDetailPage.tsx` — already displays sequels from `film_sequel` table (no changes needed)

### Goal

When a film is added via `POST /api/films`, automatically detect if it belongs to a TMDB collection (franchise) and create `film_sequel` rows linking it to other films from the same collection already in the DB. The detail page already reads and displays these — this step just populates the data.

### Changes (4 files to modify):

**1. `backend/app/services/tmdb_service.py`**

In `get_film_details()`, the TMDB API response includes `belongs_to_collection`:
```json
{ "belongs_to_collection": { "id": 119, "name": "The Lord of the Rings Collection" } }
```

Add this to the return dict (after the existing fields, e.g. after `"french_title"`):
```python
"belongs_to_collection": data.get("belongs_to_collection"),
```

**2. `backend/app/services/tmdb_mapper.py`**

In `map_film_to_db()`, after building the `film` dict, extract the collection ID:
```python
collection = tmdb_data.get("belongs_to_collection")
if collection and isinstance(collection, dict):
    film["tmdb_collection_id"] = collection.get("id")
else:
    film["tmdb_collection_id"] = None
```

**3. `backend/app/routers/films.py`**

In `create_film()`:

a) Add `tmdb_collection_id` to the INSERT INTO film SQL statement and its params dict:
```sql
INSERT INTO film (
    original_title, duration, color, first_release_date, summary,
    poster_url, backdrop_url, imdb_id, tmdb_id, budget, revenue,
    tmdb_collection_id
) VALUES (
    :original_title, :duration, :color, :first_release_date, :summary,
    :poster_url, :backdrop_url, :imdb_id, :tmdb_id, :budget, :revenue,
    :tmdb_collection_id
) RETURNING film_id
```
Add `"tmdb_collection_id": film.get("tmdb_collection_id")` to the params.

b) After all existing junction inserts (after geography, before `await db.commit()`), add auto-linking:
```python
# Auto-link franchise sequels via TMDB collection
tmdb_collection_id = film.get("tmdb_collection_id")
if tmdb_collection_id:
    coll_result = await db.execute(
        text("""
            SELECT film_id FROM film
            WHERE tmdb_collection_id = :cid AND film_id != :fid
        """),
        {"cid": tmdb_collection_id, "fid": film_id},
    )
    sibling_ids = [row[0] for row in coll_result.fetchall()]
    for sibling_id in sibling_ids:
        await db.execute(
            text("""
                INSERT INTO film_sequel (film_id, related_film_id, relation_type)
                VALUES (:fid, :rid, 'sequel')
                ON CONFLICT DO NOTHING
            """),
            {"fid": min(sibling_id, film_id), "rid": max(sibling_id, film_id)},
        )
    if sibling_ids:
        logger.info("Auto-linked %d sequel(s) via collection %d", len(sibling_ids), tmdb_collection_id)
```

**4. `database/schema.sql`**

In the film CREATE TABLE statement, add after the `revenue BIGINT` line:
```sql
    tmdb_collection_id INTEGER,                -- TMDB collection ID for franchise auto-linking
```

After the existing film indexes, add:
```sql
CREATE INDEX IF NOT EXISTS idx_film_tmdb_collection_id ON film(tmdb_collection_id);
```

### What NOT to change
- No frontend changes — the detail page already displays sequels from `film_sequel`
- No changes to `GET /api/films/{film_id}` — it already loads and returns sequels
- Do NOT recreate `database/migrations/009_collection_id.sql` — it's already written
- No changes to schemas — `FilmCreate` uses `film: dict` so the new field passes through

### Validation
1. Run migration: `psql -U postgres -d film_database -f database/migrations/009_collection_id.sql`
2. Restart backend
3. Add "The Lord of the Rings: The Return of the King" via the Add Film page (Fellowship and Two Towers should already be in DB)
4. After save, the detail page for Return of the King shows "Related Films" with links to Fellowship and Two Towers
5. Check Fellowship's detail page — it should also show links to the other two
6. Add a non-franchise film (e.g., "Amélie") — no sequel relationships created, no errors

Do NOT run the server or npm commands yourself. Just create/modify the files correctly. The user will run and test manually.
