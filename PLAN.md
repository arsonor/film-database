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
| 8.5 | Auto-link franchise sequels | 🔄 IN PROGRESS | TMDB collection → film_sequel auto-creation |
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

## Step 6.5: Taxonomy Refinements + Filter UX Fixes ✅

- Migration `006_sort_order.sql` — sort_order columns, theme merges (trauma/accident, AI/technology), motivation cleanup
- Backend: AND logic (HAVING COUNT) in all taxonomy filters, parent expansion for hierarchical dims (themes, categories)
- Backend: Categories filter handles composite "Parent: sub" format, studios filter + taxonomy dimension
- Frontend: Director filter removed, dual-handle year range slider, studios dropdown, theme/time group separators

## Step 7: Film Detail View + Edit ✅

- Full detail page with cinematic hero section (backdrop gradient, poster, meta, vu toggle, external links)
- Cast/crew sections with TMDB photos, clickable → `/browse?q=Name`
- All taxonomy sections with inline editing (EditableTagSection)
- Awards table, streaming badges, related films, similar films placeholder
- Backend: PATCH `/films/{id}/vu` for lightweight toggle
- Bug fixes: tag dropdown cap removed (was limited to 15), person photo tmdb_id mismatch fixed
- New script: `refresh_person_photos.py` (name-based matching against TMDB movie credits)

## Step 8: Add Film Workflow ✅

- Backend: `add_film.py` router with GET `/add-film/search` (TMDB dual-locale + dedup + already_in_db flag) and POST `/add-film/enrich` (TMDB details + mapper + Claude enrichment, graceful failure with enrichment_failed flag)
- Frontend: `AddFilmPage.tsx` 3-step wizard (Search → Enriching with animated messages → Review with editable tags → Save via POST `/api/films` → redirect to detail page)
- Header "+" button navigating to `/add`
- Enrichment quality: rewritten system prompt (tag selection philosophy, time period rules, place/theme centrality, empty dims OK), improved taxonomy section with inline notes per dimension
- New taxonomy values: soldier, military, ship, communication, invasion, patriotic, history revisited, traditionalist/way of life, costume (migration 007)
- Underscore-to-space renames across 9 values (migration 008)
- Fixed Mulholland Drive reference example (missing comma bug)

---

## Step 8.5: Auto-link Franchise Sequels via TMDB Collection

### Goal

When a film is added to the database, automatically detect if it belongs to a TMDB collection (franchise like Lord of the Rings, Star Wars, etc.) and create `film_sequel` relationships with any other films from the same collection already in the DB. The detail page already reads and displays these relationships — this step just populates the data.

### A. Schema: Add `tmdb_collection_id` to film table

Migration `database/migrations/009_collection_id.sql` (already created):
```sql
ALTER TABLE film ADD COLUMN IF NOT EXISTS tmdb_collection_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_film_tmdb_collection_id ON film(tmdb_collection_id);
```

Also update `database/schema.sql` for fresh installs: add `tmdb_collection_id INTEGER,` after the `revenue` line in the film CREATE TABLE, and add the index.

### B. TMDB Service: Capture collection data

In `backend/app/services/tmdb_service.py`, method `get_film_details()`: add `belongs_to_collection` to the return dict. The TMDB API already returns this field:
```json
{ "belongs_to_collection": { "id": 119, "name": "The Lord of the Rings Collection" } }
```

Add to the return dict:
```python
"belongs_to_collection": data.get("belongs_to_collection"),
```

### C. TMDB Mapper: Pass collection ID through

In `backend/app/services/tmdb_mapper.py`, method `map_film_to_db()`: extract collection ID and add to the `film` dict:
```python
collection = tmdb_data.get("belongs_to_collection")
if collection and isinstance(collection, dict):
    film["tmdb_collection_id"] = collection.get("id")
else:
    film["tmdb_collection_id"] = None
```

### D. Film Creation: Store collection_id + auto-link sequels

In `backend/app/routers/films.py`, endpoint `create_film()`:

1. Add `tmdb_collection_id` to the INSERT INTO film statement and params
2. After all existing junction inserts (before `await db.commit()`), add auto-linking:

```python
tmdb_collection_id = film.get("tmdb_collection_id")
if tmdb_collection_id:
    coll_result = await db.execute(
        text("SELECT film_id FROM film WHERE tmdb_collection_id = :cid AND film_id != :fid"),
        {"cid": tmdb_collection_id, "fid": film_id},
    )
    sibling_ids = [row[0] for row in coll_result.fetchall()]
    for sibling_id in sibling_ids:
        await db.execute(
            text("""INSERT INTO film_sequel (film_id, related_film_id, relation_type)
                    VALUES (:fid, :rid, 'sequel') ON CONFLICT DO NOTHING"""),
            {"fid": min(sibling_id, film_id), "rid": max(sibling_id, film_id)},
        )
```

### Validation

1. Run migration: `psql -U postgres -d film_database -f database/migrations/009_collection_id.sql`
2. Restart backend
3. Add "The Lord of the Rings: The Return of the King" (Fellowship + Two Towers already in DB)
4. Detail page for Return of the King shows Related Films with links to the other two
5. Fellowship and Two Towers detail pages also show the new links
6. Adding a non-franchise film creates no sequel relationships

---
