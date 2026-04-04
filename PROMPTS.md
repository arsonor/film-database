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

Read CLAUDE.md, then PLAN.md (Step 13), then these files:
- `backend/app/routers/films.py` (full file — focus on `get_film()`)
- `backend/app/database.py`
- `frontend/src/hooks/useFilms.ts`
- `frontend/src/hooks/useFilmDetail.ts`
- `frontend/src/hooks/useTaxonomy.ts`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/App.tsx`
- `frontend/package.json`

### Part A — Backend: Parallelize film detail queries

In `backend/app/database.py`:
- Increase `pool_size` from 5 to 10 (keep `max_overflow=10`)
- Export `engine` is already done — no other changes needed

In `backend/app/routers/films.py`, rewrite `get_film()`:

1. Keep the initial core film query (`SELECT * FROM film WHERE film_id = :fid`) — this must run first to check the film exists (404 if not found).

2. After the core film row is confirmed, run ALL remaining queries in parallel using `asyncio.gather()`. Since a single SQLAlchemy `AsyncSession` serializes queries on its connection, each parallel query must use its own independent connection. Add this helper at module level:

```python
import asyncio

async def _parallel_query(sql: str, params: dict) -> list:
    """Run a single query using its own connection for true parallelism."""
    async with engine.connect() as conn:
        result = await conn.execute(text(sql), params)
        return result.fetchall()
```

3. Replace the sequential section (from "titles" through "sequels") with a single `asyncio.gather()` block. Define all 17 queries as a list of `_parallel_query(sql, {"fid": film_id})` calls, then unpack the results:

```python
(
    title_rows, cat_rows, cinema_rows, theme_rows, char_rows,
    motiv_rows, atmos_rows, msg_rows, time_rows, place_rows,
    sp_rows, crew_rows, cast_rows, studio_rows, src_rows,
    award_rows, streaming_rows, seq_rows,
) = await asyncio.gather(
    _parallel_query("SELECT l.language_code, ... WHERE fl.film_id = :fid ...", {"fid": film_id}),
    _parallel_query("SELECT DISTINCT c.category_name, ... WHERE fg.film_id = :fid ...", {"fid": film_id}),
    # ... all 17 remaining queries, copy the SQL strings exactly from the current sequential code
    # (the sequel query with UNION is included here too)
)
```

4. After the gather, process rows into response objects exactly as before (the FilmTitle/CrewMember/etc. list comprehensions stay identical, just using the unpacked variables instead of `await db.execute()` results).

5. The `db` session dependency is no longer needed for the parallel queries (they use `engine.connect()` directly), but keep the `db: AsyncSession = Depends(get_db)` parameter signature for the initial film lookup. Alternatively, the initial lookup can also use `engine.connect()` and you can remove the `db` dependency entirely — your choice, but keeping it is simpler.

6. Important: the `load_names()` inner function should be removed — its queries are now part of the gather block.

Do NOT change any of the SQL strings themselves, the response model, or the query logic. The only change is making them run in parallel instead of sequentially.

### Part B — Frontend: React Query caching

1. Install the dependency:
```
npm install @tanstack/react-query
```

2. In `frontend/src/App.tsx`:
- Import `QueryClient` and `QueryClientProvider` from `@tanstack/react-query`
- Create a `queryClient` instance outside the component with:
  ```ts
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000,      // 30s default
        gcTime: 5 * 60 * 1000,     // keep unused cache 5min
        refetchOnWindowFocus: false,
      },
    },
  });
  ```
- Wrap `<BrowserRouter>` children with `<QueryClientProvider client={queryClient}>`

3. Rewrite `frontend/src/hooks/useFilms.ts`:
- Import `useQuery` from `@tanstack/react-query`
- Replace the entire custom hook body with:
  ```ts
  export function useFilms(filters: FilterState) {
    const { data: films = null, isLoading: loading, error } = useQuery({
      queryKey: ["films", filters],
      queryFn: () => fetchFilms(filters),
    });
    return { films, loading, error: error?.message ?? null };
  }
  ```
- Remove the manual state, debounce, and abort logic — React Query handles all of this.
- **Keep the 300ms debounce** for text-based filter changes. To do this, add a `debouncedFilters` state that updates 300ms after `filters` changes (use a `useEffect` with `setTimeout`), and pass `debouncedFilters` to both `queryKey` and `queryFn`. This way React Query only fires a new request after the user stops typing.

4. Rewrite `frontend/src/hooks/useFilmDetail.ts`:
- Replace with:
  ```ts
  export function useFilmDetail(filmId: number) {
    const { data: film = null, isLoading: loading, error, refetch } = useQuery({
      queryKey: ["film", filmId],
      queryFn: () => fetchFilmDetail(filmId),
      staleTime: 60 * 1000,  // 1 minute
    });
    return { film, setFilm: () => {}, loading, error: error?.message ?? null, refetch };
  }
  ```
- Note: `setFilm` is used for optimistic updates (vu toggle). To keep this working, use `queryClient.setQueryData(["film", filmId], updatedFilm)` instead of local state. Import `useQueryClient` and update the optimistic toggle in `FilmDetailPage.tsx` to use `queryClient.setQueryData`. Also invalidate the films list cache after toggling: `queryClient.invalidateQueries({ queryKey: ["films"] })`.

5. Rewrite `frontend/src/hooks/useTaxonomy.ts`:
- Use `useQuery` with `staleTime: Infinity` (taxonomy values essentially never change during a session)
- Keep the same return shape: `{ taxonomies, loading }`

6. After saving a new film via AddFilmPage, invalidate the films cache:
```ts
queryClient.invalidateQueries({ queryKey: ["films"] });
```
Same after deleting a film or updating film tags.

### Verification
- Film detail page loads in < 200ms (check Network tab)
- Navigating browse → detail → browse shows cached data instantly (no spinner on return)
- Taxonomy dropdowns populate instantly after first load
- `vu` toggle still works with optimistic update
- All existing functionality unchanged
