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
| 8.6 | Editable categories, financials & awards | 🔄 IN PROGRESS | Make categories, budget/revenue, awards editable on detail page |
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

## Step 8.5: Auto-link Franchise Sequels via TMDB Collection ✅

- Migration 009: `tmdb_collection_id` column on film table + index
- `tmdb_service.py`: captures `belongs_to_collection` from TMDB API response
- `tmdb_mapper.py`: extracts `tmdb_collection_id` into film dict
- `films.py` create endpoint: stores collection_id + auto-links siblings via `film_sequel`
- `schema.sql`: updated for fresh installs
- New scripts: `backfill_collection_ids.py` (backfill existing films), `refresh_streaming.py` (refresh streaming platforms from TMDB)

---

## Step 8.6: Editable Categories, Financials & Awards

### Goal

Make three currently read-only sections on the film detail page editable: categories (as tags), budget/revenue (as number inputs), and awards (toggle won/nominated). These are fields that Claude or TMDB can get wrong and the user needs to be able to correct.

### A. Categories — Frontend Only (Simple)

**Problem:** Categories are shown as badges in the hero section but not in the editable Classification section below. The backend `PUT /api/films/{id}` already handles `update.categories` — just need the UI.

**Fix in `FilmDetailPage.tsx`:** Add an `EditableTagSection` for `categories` in the Classification section, alongside cinema_types and cultural_movements:
```tsx
<EditableTagSection
  filmId={film.film_id}
  dimension="categories"
  currentValues={film.categories}
  onSaved={refetch}
/>
```

**Note:** Categories in the hero section stay as read-only badges (they update when `refetch` is called after editing in the section below).

### B. Budget & Revenue — Frontend Only (Simple)

**Problem:** Budget and revenue are displayed as read-only text in the Production section. The backend `PUT /api/films/{id}` already accepts `budget` and `revenue` in `FilmUpdate` — just need editable inputs.

**Fix:** Create a small `EditableFinancials` component (or inline it in `FilmDetailPage.tsx`) in the Production section. Pattern:
- View mode: shows formatted currency (using existing `formatCurrency`)
- Edit mode (pencil icon toggle): two number inputs for budget and revenue, with Save/Cancel buttons
- Save sends `PUT /api/films/{id}` with `{ budget: number, revenue: number }`
- Values are stored in USD as integers (no decimals). Input should accept raw numbers (e.g. `160000000` for $160M) or optionally support shorthand entry

Component should handle:
- Null values gracefully (show "—" in view mode, empty input in edit mode)
- The pencil icon and save/cancel pattern should match `EditableTagSection` for visual consistency

### C. Awards — Backend + Frontend (Medium)

**Problem:** Awards are displayed in a read-only `AwardsTable`. The user cannot toggle won/nominated or remove incorrect awards. The backend `FilmUpdate` schema has no `awards` field, and the `update_film` endpoint doesn't handle awards.

**Backend changes:**

1. **`backend/app/schemas/film.py`** — Add `awards` field to `FilmUpdate`:
```python
class FilmUpdate(BaseModel):
    # ... existing fields ...
    awards: list[dict] | None = None  # [{"festival_name": "...", "category": "...", "year": 2001, "result": "won|nominated"}]
```

2. **`backend/app/routers/films.py`** — In `update_film()`, add awards handling after the existing streaming_platforms block, using the same clear-and-reinsert pattern:
```python
if update.awards is not None:
    await db.execute(text("DELETE FROM award WHERE film_id = :fid"), {"fid": film_id})
    for award in update.awards:
        if not isinstance(award, dict) or not award.get("festival_name"):
            continue
        if award.get("result") not in ("won", "nominated"):
            continue
        await db.execute(
            text("""
                INSERT INTO award (film_id, festival_name, category, award_year, result)
                VALUES (:fid, :festival, :category, :year, :result)
            """),
            {
                "fid": film_id,
                "festival": award["festival_name"],
                "category": award.get("category"),
                "year": award.get("year"),
                "result": award["result"],
            },
        )
```

**Frontend changes:**

3. **`frontend/src/components/films/AwardsTable.tsx`** — Make it editable. Add props for `filmId` and `onSaved` callback. When editing:
- Each award row gets a toggle button to switch between "Won" and "Nominated" (or a small dropdown)
- Each row gets an X button to remove it
- A Save/Cancel button pair at the bottom
- Save sends `PUT /api/films/{id}` with `{ awards: [...] }` (the full awards array)

4. **`frontend/src/api/client.ts`** — The existing `updateFilm` function already sends arbitrary partial data to PUT — no change needed.

### Validation

After implementation:
1. Film detail page: Categories section appears in Classification with edit pencil
2. Edit categories: remove a tag, add one from dropdown, save → hero badges update
3. Production section: Budget & Revenue show pencil icon
4. Edit financials: change budget value, save → formatted currency updates
5. Awards section: pencil icon → each row shows won/nominated toggle + X remove
6. Toggle an award from "Nominated" to "Won" → save → trophy icon changes to gold
7. Remove an award → save → row disappears
8. All edits persist after page reload

---


