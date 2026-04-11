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

Read PLAN.md (Step 15c), then these files:
- `frontend/src/context/AuthContext.tsx` (for tier info)
- `frontend/src/components/filters/FilterChip.tsx`
- `frontend/src/components/filters/FilterSection.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/filters/ActiveFilters.tsx`
- `frontend/src/components/films/SimilarFilmsCarousel.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/hooks/useFilterState.ts`
- `backend/app/routers/films.py` (focus on list_films)
- `backend/app/auth.py` (for UserInfo/tier)
- `database/seed_taxonomy.sql` (for theme sort_order values)

### Overview

Restrict taxonomy filter access by user tier. All dimensions remain visible in the sidebar but locked dimensions/tags show greyed-out chips with a lock icon. Clicking a locked chip shows an upgrade prompt. Filter count is limited per tier. OR/NOT logic is pro-only. The backend silently ignores filter params the user's tier doesn't allow.

### Part 1 — Frontend: Tier Access Configuration

Create `frontend/src/lib/tierAccess.ts`:

```ts
import { useAuth } from "@/context/AuthContext";
import type { FilterState, ArrayFilterKey } from "@/types/api";

type TierName = "anonymous" | "free" | "pro" | "admin";

interface TierConfig {
  allowedDimensions: Set<ArrayFilterKey>;
  allowedDropdowns: Set<string>;           // "source", "studios", "language", "location"
  allowedThemeSortOrderMax: number | null; // themes with sort_order <= this value are allowed; null = all or N/A
  maxFilters: number | null;               // null = unlimited
  canUseOrNot: boolean;
}

const TIER_CONFIGS: Record<TierName, TierConfig> = {
  anonymous: {
    allowedDimensions: new Set(["categories", "time_periods", "place_contexts"]),
    allowedDropdowns: new Set(["language", "location"]),
    allowedThemeSortOrderMax: null, // themes dimension not allowed at all for anonymous
    maxFilters: 2,
    canUseOrNot: false,
  },
  free: {
    allowedDimensions: new Set([
      "categories", "time_periods", "place_contexts",
      "studios", "themes",
    ]),
    allowedDropdowns: new Set(["language", "location", "source", "studios"]),
    allowedThemeSortOrderMax: 299, // G1 (100-113) + G2 (200-209) allowed; G3+ (300+) locked
    maxFilters: 5,
    canUseOrNot: false,
  },
  pro: {
    allowedDimensions: new Set([
      "categories", "themes", "atmospheres", "characters",
      "motivations", "messages", "cinema_types",
      "time_periods", "place_contexts", "studios",
    ]),
    allowedDropdowns: new Set(["language", "location", "source", "studios"]),
    allowedThemeSortOrderMax: null, // all themes allowed
    maxFilters: null,
    canUseOrNot: true,
  },
  admin: {
    allowedDimensions: new Set([
      "categories", "themes", "atmospheres", "characters",
      "motivations", "messages", "cinema_types",
      "time_periods", "place_contexts", "studios",
    ]),
    allowedDropdowns: new Set(["language", "location", "source", "studios"]),
    allowedThemeSortOrderMax: null,
    maxFilters: null,
    canUseOrNot: true,
  },
};
```

Export a `useTierAccess(filters: FilterState)` hook that:
1. Gets `tier` and `isAuthenticated` from `useAuth()`
2. Resolves effective tier: not authenticated → `"anonymous"`, else `tier ?? "free"`
3. Returns an object with:
   - `isDimensionAllowed(dim: ArrayFilterKey): boolean` — checks `allowedDimensions`
   - `isTagAllowed(dim: ArrayFilterKey, sortOrder: number | null): boolean` — for dims other than themes: returns `isDimensionAllowed(dim)`. For themes: also checks `sortOrder !== null && (allowedThemeSortOrderMax === null || sortOrder <= allowedThemeSortOrderMax)`
   - `isDropdownAllowed(name: string): boolean` — checks `allowedDropdowns`
   - `maxFilters: number | null`
   - `currentFilterCount: number` — sum of all `filters[dim].include.length + filters[dim].exclude.length` across all `ARRAY_FILTER_KEYS`, plus 1 for each non-empty string filter (location, language, source)
   - `canAddFilter: boolean` — `maxFilters === null || currentFilterCount < maxFilters`
   - `canUseOrNot: boolean`
   - `tierName: TierName`

### Part 2 — Frontend: FilterChip Locked State

Update `frontend/src/components/filters/FilterChip.tsx`:

Add `"locked"` to ChipState:
```ts
export type ChipState = "off" | "include" | "exclude" | "locked";
```

Add optional props:
```ts
onLockedClick?: () => void;
```

When state is `"locked"`:
- Style: `opacity-40 cursor-not-allowed border-border/40 bg-transparent text-muted-foreground/50`
- Add a small lock icon (`Lock` from lucide-react, `h-2.5 w-2.5`) before the name text
- On click: call `onLockedClick?.()` instead of `onInclude()`. Do NOT call `onExclude` on right-click/long-press either.
- Disable the context menu handler and long-press handler when locked.

### Part 3 — Frontend: FilterSection Gating

Update `frontend/src/components/filters/FilterSection.tsx`:

Add new optional props:
```ts
locked?: boolean;              // entire dimension locked
lockedTagNames?: Set<string>;  // specific tags locked (for themes G3-G6)
canAddFilter?: boolean;        // false = filter limit reached
canUseOrNot?: boolean;         // false = hide OR/AND toggle
onLockedClick?: () => void;    // called when locked chip clicked
onLimitReached?: () => void;   // called when user hits filter limit
```

Behavior:
- If `locked` is true: add a small Lock icon + amber "Pro" badge text next to the section title. All chips render with state `"locked"` regardless of tagFilter. Section can still expand/collapse.
- If `lockedTagNames` is set: chips whose `item.name` is in the set render as `"locked"`. Others render normally.
- If `canAddFilter` is false: chips in state `"off"` should behave as locked (clicking calls `onLimitReached` instead of `onToggle`). Chips already in `"include"` or `"exclude"` state can still be toggled off (removing a filter should always work).
- If `canUseOrNot` is false: never render the AND/OR toggle pill. The condition `tagFilter.include.length >= 2` should be combined with `canUseOrNot !== false`.

### Part 4 — Frontend: Sidebar Integration

Update `frontend/src/components/layout/Sidebar.tsx`:

- Add `filters` to the `SidebarProps` interface if not already there (it's needed for `useTierAccess`)
- Import and call `useTierAccess(filters)` at the top of `SidebarContent`
- Add a `tierMessage` local state (`useState<string | null>(null)`) with a 3-second auto-clear timeout for showing upgrade/limit messages

For each `TAXONOMY_DIMENSIONS` entry:
```ts
const locked = !tierAccess.isDimensionAllowed(dim);
const lockedTagNames = dim === "themes" && !locked
  ? new Set(
      (taxonomies["themes"] || [])
        .filter((item) => !tierAccess.isTagAllowed("themes", item.sort_order))
        .map((item) => item.name)
    )
  : undefined;
```

Pass to FilterSection:
```ts
<FilterSection
  key={dim}
  // ... existing props ...
  locked={locked}
  lockedTagNames={lockedTagNames}
  canAddFilter={tierAccess.canAddFilter}
  canUseOrNot={tierAccess.canUseOrNot}
  onLockedClick={() => setTierMessage(
    tierAccess.tierName === "anonymous"
      ? "Create an account to unlock more filters"
      : "Upgrade to Pro to unlock all filters"
  )}
  onLimitReached={() => setTierMessage(
    `Filter limit reached (${tierAccess.currentFilterCount}/${tierAccess.maxFilters}) — ${
      tierAccess.tierName === "anonymous" ? "sign in for more" : "upgrade to Pro"
    }`
  )}
/>
```

For the Source dropdown: if `!tierAccess.isDropdownAllowed("source")`, wrap it in a div with `opacity-40 pointer-events-none` and show a small lock icon next to the label.

For the Studio search: same pattern — if `!tierAccess.isDropdownAllowed("studios")`, disable it.

Display `tierMessage` at the top of the sidebar as a small amber-tinted banner that auto-dismisses:
```tsx
{tierMessage && (
  <div className="mx-4 mb-2 rounded-md bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-400">
    {tierMessage}
  </div>
)}
```

### Part 5 — Frontend: SimilarFilmsCarousel Teaser

Update `frontend/src/components/films/SimilarFilmsCarousel.tsx`:

Add a `locked?: boolean` prop.

When `locked` is true, replace the entire content with a styled teaser:
```tsx
<div>
  <SectionHeading title="Similar Films" />
  <div className="flex items-center gap-3 rounded-lg border border-dashed border-amber-500/30 bg-amber-500/5 p-6">
    <Lock className="h-5 w-5 text-amber-500/60" />
    <div>
      <p className="text-sm font-medium text-foreground">Discover similar films</p>
      <p className="text-xs text-muted-foreground">Upgrade to Pro to unlock personalized recommendations</p>
    </div>
  </div>
</div>
```

When `locked` is false: keep the current "Recommendations coming soon" placeholder with skeletons.

In `FilmDetailPage.tsx`: import `useAuth`, compute:
```ts
const { tier } = useAuth();
const similarLocked = tier !== "pro" && tier !== "admin";
```
Pass `locked={similarLocked}` to `<SimilarFilmsCarousel>`.

### Part 6 — Backend: Tier Validation

Create `backend/app/tier_config.py`:

```python
"""
Tier-based access configuration.
Mirrors the frontend tier config for server-side validation.
"""

TIER_ALLOWED_DIMENSIONS: dict[str, set[str]] = {
    "anonymous": {"categories", "time_periods", "place_contexts"},
    "free": {"categories", "time_periods", "place_contexts", "studios", "themes"},
    "pro": {"categories", "themes", "atmospheres", "characters", "motivations",
            "messages", "cinema_types", "time_periods", "place_contexts", "studios"},
    "admin": {"categories", "themes", "atmospheres", "characters", "motivations",
              "messages", "cinema_types", "time_periods", "place_contexts", "studios"},
}

# For themes: max sort_order allowed (None = all allowed)
TIER_THEME_MAX_SORT_ORDER: dict[str, int | None] = {
    "anonymous": None,   # themes not in allowed dims
    "free": 299,         # G1 + G2 only
    "pro": None,
    "admin": None,
}

TIER_MAX_FILTERS: dict[str, int | None] = {
    "anonymous": 2,
    "free": 5,
    "pro": None,
    "admin": None,
}

TIER_CAN_USE_OR_NOT: dict[str, bool] = {
    "anonymous": False,
    "free": False,
    "pro": True,
    "admin": True,
}
```

Update `backend/app/routers/films.py` — in `list_films()`, after collecting all filter params and before building WHERE clauses:

1. Determine tier: `tier = user.tier if user else "anonymous"`

2. Import `TIER_ALLOWED_DIMENSIONS, TIER_MAX_FILTERS, TIER_CAN_USE_OR_NOT, TIER_THEME_MAX_SORT_ORDER` from `backend.app.tier_config`

3. **Silently clear disallowed dimensions**: For each taxonomy filter variable (themes, atmospheres, etc.), if the dimension name is not in `TIER_ALLOWED_DIMENSIONS[tier]`, set its values to `None` (clearing the filter). Use a mapping from variable name to dimension name.

4. **Filter count enforcement**: Count total active filter values across all dimensions (sum of len(values) for each non-None taxonomy filter + 1 for each non-empty string filter like location, language). If `TIER_MAX_FILTERS[tier]` is not None and count exceeds it, return HTTP 400: `"Filter limit exceeded (max {limit} for your tier)"`

5. **Force AND mode**: If `not TIER_CAN_USE_OR_NOT[tier]`: for all `_mode` params, force them to `"and"`. For all `_not` params, set them to `None` (clear excludes).

6. **Theme sort_order filtering**: If `tier` has a `TIER_THEME_MAX_SORT_ORDER` value and themes are allowed but limited: after the themes values are collected but before building the WHERE clause, query the `theme_context` table to get sort_orders for the requested theme names. Remove any theme values whose sort_order exceeds the limit. This prevents users from bypassing the frontend's per-tag locking by calling the API directly with locked theme names.

This validation block should go BEFORE the existing WHERE clause construction loop, so that by the time the query is built, all disallowed filters have already been cleared.

### Verification
- Anonymous user: can use categories, time_periods, place_contexts filters (max 2). Other dimensions show greyed/locked chips with lock icon. Clicking locked chip shows upgrade banner. OR/AND toggle hidden. Source/Studio dropdowns locked.
- Anonymous user: adding a 3rd filter shows "Filter limit reached (2/2)" banner. Removing one allows adding another.
- Free registered user: can use categories, time_periods, place_contexts, studios, source, + themes G1 & G2 (max 5). Themes G3–G6 show locked chips within an otherwise usable themes section. Atmospheres, characters, motivations, messages, cinema_types show fully locked. OR/AND toggle hidden.
- Pro user: full access to all dimensions, unlimited filters, OR/NOT enabled.
- Admin: same as pro.
- Similar Films section: shows locked teaser for anonymous/free, "coming soon" for pro/admin.
- Backend: API call with filters for a locked dimension → silently ignored, results returned without that filter.
- Backend: API call exceeding filter limit → 400 error with clear message.
- Backend: API call with OR/NOT mode from anonymous/free → silently forced to AND, excludes ignored.
- All existing functionality unchanged for pro/admin users.
