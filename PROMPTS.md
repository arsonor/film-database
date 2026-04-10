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

Read PLAN.md (Step 15b), then these files:
- `backend/app/routers/users.py`
- `backend/app/routers/films.py` (for reference: how list_films builds queries + response)
- `backend/app/schemas/film.py`
- `frontend/src/components/films/FilmCard.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/types/api.ts`
- `frontend/src/App.tsx`

### Part 1 — Backend: User Films List Endpoint

In `backend/app/routers/users.py`, add a new endpoint:

```python
@router.get("/users/me/films")
async def list_user_films(
    filter: str = Query(..., pattern="^(seen|favorite|watchlist)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
```

This endpoint should:
- Query `user_film_status ufs JOIN film f ON ufs.film_id = f.film_id` filtered by `ufs.{filter} = TRUE`
- Return the same shape as the browse endpoint: paginated with `total`, `page`, `per_page`, `total_pages`, `items`
- Each item has: `film_id`, `original_title`, `first_release_date`, `duration`, `poster_url`, `categories` (batch loaded like in list_films), `director` (batch loaded), `user_status` (seen, favorite, watchlist, rating)
- Sort by `ufs.updated_at DESC` (most recently updated first)
- Import `Query` from fastapi if not already imported

### Part 2 — Frontend: FilmCard — Favorite + Watchlist Icons

Update `frontend/src/components/films/FilmCard.tsx`:

Add two new icon buttons alongside the existing seen (eye) toggle in the poster overlay area:
- **Heart** (favorite): `Heart` from lucide-react. When active: filled red (`bg-rose-500/90 text-white`). When inactive: same hover-reveal style as the eye icon.
- **Bookmark** (watchlist): `Bookmark` from lucide-react. When active: filled amber (`bg-amber-500/90 text-white`). When inactive: same hover-reveal style.

Layout: stack the 3 icons vertically in the top-right corner of the poster:
```
[eye]       ← top (existing, keep current position)
[heart]     ← middle (new)
[bookmark]  ← bottom (new)
```

Each icon needs its own local state + optimistic toggle, same pattern as the existing `seen` toggle:
```ts
const [favorite, setFavorite] = useState(film.user_status?.favorite ?? false);
const [watchlist, setWatchlist] = useState(film.user_status?.watchlist ?? false);
```

Each calls `updateUserFilmStatus(film.film_id, { favorite: !favorite })` etc. on click.

Only show all 3 icons when `canToggleSeen` is true (i.e., user is authenticated). Rename the prop to `canToggleStatus` for clarity.

Update `FilmGrid.tsx` and `BrowsePage.tsx` to pass `canToggleStatus` instead of `canToggleSeen`.

### Part 3 — Frontend: FilmDetailPage — Status Section

Create a new component `frontend/src/components/films/FilmStatusBar.tsx`:

This component displays the full user status controls for a film. It receives:
```ts
interface FilmStatusBarProps {
  filmId: number;
  status: UserFilmStatus | null;  // null if not authenticated
  onStatusChange: (updated: Partial<UserFilmStatus>) => void;
}
```

Layout (horizontal bar, consistent with the dark aesthetic):
- **Seen** toggle: Eye icon + "Seen" text, green when active
- **Favorite** toggle: Heart icon + "Favorite" text, red when active
- **Watchlist** toggle: Bookmark icon + "Watchlist" text, amber when active
- **Star Rating**: 5 stars, clickable. Display as 5 star icons. Each star represents 2 points (star 1 = 2, star 2 = 4, ... star 5 = 10). Clicking a star sets the rating. Clicking the same star again clears the rating. Half-star support is optional — if too complex, just do whole stars (2/4/6/8/10). Show the numeric value next to the stars (e.g. "8/10"). Stars use amber/gold color when filled, muted when empty.
- **Notes**: A small "Add note..." button that expands into a textarea on click. Auto-saves on blur with a 500ms debounce. Show a subtle "Saved" indicator briefly after save.

All toggles call `onStatusChange` which triggers `updateUserFilmStatus()` in the parent.

Create a separate `frontend/src/components/films/StarRating.tsx` component:
```ts
interface StarRatingProps {
  value: number | null;   // 1-10 or null
  onChange: (value: number | null) => void;
  readonly?: boolean;
}
```
- Renders 5 star icons (`Star` from lucide-react)
- Maps value 1-10 to stars: value/2 stars filled (round up for half). For simplicity: value 1-2 → 1 star, 3-4 → 2 stars, etc. Or more precisely: fill star N if value >= N*2.
- On click star N: if current value was N*2, set to null (clear). Otherwise set to N*2.
- Hover effect: highlight stars up to the hovered position

In `FilmDetailPage.tsx`:
- Import and place `FilmStatusBar` in the hero area, below the film title/meta section, above the synopsis
- Only render if `isAuthenticated`
- Wire up `onStatusChange` to call `updateUserFilmStatus()` with optimistic query cache updates
- After any status change, invalidate `["films"]` and `["collection"]` queries

### Part 4 — Frontend: Collection Page

Create `frontend/src/pages/CollectionPage.tsx`:

- Top section: title "My Collection" + 3 tab buttons: "Seen (N)", "Favorites (N)", "Watchlist (N)"
- The active tab filters the displayed films
- Uses `useQuery` with key `["collection", activeFilter, page]` calling a new `fetchUserFilms(filter, page, perPage)` function in `client.ts`
- Displays films in the same poster grid as BrowsePage (reuse `FilmGrid` component)
- Pagination at the bottom (reuse `Pagination` component)
- If not authenticated, redirect to `/auth`
- Dark theme consistent with existing pages
- Use the same `Layout` wrapper if appropriate, or a simpler layout without the sidebar (collection doesn't need taxonomy filters)

Add `fetchUserFilms` to `frontend/src/api/client.ts`:
```ts
export async function fetchUserFilms(
  filter: "seen" | "favorite" | "watchlist",
  page = 1,
  perPage = 24,
): Promise<PaginatedFilms> {
  const headers = await getAuthHeaders();
  return fetchJsonWithHeaders<PaginatedFilms>(
    `${BASE}/users/me/films?filter=${filter}&page=${page}&per_page=${perPage}`,
    headers,
  );
}
```

You'll need a `fetchJsonWithHeaders` helper (or modify the existing pattern) since this endpoint requires auth headers on a GET request. Alternatively, just inline the fetch:
```ts
const res = await fetch(url, { headers });
if (!res.ok) throw new ApiError(res.status, ...);
return res.json();
```

Add route in `App.tsx`: `<Route path="/collection" element={<CollectionPage />} />`

### Part 5 — Frontend: Header Nav Menu Dropdown

Rewrite the right section of `frontend/src/components/layout/Header.tsx`:

For **authenticated users**, replace the current flat buttons with a dropdown menu:
- Trigger: a button with the user's email initial (first letter, uppercase) in a circle, or a `User` icon from lucide-react
- Use a shadcn/ui `DropdownMenu` component (may need to install `@radix-ui/react-dropdown-menu` if not already available)

Dropdown content:
```
My Collection          → navigate("/collection")
Dashboard              → disabled, shows "Coming soon" or a lock icon
──────────────────
Add Film               → navigate("/add")        [admin only]
Manage Tags            → navigate("/admin/taxonomy") [admin only]
──────────────────
Sign out               → signOut()
```

Non-admin users don't see the admin section at all (not even disabled — just hidden).

For **anonymous users**: keep the simple "Sign in" button (LogIn icon), unchanged.

The sort controls (Select + arrow button) stay **outside** the dropdown, in the main header bar. The dropdown only contains navigation + auth actions.

If `@radix-ui/react-dropdown-menu` is not in `package.json`, install it and create the shadcn/ui `DropdownMenu` component files. Check existing shadcn components in `frontend/src/components/ui/` for the pattern. Alternatively, you can use a simpler approach with a custom popover using existing components.

### Verification
- Authenticated user sees 3 icons (eye, heart, bookmark) on film cards on hover
- Clicking each icon toggles the respective status with optimistic update
- Film detail page shows FilmStatusBar with all controls for authenticated users
- Star rating works: click to set, click same to clear, visual feedback on hover
- Notes expand, auto-save on blur, show brief "Saved" confirmation
- `/collection` page shows 3 tabs with correct film counts
- Switching tabs loads the correct filtered films
- Nav dropdown shows correct items based on role (admin sees add/tags, others don't)
- Anonymous users see no status icons, no collection link, just "Sign in"
- All existing functionality unchanged
