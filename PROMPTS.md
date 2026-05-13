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

*(see git history for original prompts)*

---

## Step 16a Prompt — Recommender: "Refine in Browse" Button

Step 16a Summary
Backend: GET /api/taxonomy/tag-frequencies (24h cache, mutation-invalidated) — kept for use by future 16b/16c logic.
Frontend: "Refine in Browse →" button in Similar Films section header. Pro/Admin only. Click loads all tags from the current film into /browse in OR mode (per-dimension), letting the user manually deselect/AND-toggle from a complete starting state. Smart-selection approach (selectDistinctiveTags) was prototyped and discarded — applying all tags in OR mode tested better in practice because the user is already the best judge of which tags matter for that specific film.

---

## Step 16b Prompt — Recommender: Similar Films Algorithm (In-DB)

**Goal:** New endpoint `GET /api/films/{id}/similar?limit=N` returning the top-N most similar films using IDF-weighted Jaccard across 9 taxonomy dimensions plus structural bonuses.

### Algorithm

**IDF-weighted Jaccard per dimension, summed across 9 dimensions, plus structural bonuses.**

For source film S and candidate C, per-dimension d:
- per_dim_score(d) = Σ_{t ∈ T_S^d ∩ T_C^d} idf(t) / Σ_{t ∈ T_S^d ∪ T_C^d} idf(t)
- total = Σ_d W_d × per_dim_score(d) + bonuses

**Initial dimension weights** (tunable):
atmospheres 1.4 · themes 1.3 · motivations 1.1 · messages 1.0 · cinema_types 1.0 · characters 0.9 · categories 0.7 · place_contexts 0.6 · time_periods 0.5

**Bonuses**:
- Same director (any overlap): +0.10
- Same studio + same release decade: +0.03
- Quality nudge: +0.05 × normalized weighted_score

---

## Step 16c Prompt — Recommender: SimilarFilmsCarousel UI

**Goal:** Replace the placeholder `SimilarFilmsCarousel` with the real recommendation UI driven by the 16b endpoint, with the "Refine in Browse →" button (16a) integrated into the section header.

---

## Step 17a-Stats Dashboard API & UI

*(see git history for original prompts)*
---

## Step 17c-Taxonomy stats enhancements

*(see git history for original prompts)*
---

## Step 17d-Geography stats data & tab UI

*(see git history for original prompts)*

---

## Step 18 Prompt — Game Mode "Tag It"

Read CLAUDE.md, then PLAN.md (Step 18), then these files:
- `backend/app/routers/films.py` (for reference: how list_films builds filter queries + count)
- `backend/app/routers/users.py` (for reference: endpoint patterns)
- `backend/app/schemas/film.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/tier_config.py`
- `frontend/src/components/filters/FilterSection.tsx`
- `frontend/src/components/filters/FilterChip.tsx`
- `frontend/src/hooks/useTaxonomy.ts`
- `frontend/src/api/client.ts`
- `frontend/src/types/api.ts`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/App.tsx`
- `database/schema.sql`

### Overview

Build a game mode called "Tag It" where the player picks a film from 3 random options, then selects taxonomy tags one by one to narrow the matching film count from the full database down to 1. The goal is to isolate the target film using as few tags as possible. The player has 3 lives — selecting a tag that eliminates the target film costs a life. At 0 lives = game over. Two modes: daily challenge (same film for everyone, shareable results) and free play (unlimited, with optional decade/language filters).

This is a large step with backend + frontend. The backend is mostly new endpoints (no changes to existing ones). The frontend is an entirely new page with several new components. Existing components (FilterSection, FilterChip) can be referenced for styling but the game has its own interaction model — do NOT reuse them directly since game clicks have different behavior (check against target, life system) than browse filter clicks.

### Part 1 — Database: Migration 022

Create `database/migrations/022_game_mode.sql`:

```sql
-- Step 18: Game mode tables

CREATE TABLE IF NOT EXISTS daily_challenge (
    challenge_date DATE PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_result (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    mode TEXT NOT NULL CHECK (mode IN ('daily', 'free')),
    challenge_date DATE,
    tags_used INTEGER NOT NULL,
    lives_remaining INTEGER NOT NULL CHECK (lives_remaining >= 0 AND lives_remaining <= 3),
    jokers_used INTEGER DEFAULT 0,
    stars INTEGER NOT NULL CHECK (stars >= 0 AND stars <= 5),
    tag_sequence JSONB,
    completed BOOLEAN DEFAULT TRUE,
    played_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_result_user ON game_result(user_id);
CREATE INDEX IF NOT EXISTS idx_game_result_daily ON game_result(challenge_date);
CREATE INDEX IF NOT EXISTS idx_game_result_user_mode ON game_result(user_id, mode);
```

Update `database/schema.sql` with the same tables for fresh installs.

### Part 2 — Backend: Game Router

Create `backend/app/routers/game.py`:

All endpoints are under the `/game` prefix. Import `Query` from fastapi, `text` from sqlalchemy, `UserInfo`/`get_current_user`/`require_authenticated` from auth, `get_db` from database.

**`GET /game/daily`** — Get today's daily challenge:
```python
@router.get("/game/daily")
async def get_daily_challenge(db: AsyncSession = Depends(get_db)):
```
- Check if a `daily_challenge` row exists for today's date
- If not, create one: pick a random film that has tags in at least 5 different dimensions. Query:
  ```sql
  SELECT f.film_id FROM film f
  WHERE f.poster_url IS NOT NULL
  AND f.summary IS NOT NULL
  AND (
    (SELECT COUNT(*) FROM (
      SELECT 1 FROM film_theme WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_atmosphere WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_character WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_motivation WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_message WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_time_period WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_place_context WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_genre WHERE film_id = f.film_id LIMIT 1
      UNION ALL SELECT 1 FROM film_cinema_type WHERE film_id = f.film_id LIMIT 1
    ) dims) >= 5
  )
  ORDER BY RANDOM() LIMIT 1
  ```
  Or a simpler approach: just count distinct dimensions that have at least one tag for this film. Use whatever approach is cleanest.
- Insert the daily_challenge row
- Then pick 2 random decoy films (different from the target, also with posters)
- Return: `{films: [{film_id, title, year, poster_url}, ...], pool_size: int}`. All 3 are valid targets. The player picks one and that becomes the target. For the daily challenge, all 3 films are fixed for the day (so all players see the same 3 choices, but they might pick different targets — that's fine, it adds variety to the shareable scores). Store only one `film_id` in `daily_challenge`. Return that film + 2 random decoys. All are valid targets. The daily leaderboard tracks results by `challenge_date` regardless of which film was picked.

**`GET /game/random`** — Get 3 random films for free play:
```python
@router.get("/game/random")
async def get_random_films(
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
```
- Build a filtered pool query: `SELECT film_id, original_title, first_release_date, poster_url FROM film WHERE poster_url IS NOT NULL`
- Add optional filters: `EXTRACT(YEAR FROM first_release_date) >= :year_min`, same for year_max
- For language: join `film_language` where `is_original = TRUE` and `language_code = :language`
- Count the pool. If < 50, return error 400: `"Not enough films in this pool ({count}) — broaden your filters (minimum 50)"`
- Pick 3 random films from the pool: `ORDER BY RANDOM() LIMIT 3`
- Return: `{films: [...], pool_size: int}`

**`POST /game/check`** — Core game mechanic (called on every tag click):
```python
@router.post("/game/check")
async def check_tags(
    body: dict,  # {film_id: int, tags: [{dimension: str, value: str}], pool_filters?: {year_min, year_max, language}}
    db: AsyncSession = Depends(get_db),
):
```
- `body["film_id"]` is the target film
- `body["tags"]` is the list of all currently selected tags
- `body.get("pool_filters")` optionally restricts the base pool (for free play with decade/language filters)
- Build a COUNT query that applies all tags as AND filters (same logic as `list_films` but only returning count). For each tag in the list, add a subquery: `film_id IN (SELECT film_id FROM film_{dimension_table} ft JOIN {dimension_table} t ON ... WHERE t.{name_column} = :value)`. AND all subqueries together.
- Also apply pool_filters if present (year range, language).
- Execute two things:
  1. `SELECT COUNT(*) FROM film WHERE {all_conditions}` → `remaining_count`
  2. Check if target film matches all conditions: `SELECT 1 FROM film WHERE film_id = :target AND {all_conditions}` → `target_included`
- Return: `{remaining_count: int, target_included: bool, victory: bool}`
  - `victory = remaining_count == 1 and target_included`

**Performance note**: This endpoint is called on every click, so it must be fast. The query is essentially N subqueries ANDed together (one per tag). With indexes on the junction tables (which already exist), this should be fast even with 10 tags. But if performance becomes an issue, consider caching the current result set in the session.

**Dimension-to-table mapping**: Create a helper dict at module level:
```python
DIMENSION_TABLE_MAP = {
    "categories": ("film_genre", "genre_id", "category", "category_name"),
    "themes": ("film_theme", "theme_id", "theme_context", "theme_name"),
    "atmospheres": ("film_atmosphere", "atmosphere_id", "atmosphere_context", "atmosphere_name"),
    "characters": ("film_character", "character_id", "character_context", "character_name"),
    "motivations": ("film_motivation", "motivation_id", "motivation_context", "motivation_name"),
    "messages": ("film_message", "message_id", "message_context", "message_name"),
    "cinema_types": ("film_cinema_type", "cinema_type_id", "cinema_type_context", "cinema_type_name"),
    "time_periods": ("film_time_period", "time_period_id", "time_context", "time_period_name"),
    "place_contexts": ("film_place_context", "place_context_id", "place_context", "place_context_name"),
}
```
Verify the actual table/column names against `schema.sql` before using — the naming conventions vary across dimensions.

**`POST /game/joker/remaining`** — Show remaining films:
- Same filter logic as `/check`, but return the actual films (not just count)
- Limit to 20 results
- Return: `{films: [{film_id, title, year, poster_url}, ...]}`

**`POST /game/joker/hint`** — Suggest the best next tag:
- For each dimension, get the target film's tags in that dimension
- For each of those tags (that isn't already selected), compute what the remaining count would be if that tag were added
- Return the tag that reduces the count the most: `{dimension: str, tag: str, would_reduce_to: int}`
- Optimize by only checking tags from the target film, limit to ~20 candidate tags.

**`POST /game/joker/synopsis`** — Reveal synopsis:
- Simple: `SELECT summary FROM film WHERE film_id = :fid`
- Return: `{synopsis: str}`

**`POST /game/result`** — Save game result (requires auth):
- For daily mode: reject if user already has a result for today
- Return: `{saved: true, id: int}`

**`GET /game/stats`** — User game statistics (requires auth):
- Return: `{total_games, total_wins, avg_stars, best_stars, best_tags, current_daily_streak, max_daily_streak, games_by_mode}`

Register router in `main.py`: `app.include_router(game.router, prefix="/api")`

### Part 3 — Frontend: Game Page Structure

Create `frontend/src/pages/GamePage.tsx`:

State machine with 3 states: `"setup" | "playing" | "result"`. Renders `<GameSetup>`, `<GameBoard>`, or `<GameResult>` based on state. Dark theme, does NOT use Layout/Sidebar wrapper — own full-screen layout.

Add route in `App.tsx`: `<Route path="/game" element={<GamePage />} />`

### Part 4 — Frontend: GameSetup Component

`frontend/src/components/game/GameSetup.tsx`:
- Title: "Tag It" with game icon, subtitle "Isolate the film using as few tags as possible"
- Mode toggle: "Daily Challenge" / "Free Play" tabs
- Daily: "Start" button, calls `GET /api/game/daily`. If already played today, show result + "Play Free"
- Free play: decade buttons (All, 1950s–2020s) + language dropdown + "Start" with pool size
- After receiving 3 films: show as large cards, prompt "Pick the film you know best"

### Part 5 — Frontend: GameBoard Component

`frontend/src/components/game/GameBoard.tsx`:
- Top bar: target film mini, remaining counter (animated), lives (hearts), jokers
- 9 expandable taxonomy dimensions with clickable tag chips
- Chip states: `available`, `selected-correct` (green), `selected-wrong` (red strikethrough)
- On click: call `/api/game/check`, handle life loss or counter decrease
- No undo on correct tags
- Joker buttons: remaining (modal), hint (highlight), synopsis (modal)

### Part 6 — Frontend: GameResult Component

`frontend/src/components/game/GameResult.tsx`:
- Victory: poster animation, stars, stats, tag path, share button
- Game over: dimmed poster, attempt stats, share button
- Share formats Wordle-style text with dimension-colored squares
- Save result if authenticated

### Part 7 — Frontend: Supporting Components

- `LivesDisplay.tsx` — 3 hearts with shake animation on loss
- `RemainingCounter.tsx` — large animated number, color changes as it drops
- `JokerButton.tsx` — icon + label + remaining badge, disabled at 0

### Part 8 — Frontend: API Client + Types

Add GameFilm, GameTag, GameCheckResult, GameResultData, GameStats types to `api.ts`.
Add fetchDailyChallenge, fetchRandomFilms, checkGameTags, useJokerRemaining, useJokerHint, useJokerSynopsis, saveGameResult, fetchGameStats to `client.ts`.

### Part 9 — Navigation

Update Header.tsx: Add prominent "Play" link for all users (including anonymous) in the main header bar, not in the dropdown. If needed, remove the dashboard stats icon (it's already in the dropdown).

### Verification
- Daily challenge: shows 3 films, picking one starts the game, remaining counter starts at pool size
- Selecting a correct tag: counter decreases, chip turns green/amber
- Selecting a wrong tag: life lost (heart animation), tag crossed out red, counter unchanged, message shown
- 0 lives: game over screen with stats + share button
- Victory (remaining == 1): celebration, stars, share button
- Share button copies Wordle-style text to clipboard
- Jokers work: remaining shows film list, hint highlights a tag, synopsis shows text
- Free play: decade and language filters restrict the pool, minimum 50 enforced
- Daily mode: same 3 films for everyone on the same day
- Game result saved to database for authenticated users
- Game stats page shows streak, avg score, totals
- Anonymous users can play daily challenge but results aren't saved
- "Play" link visible in header for all users
- All existing functionality unchanged
