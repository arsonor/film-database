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

## Step 8.6 Prompt — Editable Categories, Financials & Awards

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 8.6 specification (sections A through C). Then read ALL of the following files:

**Backend — files to modify:**
- `backend/app/schemas/film.py` — `FilmUpdate` class (add `awards` field)
- `backend/app/routers/films.py` — `update_film()` endpoint (add awards clear-and-reinsert logic)

**Frontend — files to modify:**
- `frontend/src/pages/FilmDetailPage.tsx` — Add `EditableTagSection` for categories, add `EditableFinancials` component, pass new props to `AwardsTable`
- `frontend/src/components/films/AwardsTable.tsx` — Make editable (add/remove awards, toggle won/nominated)

**Frontend — new file (optional, can be inlined in FilmDetailPage):**
- `frontend/src/components/films/EditableFinancials.tsx` — Editable budget/revenue with pencil toggle

**Files to read for patterns and context:**
- `frontend/src/components/films/EditableTagSection.tsx` — Edit mode pattern (pencil toggle, save/cancel, API call)
- `frontend/src/components/films/SectionHeading.tsx` — Section header with optional edit button
- `frontend/src/api/client.ts` — `updateFilm()` function (already sends partial data to PUT)
- `frontend/src/lib/utils.ts` — `formatCurrency()` helper
- `frontend/src/types/api.ts` — `AwardOut` interface, `FilmDetail` interface

### Goal

Make three read-only sections on the film detail page editable so the user can correct mistakes from Claude enrichment or TMDB data. Use the same edit pattern (pencil icon → edit mode → save/cancel) established by `EditableTagSection`.

### Task 1 — Editable Categories (frontend only)

The backend `PUT /api/films/{id}` already supports `categories` in `FilmUpdate`. Categories currently appear as badges in the hero section but are NOT in the editable Classification section.

**In `FilmDetailPage.tsx`**, add an `EditableTagSection` for categories in the Classification section (alongside the existing cinema_types and cultural_movements):

```tsx
<EditableTagSection
  filmId={film.film_id}
  dimension="categories"
  currentValues={film.categories}
  onSaved={refetch}
/>
```

The hero section badges stay read-only — they refresh automatically when `refetch` is called after saving in the section below.

### Task 2 — Editable Budget & Revenue (frontend only)

The backend already supports `budget` and `revenue` in `FilmUpdate`.

Create an `EditableFinancials` component (or inline in `FilmDetailPage.tsx`) for the Production section. Pattern:
- **View mode:** Shows formatted currency (using `formatCurrency`) for budget and revenue, with a pencil icon
- **Edit mode:** Two number inputs (labeled "Budget" and "Revenue"), pre-filled with current values. Save/Cancel buttons
- Save calls `updateFilm(filmId, { budget: number | null, revenue: number | null })`
- Values are in USD as integers (e.g., `160000000` for $160M). No need for shorthand — raw number input is fine
- Handle null gracefully: show "—" in view mode, empty input in edit mode
- Match the visual style of `EditableTagSection` (same pencil icon, same save/cancel button sizes)

Replace the current read-only financials block in the Production section with this component.

### Task 3 — Editable Awards (backend + frontend)

**Backend — `backend/app/schemas/film.py`:**

Add `awards` to `FilmUpdate`:
```python
class FilmUpdate(BaseModel):
    # ... existing fields ...
    awards: list[dict] | None = None
```

**Backend — `backend/app/routers/films.py`:**

In `update_film()`, add awards handling after the existing `streaming_platforms` block (before `await db.commit()`). Use the same clear-and-reinsert pattern:
```python
# Awards
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

**Frontend — `frontend/src/components/films/AwardsTable.tsx`:**

Make the component editable. Add props `filmId: number` and `onSaved: () => void`. When clicking the pencil icon:
- Each award row shows:
  - A toggle or small dropdown to switch between "Won" and "Nominated"
  - An X button to remove the award
- Save button sends `updateFilm(filmId, { awards: editedAwards })` where `editedAwards` is the array of `{ festival_name, category, year, result }` dicts
- Cancel reverts to original values

**In `FilmDetailPage.tsx`:** Pass the new props to `AwardsTable`:
```tsx
<AwardsTable awards={film.awards} filmId={film.film_id} onSaved={refetch} />
```

### Important Notes

1. **No new npm dependencies needed** — everything uses existing shadcn/ui components (Button, Input, Badge)
2. **The `updateFilm` function in `api/client.ts` already handles arbitrary partial data** — it sends whatever object it receives to `PUT /api/films/{id}`. No changes needed there.
3. **The pencil icon / edit toggle / save-cancel pattern is established by `SectionHeading` + `EditableTagSection`** — follow the same visual pattern for consistency
4. **Categories use the same `EditableTagSection` component as other taxonomy dimensions** — the backend handles the special composite key (Historical: subcategory) transparently

### Validation

1. Categories: pencil icon appears in Classification section → can remove/add categories → save → hero badges update
2. Budget/Revenue: pencil icon in Production section → number inputs → save → formatted currency updates
3. Budget/Revenue with null values: film with no budget shows "—", edit mode shows empty input, saving empty clears the value
4. Awards: pencil icon → each row shows won/nominated toggle + X remove button
5. Toggle an award from "Nominated" to "Won" → save → trophy turns gold
6. Remove an award → save → row disappears
7. All changes persist after page reload
8. Films with no awards: "No awards recorded" message still shows, no edit functionality needed for empty state

Do NOT run the server or npm commands yourself. Just create/modify the files correctly. The user will run and test manually.
