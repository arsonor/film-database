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
| 7 | Film detail view + edit | 🔄 IN PROGRESS | Full detail page, tag editing, vu toggle, external links, person navigation |
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

## Step 6.5: Taxonomy Refinements + Filter UX Fixes ✅

- Migration `006_sort_order.sql` — sort_order columns, theme merges (trauma/accident, AI/technology), motivation cleanup
- Backend: AND logic (HAVING COUNT) in all taxonomy filters, parent expansion for hierarchical dims (themes, categories)
- Backend: Categories filter handles composite "Parent: sub" format, studios filter + taxonomy dimension
- Frontend: Director filter removed, dual-handle year range slider, studios dropdown, theme/time group separators

---

## Step 7: Film Detail View + Edit

### Goal
Build a rich, visually compelling film detail page that displays all metadata from the `GET /api/films/{film_id}` endpoint. Include tag editing capabilities, a quick seen/unseen toggle, clickable person names/photos, external links, and a placeholder for the future "Similar Films" recommendation carousel (steps 9-10).

### A. Frontend API Client + Types — `frontend/src/api/client.ts` + `frontend/src/types/api.ts`

**Types (`api.ts`):** Add full TypeScript interfaces matching the backend `FilmDetail` response:

```typescript
export interface FilmTitle {
  language_code: string;
  language_name: string;
  title: string;
  is_original: boolean;
}

export interface CrewMember {
  person_id: number;
  firstname: string | null;
  lastname: string;
  role: string;
  photo_url: string | null;
}

export interface CastMember {
  person_id: number;
  firstname: string | null;
  lastname: string;
  character_name: string | null;
  cast_order: number | null;
  photo_url: string | null;
}

export interface FilmSetPlace {
  continent: string | null;
  country: string | null;
  state_city: string | null;
  place_type: string;
}

export interface SourceOut {
  source_type: string;
  source_title: string | null;
  author: string | null;
}

export interface AwardOut {
  festival_name: string;
  category: string | null;
  year: number | null;
  result: string | null;
}

export interface FilmRelation {
  related_film_id: number;
  related_film_title: string;
  relation_type: string;
}

export interface FilmDetail {
  film_id: number;
  original_title: string;
  duration: number | null;
  color: boolean;
  first_release_date: string | null;
  summary: string | null;
  vu: boolean;
  poster_url: string | null;
  backdrop_url: string | null;
  imdb_id: string | null;
  tmdb_id: number | null;
  budget: number | null;
  revenue: number | null;
  titles: FilmTitle[];
  categories: string[];
  cinema_types: string[];
  cultural_movements: string[];
  themes: string[];
  characters: string[];
  character_contexts: string[];
  motivations: string[];
  atmospheres: string[];
  messages: string[];
  time_periods: string[];
  place_contexts: string[];
  set_places: FilmSetPlace[];
  crew: CrewMember[];
  cast: CastMember[];
  studios: string[];
  sources: SourceOut[];
  awards: AwardOut[];
  streaming_platforms: string[];
  sequels: FilmRelation[];
}
```

**API client (`client.ts`):** Add functions:
```typescript
export async function fetchFilmDetail(filmId: number): Promise<FilmDetail> {
  return fetchJson<FilmDetail>(`${BASE}/films/${filmId}`);
}

export async function updateFilm(filmId: number, data: Partial<FilmDetail>): Promise<void> {
  const res = await fetch(`${BASE}/films/${filmId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, `Update failed: ${res.statusText}`);
}

export async function toggleVu(filmId: number, vu: boolean): Promise<void> {
  return updateFilm(filmId, { vu } as any);
}
```

### B. Hook — `frontend/src/hooks/useFilmDetail.ts`

Create a hook that fetches the full film detail:
```typescript
export function useFilmDetail(filmId: number) {
  // Returns { film, loading, error, refetch }
  // Fetches on mount and when filmId changes
  // Provides a refetch function for after edits
}
```

### C. Film Detail Page — `frontend/src/pages/FilmDetailPage.tsx`

Replace the current placeholder with a full detail page. The page layout has two main zones:

**1. Hero section (top):**
- Full-width backdrop image (`backdrop_url`) with gradient overlay fading to background
- Overlaid on the left: large poster image (`poster_url`), roughly 300px wide
- Overlaid on the right of poster: primary info block:
  - Original title (large heading)
  - Localized titles below (smaller, muted — list the non-original titles from `titles[]`)
  - Year · Duration · Color/B&W
  - Categories as badges
  - Director name(s) (from crew where role="Director")
  - **Seen/Unseen toggle button** — prominently placed, clickable (calls `toggleVu`). Green Eye icon if seen, grey outline if unseen. Clicking toggles immediately (optimistic update) then syncs with API.
  - **External links row:** small icon buttons linking to:
    - TMDB: `https://www.themoviedb.org/movie/{tmdb_id}`
    - IMDb: `https://www.imdb.com/title/{imdb_id}` (if `imdb_id` exists)
    - Allociné: `https://www.google.com/search?q=allocine+{encodeURIComponent(original_title)}+{year}` (Google search fallback since Allociné has no direct TMDB mapping)
    - Wikipedia: `https://en.wikipedia.org/wiki/Special:Search/{encodeURIComponent(original_title)}_(film)`

**2. Content sections (below hero), organized in a responsive grid/column layout:**

Each section is a card or always-open section with a consistent heading. Use a reusable section component.

- **Synopsis** — `summary` text, full paragraph
- **Cast & Crew**
  - Cast: horizontal scrollable row of person cards (photo thumbnail from TMDB, actor name, character name). Photos use `https://image.tmdb.org/t/p/w185{photo_url}` if photo_url starts with `/`. Each card is **clickable** → navigates to `/browse?q={firstname}+{lastname}` (sets the search bar to the person's name so it shows all their films)
  - Crew: grouped by role. Director, Writer, Cinematographer, Composer listed with name + photo. Same click behavior.
- **Classification** — a compact tag cloud / grouped badges showing:
  - Cinema types, Cultural movements
  - Each tag group has an **Edit** button nearby (pencil icon) that opens an inline edit mode (or a dialog) for that dimension — described in section F below
- **Context & Themes** — Tags displayed as badges:
  - Themes, Characters, Character Contexts, Motivations, Atmosphere, Messages
  - Same edit capability
- **Setting** — Time periods + Place contexts + Geography (set_places formatted as "Country, City (diegetic)" etc.)
- **Production** — Studios list, Source/Origin info, Budget & Revenue (formatted as currency if available)
- **Awards** — Table or list: Festival | Category | Year | Won/Nominated, with a trophy icon for wins
- **Streaming** — Platform badges (Netflix, Prime Video, etc.)
- **Related Films** — If `sequels[]` is non-empty, show linked film titles with relation type (sequel, prequel, remake…). Each links to `/films/{related_film_id}`.
- **Similar Films** *(placeholder)* — An empty section with a subtle message: "Recommendations coming soon" and a placeholder carousel skeleton. This will be populated in steps 9-10 with the recommendation engine output. Keep the component structure ready: `SimilarFilmsCarousel` that accepts a `filmId` prop and will eventually call a `/api/films/{id}/recommendations` endpoint.

### D. Person Navigation — Click to Browse

When a person (cast or crew) is clicked, navigate to `/browse?q={encodeURIComponent(fullName)}`. This leverages the existing full-text search which already searches across casting and crew person names. The `BrowsePage` will receive the `q` param from the URL and display matching films.

Verify in `useFilterState.ts` that the `q` param is properly read from the URL on page load (it should already work since search is URL-synced).

### E. Seen/Unseen Quick Toggle

The seen/unseen button in the hero section should:
1. Show current state visually (filled green Eye for seen, outline Eye for unseen)
2. On click: optimistically update the UI immediately
3. Send `PUT /api/films/{film_id}` with `{ vu: newValue }`
4. On error: revert the optimistic update and show a brief toast/notification
5. The backend `update_film` endpoint already supports partial updates including `vu`

### F. Tag Editing — Edit Mode for Taxonomy Dimensions

Add an **Edit** button (pencil icon) on each taxonomy section header. When clicked:
1. The section switches to "edit mode" — the existing tags become removable (X button on each)
2. A combobox/autocomplete appears below, fetching values from `GET /api/taxonomy/{dimension}` to suggest available tags to add
3. **Save** button sends `PUT /api/films/{film_id}` with the updated array for that dimension
4. **Cancel** button reverts to the original values

Implementation approach:
- Create a reusable `EditableTagSection` component that wraps any taxonomy dimension
- Props: `filmId`, `dimension` (taxonomy key), `currentValues` (string[]), `onSaved` (callback to refetch)
- Uses the existing `fetchTaxonomy` to get all possible values for the dimension
- On save, calls `updateFilm` with just the changed dimension field

This keeps editing lightweight — no need for a full-page edit form. Each section is independently editable.

### G. Backend: PATCH for Quick vu Toggle (Optional Optimization)

The existing `PUT /api/films/{film_id}` works for all updates, but for a single boolean toggle it sends a lot of unnecessary NULL fields. Consider adding a lightweight endpoint:

```python
@router.patch("/films/{film_id}/vu")
async def toggle_vu(film_id: int, vu: bool = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("UPDATE film SET vu = :vu WHERE film_id = :fid RETURNING film_id"),
        {"fid": film_id, "vu": vu}
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")
    await db.commit()
    return {"film_id": film_id, "vu": vu}
```

If implemented, the frontend `toggleVu` function uses `PATCH /api/films/{film_id}/vu?vu=true` instead of PUT.

### H. UI Component Library — New Components Needed

**Install additional shadcn/ui components** (if not already present):
```bash
cd frontend
npx shadcn@latest add dialog
npx shadcn@latest add tabs
npx shadcn@latest add tooltip
npx shadcn@latest add toggle
npx shadcn@latest add command   # for combobox/autocomplete in edit mode
npx shadcn@latest add popover   # for combobox
npx shadcn@latest add toast     # for edit save feedback
```

**Custom components to create:**
- `PersonCard` — Thumbnail photo + name + role/character, clickable
- `SectionHeading` — Consistent section title with optional edit button
- `EditableTagSection` — View/edit mode toggle for taxonomy tags
- `ExternalLinks` — Row of icon buttons for TMDB, IMDb, Allociné, Wikipedia
- `AwardsTable` — Formatted awards display
- `SimilarFilmsCarousel` — Placeholder skeleton for future recommendations

### Design Guidelines

Maintain the existing dark theme (charcoal #0f0f0f, amber #f59e0b accent). The detail page should feel like a blend of Letterboxd's film detail and TMDB's rich metadata display:
- Backdrop image with strong gradient overlay (bottom → background color)
- Poster with subtle shadow/border
- Muted color palette for text, amber for interactive elements (buttons, links, edit icons)
- Smooth transitions between view and edit modes
- Mobile responsive: poster + info stack vertically on small screens, cast scrolls horizontally

### Validation

After implementation:
1. Navigate to `/films/1` (or any seeded film) — full detail renders
2. Backdrop image displays with gradient overlay
3. Poster shows on the left in desktop, stacks on mobile
4. All taxonomy sections populated with correct data
5. Cast section shows photos, names, characters in a scrollable row
6. Crew section shows director, writer, cinematographer grouped by role
7. Click any person → navigates to `/browse?q=PersonName` → browse page shows their films
8. Seen/unseen toggle: click toggles icon + sends API update
9. External links: TMDB and IMDb links open correct pages in new tab
10. Edit mode on any taxonomy section: can remove tags, add from dropdown, save
11. Awards section displays correctly (or empty if no awards)
12. "Similar Films" placeholder section visible with "coming soon" message
13. Back button returns to browse page preserving previous filter state
14. Mobile responsive: all sections readable on phone screen

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
