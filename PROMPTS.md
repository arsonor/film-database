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

Read CLAUDE.md, then PLAN.md (Step 15a), then these files:
- `backend/app/auth.py`
- `backend/app/main.py` (focus on auth endpoints)
- `backend/app/routers/films.py` (focus on `get_film()`, `list_films()`, `toggle_vu()`)
- `backend/app/schemas/film.py`
- `backend/app/database.py`
- `backend/requirements.txt`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/types/api.ts`
- `frontend/src/components/films/FilmCard.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/App.tsx`
- `frontend/package.json`
- `database/schema.sql`

### Overview

Replace the current `ADMIN_SECRET_KEY` bearer-token authentication with Supabase Auth (email/password + Google OAuth). Introduce a 3-tier role model (`free`/`pro`/`admin`) and per-user film status tracking. Migrate the global `film.vu` column to a per-user `user_film_status.seen` column. Martin becomes user #1 (admin), and the system is ready for public user registration.

This is a large step. Take care to read all referenced files fully before making any changes. The auth rewrite touches both backend and frontend comprehensively.

### Part 1 — Database: Migration 011

Create `database/migrations/011_user_auth.sql`:

```sql
-- Step 15a: User authentication and per-user film status
-- Adds user_profile and user_film_status tables, migrates film.vu

-- 1. User profile table (id matches Supabase auth.users UUID)
CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    tier TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'pro', 'admin')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profile_email ON user_profile(email);
CREATE INDEX IF NOT EXISTS idx_user_profile_tier ON user_profile(tier);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS user_profile_updated_at_trigger ON user_profile;
CREATE TRIGGER user_profile_updated_at_trigger
    BEFORE UPDATE ON user_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 2. Per-user film status
CREATE TABLE IF NOT EXISTS user_film_status (
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id) ON DELETE CASCADE,
    seen BOOLEAN DEFAULT FALSE,
    favorite BOOLEAN DEFAULT FALSE,
    watchlist BOOLEAN DEFAULT FALSE,
    rating SMALLINT CHECK (rating IS NULL OR (rating >= 1 AND rating <= 10)),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, film_id)
);

CREATE INDEX IF NOT EXISTS idx_user_film_status_user ON user_film_status(user_id);
CREATE INDEX IF NOT EXISTS idx_user_film_status_film ON user_film_status(film_id);
CREATE INDEX IF NOT EXISTS idx_user_film_status_seen ON user_film_status(user_id, seen) WHERE seen = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_film_status_favorite ON user_film_status(user_id, favorite) WHERE favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_film_status_watchlist ON user_film_status(user_id, watchlist) WHERE watchlist = TRUE;

DROP TRIGGER IF EXISTS user_film_status_updated_at_trigger ON user_film_status;
CREATE TRIGGER user_film_status_updated_at_trigger
    BEFORE UPDATE ON user_film_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Important**: Do NOT include the `film.vu` migration (INSERT INTO user_film_status + DROP COLUMN) in this migration file. That will be done via a separate manual script after Martin creates his Supabase Auth account and we know his UUID. Create a script `scripts/migrate_vu_to_user_status.py` instead that:
- Takes `--user-uuid` as an argument
- Connects to the database
- Inserts `user_film_status(user_id, film_id, seen=TRUE)` for all films WHERE vu = TRUE
- Then runs `ALTER TABLE film DROP COLUMN vu`
- Prints a summary (X films migrated)

Also update `database/schema.sql`:
- Remove `vu BOOLEAN DEFAULT FALSE` from the `film` table CREATE statement
- Remove the `COMMENT ON COLUMN film.vu` line
- Add the two new table definitions (user_profile, user_film_status) with their indexes and triggers

### Part 2 — Backend: JWT Auth + New Endpoints

**`backend/requirements.txt`**: Add `python-jose[cryptography]>=3.3.0`

**Rewrite `backend/app/auth.py`** completely:

```python
"""
Supabase JWT authentication for FastAPI.
Verifies tokens issued by Supabase Auth and manages user roles.
"""

import os
import logging
from dataclasses import dataclass
from jose import jwt, JWTError
from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"

@dataclass
class UserInfo:
    id: str          # UUID as string
    email: str
    tier: str        # 'free' | 'pro' | 'admin'

def _decode_token(token: str) -> dict:
    """Decode and verify a Supabase JWT. Returns the payload."""
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(status_code=500, detail="Auth not configured")
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},  # Supabase tokens may not have aud
        )
        return payload
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> UserInfo | None:
    """
    Optional auth dependency. Returns UserInfo if a valid token is present, None otherwise.
    Auto-creates user_profile on first login.
    """
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        return None

    token = parts[1]

    # Dev fallback: if SUPABASE_JWT_SECRET is not set AND the token matches
    # ADMIN_SECRET_KEY, return a synthetic admin user (for local dev without Supabase Auth)
    admin_key = os.getenv("ADMIN_SECRET_KEY")
    if not SUPABASE_JWT_SECRET and admin_key and token == admin_key:
        return UserInfo(id="dev-admin", email="admin@localhost", tier="admin")

    payload = _decode_token(token)
    user_id = payload.get("sub")
    email = payload.get("email", "")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no sub claim")

    # Look up or auto-create user_profile
    result = await db.execute(
        text("SELECT id, email, tier FROM user_profile WHERE id = :uid"),
        {"uid": user_id},
    )
    row = result.fetchone()

    if row:
        # Update email if changed
        if row[1] != email and email:
            await db.execute(
                text("UPDATE user_profile SET email = :email WHERE id = :uid"),
                {"uid": user_id, "email": email},
            )
            await db.commit()
        return UserInfo(id=str(row[0]), email=row[1], tier=row[2])
    else:
        # Auto-create profile on first login (default tier: free)
        await db.execute(
            text("""
                INSERT INTO user_profile (id, email, display_name, tier)
                VALUES (:uid, :email, :display_name, 'free')
            """),
            {"uid": user_id, "email": email, "display_name": email.split("@")[0]},
        )
        await db.commit()
        logger.info("Auto-created user profile for %s (%s)", user_id, email)
        return UserInfo(id=user_id, email=email, tier="free")

async def require_authenticated(
    user: UserInfo | None = Depends(get_current_user),
) -> UserInfo:
    """Dependency: requires a logged-in user, any tier."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(
    user: UserInfo = Depends(require_authenticated),
) -> UserInfo:
    """Dependency: requires an admin user."""
    if user.tier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

Key design points:
- `get_current_user` is an **optional** dependency (returns None for anonymous). Use it in endpoints that work for both anonymous and authenticated users (like list_films, get_film — which return user_status if logged in).
- `require_authenticated` wraps get_current_user and raises 401 if None.
- `require_admin` wraps require_authenticated and checks tier.
- Auto-create on first token verification means we don't need a separate registration endpoint. When a user signs up via Supabase Auth and first hits the API, their profile gets created automatically with tier='free'.
- Dev fallback: keep ADMIN_SECRET_KEY working locally so local dev without Supabase Auth still works.
- **IMPORTANT**: `get_current_user` takes `db: AsyncSession = Depends(get_db)` — this means every endpoint that uses `get_current_user` also gets a DB session through the dependency chain. Endpoints that previously took `db` directly may need adjustment if they now receive it through the auth dependency. The cleanest approach: keep `db` as a separate explicit `Depends(get_db)` on each endpoint, and also pass `db` to `get_current_user` via the dependency injection — FastAPI handles this correctly with shared dependencies.

**Create `backend/app/routers/users.py`** — new router for user film status:

```python
"""
User film status endpoints — seen, favorite, watchlist per user per film.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.auth import UserInfo, require_authenticated
from backend.app.database import get_db

router = APIRouter(tags=["users"])

@router.get("/users/me/films/{film_id}/status")
async def get_film_status(
    film_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT seen, favorite, watchlist, rating, notes
            FROM user_film_status
            WHERE user_id = :uid AND film_id = :fid
        """),
        {"uid": user.id, "fid": film_id},
    )
    row = result.fetchone()
    if not row:
        return {"seen": False, "favorite": False, "watchlist": False, "rating": None, "notes": None}
    return {"seen": row[0], "favorite": row[1], "watchlist": row[2], "rating": row[3], "notes": row[4]}

@router.put("/users/me/films/{film_id}/status")
async def update_film_status(
    film_id: int,
    body: dict,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    # Validate film exists
    r = await db.execute(text("SELECT film_id FROM film WHERE film_id = :fid"), {"fid": film_id})
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")

    # Upsert user_film_status
    await db.execute(
        text("""
            INSERT INTO user_film_status (user_id, film_id, seen, favorite, watchlist, rating, notes)
            VALUES (:uid, :fid, :seen, :fav, :wl, :rating, :notes)
            ON CONFLICT (user_id, film_id) DO UPDATE SET
                seen = COALESCE(:seen, user_film_status.seen),
                favorite = COALESCE(:fav, user_film_status.favorite),
                watchlist = COALESCE(:wl, user_film_status.watchlist),
                rating = COALESCE(:rating, user_film_status.rating),
                notes = COALESCE(:notes, user_film_status.notes)
        """),
        {
            "uid": user.id, "fid": film_id,
            "seen": body.get("seen"),
            "fav": body.get("favorite"),
            "wl": body.get("watchlist"),
            "rating": body.get("rating"),
            "notes": body.get("notes"),
        },
    )
    await db.commit()
    return {"film_id": film_id, "updated": True}
```

Register this router in `main.py`: `app.include_router(users.router, prefix="/api")`

**Update `main.py`**:
- Remove the `LoginRequest` model, the `POST /api/auth/login` endpoint, and the `GET /api/auth/check` endpoint
- Add a new `GET /api/auth/me` endpoint:
  ```python
  @app.get("/api/auth/me")
  async def auth_me(user: UserInfo = Depends(require_authenticated)):
      return {"id": user.id, "email": user.email, "tier": user.tier}
  ```
- Import and register the `users` router

**Update `routers/films.py`**:

1. **`list_films()`**: Add an optional `user` parameter via `user: UserInfo | None = Depends(get_current_user)`. If a user is logged in, LEFT JOIN `user_film_status` to include their `seen` status on each film. Change `FilmListItem` to include `user_status` instead of `vu`. In the main query:
   ```sql
   SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
          f.poster_url,
          ufs.seen AS user_seen, ufs.favorite AS user_fav, ufs.watchlist AS user_wl
   FROM film f
   LEFT JOIN user_film_status ufs ON f.film_id = ufs.film_id AND ufs.user_id = :current_user_id
   WHERE {where_sql}
   ```
   If user is None, skip the JOIN and return `user_status: null` for all items.
   
   For the `vu` filter parameter: if `vu` is set and user is logged in, filter by `ufs.seen = :vu` (or NOT EXISTS for unseen). If user is anonymous and vu is set, return empty results (can't filter personal status without being logged in).

2. **`get_film()`**: Add optional `user` parameter. After fetching all film data, if user is logged in, also fetch their status for this film from `user_film_status` and include it as `user_status` in the response.

3. **Remove `toggle_vu()`** — the `PATCH /films/{id}/vu` endpoint is fully replaced by `PUT /users/me/films/{id}/status`.

**Update `schemas/film.py`**:
- Add `UserFilmStatus` schema:
  ```python
  class UserFilmStatus(BaseModel):
      seen: bool = False
      favorite: bool = False
      watchlist: bool = False
      rating: int | None = None
  ```
- `FilmListItem`: replace `vu: bool` with `user_status: UserFilmStatus | None = None`
- `FilmDetail`: replace `vu: bool` with `user_status: UserFilmStatus | None = None`
- `FilmUpdate`: remove `vu: bool | None = None` if present

### Part 3 — Frontend: Supabase Auth Client

**Install**: `npm install @supabase/supabase-js`

**Create `frontend/src/lib/supabase.ts`**:
```ts
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn("Supabase env vars not set — auth will not work");
}

export const supabase = createClient(supabaseUrl || "", supabaseAnonKey || "");
```

**Rewrite `frontend/src/context/AuthContext.tsx`**:
- Use `supabase.auth.onAuthStateChange()` to listen for auth events
- On session change: call `GET /api/auth/me` with the Supabase access token to get user profile (id, email, tier)
- Expose: `user: { id, email, tier, displayName } | null`, `isAdmin`, `isAuthenticated`, `loading`, `signIn(email, password)`, `signUp(email, password)`, `signInWithGoogle()`, `signOut()`
- `signInWithGoogle()` calls `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin + '/browse' } })`

**Rewrite `frontend/src/api/client.ts`** — `getAuthHeaders()`:
```ts
async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}
```
This is now `async`. Every function that uses `getAuthHeaders()` must now `await` it. Go through all functions in `client.ts` that call `getAuthHeaders()` and add `await`. Since these functions already return Promises (they use `fetch`), this is a minor change — just add `await` before `getAuthHeaders()` in each one.

**Add new API functions in `client.ts`**:
```ts
export async function fetchUserFilmStatus(filmId: number): Promise<UserFilmStatus> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/films/${filmId}/status`, { headers });
  if (!res.ok) return { seen: false, favorite: false, watchlist: false, rating: null };
  return res.json();
}

export async function updateUserFilmStatus(
  filmId: number,
  status: Partial<UserFilmStatus>,
): Promise<void> {
  const headers = await getAuthHeaders();
  await fetch(`${BASE}/users/me/films/${filmId}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(status),
  });
}
```

Remove `toggleVu()` function.

**Replace `LoginPage.tsx`** with `AuthPage.tsx`**:
- Combined login/register page with a toggle ("Already have an account?" / "Need an account?")
- Email + password form fields
- "Sign in with Google" button (styled with Google icon or text)
- Error handling for invalid credentials, email already taken, etc.
- Redirect to `/browse` after successful auth
- Dark theme consistent with the existing charcoal/amber aesthetic
- If the user navigates to `/auth` while already logged in, redirect to `/browse`

**Update `App.tsx`**:
- Replace `<Route path="/login" element={<LoginPage />} />` with `<Route path="/auth" element={<AuthPage />} />`
- Remove import of `LoginPage`, add import of `AuthPage`

**Update `types/api.ts`**:
- Add:
  ```ts
  export interface UserFilmStatus {
    seen: boolean;
    favorite: boolean;
    watchlist: boolean;
    rating: number | null;
  }
  ```
- In `FilmListItem`: replace `vu: boolean` with `user_status: UserFilmStatus | null`
- In `FilmDetail`: replace `vu: boolean` with `user_status: UserFilmStatus | null`
- In `StatsResponse`: replace `seen` and `unseen` with optional fields (these become per-user later)

**Update `FilmCard.tsx`**:
- The seen toggle now reads from `item.user_status?.seen` instead of `item.vu`
- On click, call `updateUserFilmStatus(filmId, { seen: !currentSeen })` instead of `toggleVu()`
- Only show the toggle button if the user is authenticated (use `useAuth()` hook)
- Keep optimistic update pattern: `queryClient.setQueryData` to flip the status immediately

**Update `FilmDetailPage.tsx`**:
- Replace `handleToggleVu` with a call to `updateUserFilmStatus(film.film_id, { seen: !film.user_status?.seen })`
- Optimistic update: `queryClient.setQueryData(["film", filmId], ...)` updating the `user_status.seen` field
- Invalidate films list: `queryClient.invalidateQueries({ queryKey: ["films"] })`
- Only show the seen toggle if the user is authenticated

**Update `Header.tsx`**:
- When `isAuthenticated`: show user avatar/email dropdown with "Sign out" option
- When anonymous: show "Sign in" button linking to `/auth`
- The admin-only buttons (Add Film, Tags) remain gated by `isAdmin`
- The "Sign in" button replaces the old "Login" button

### Part 4 — Manual Steps (not in Claude Code prompt)

These steps require manual action by Martin:

1. **Supabase dashboard**: Enable Email provider + Google OAuth provider under Authentication > Providers
2. **Google Cloud Console**: Create OAuth 2.0 credentials, set authorized redirect URI to `https://<supabase-project-ref>.supabase.co/auth/v1/callback`
3. **Supabase dashboard**: Set Site URL to the Vercel frontend URL, add localhost:3000 as additional redirect URL
4. **Render env vars**: Add `SUPABASE_JWT_SECRET` (from Supabase > Settings > API > JWT Secret)
5. **Vercel env vars**: Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (from Supabase > Settings > API)
6. **Run migration**: Execute `011_user_auth.sql` against Supabase
7. **First login**: Log in via the new auth page to create the Supabase Auth account
8. **Get UUID**: Copy the user UUID from Supabase dashboard > Authentication > Users
9. **Set admin tier**: `UPDATE user_profile SET tier = 'admin' WHERE id = '<uuid>'`
10. **Run vu migration script**: `python scripts/migrate_vu_to_user_status.py --user-uuid <uuid>`

### Verification
- Anonymous users can browse, view film details, and see all taxonomy filters (no seen/favorite/watchlist status shown)
- Clicking "Sign in" goes to `/auth` page with email+password form and Google OAuth button
- Email/password registration creates account, redirects to `/browse`, shows user menu in header
- Google OAuth sign-in works end-to-end (redirects to Google, comes back, user is logged in)
- `GET /api/auth/me` returns the correct user profile with tier
- Admin can still access Add Film, Tags admin, edit tags, delete films
- Registered user can toggle seen status on films (both grid and detail page)
- Film list and detail responses include `user_status` when logged in, `null` when anonymous
- `vu` filter still works for logged-in users (filters by their personal seen status)
- Dev environment still works with `ADMIN_SECRET_KEY` fallback when `SUPABASE_JWT_SECRET` is not set
- All existing functionality (browse, search, filter, film detail, taxonomy) is unchanged
