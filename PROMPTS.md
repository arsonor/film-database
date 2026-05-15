# Claude Code Prompts — Step-by-step

## Steps 1–14: Core Build + UX

*(see git history for original prompts)*

---

## Step 15a–c: Auth + Personal Tracking + Tier Gating

*(see git history for original prompts)*

---

## Step 16a–c: Recommender Engine

*(see git history for original prompts)*

---

## Step 17a–d: Stats Dashboard

*(see git history for original prompts)*

---

## Step 18 Prompt — Game Mode "Tag It"

*(see git history for original prompts)*

---

## Step 19 Prompt — Game Mode "Chain It" + Game Hub + Stats Page

Read CLAUDE.md, then PLAN.md (Step 19), then these files:
- `backend/app/routers/game.py` (full file — the existing Tag It game router with DIMENSION_TABLE_MAP, helpers, all endpoints)
- `backend/app/services/recommender.py` (for reference: similarity score logic, for pair selection)
- `frontend/src/pages/GamePage.tsx` (current Tag It page — will be renamed)
- `frontend/src/components/game/*.tsx` (all existing game components)
- `frontend/src/api/client.ts` (existing game API functions)
- `frontend/src/types/api.ts` (existing game types)
- `frontend/src/App.tsx`
- `frontend/src/components/layout/Header.tsx`
- `database/schema.sql`
- `database/migrations/022_game_mode.sql` (existing game tables)

### Overview

Three things in one step:
1. **Game Hub**: restructure routes so `/game` is a selection page, Tag It moves to `/game/tag-it`, Chain It lives at `/game/chain-it`
2. **Chain It game**: new game mode where the player connects two distant films by building a tag chain through intermediate films
3. **Unified Stats page**: `/game/stats` with per-game tabs, summary stats, and game history with film details

This is a large step. The backend extends the existing `game.py` router (reuse `DIMENSION_TABLE_MAP`, `_build_tag_clauses`, `_fetch_films`, `_pick_eligible_film` helpers). The frontend creates several new pages and components but follows the same patterns as Tag It.

### Part 1 — Database: Migration 023

Create `database/migrations/023_chain_it.sql`:

```sql
-- Step 19: Chain It game + game hub restructure

-- 1. Add game_type to daily_challenge (for multiple games sharing the table)
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS game_type TEXT NOT NULL DEFAULT 'tag_it';
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS target_film_id INTEGER REFERENCES film(film_id);

-- Recreate PK to include game_type
ALTER TABLE daily_challenge DROP CONSTRAINT IF EXISTS daily_challenge_pkey;
ALTER TABLE daily_challenge ADD PRIMARY KEY (challenge_date, game_type);

-- 2. Add game_type + chain-specific fields to game_result
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS game_type TEXT NOT NULL DEFAULT 'tag_it';
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS chain_length INTEGER;
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS origin_film_id INTEGER REFERENCES film(film_id);
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS target_film_id INTEGER REFERENCES film(film_id);

-- Update unique daily index to include game_type
DROP INDEX IF EXISTS idx_game_result_user_daily_unique;
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_result_user_daily_unique
    ON game_result(user_id, challenge_date, game_type) WHERE mode = 'daily';

CREATE INDEX IF NOT EXISTS idx_game_result_game_type ON game_result(game_type);
```

Also update `database/schema.sql` with these columns in the table definitions.

**Important**: After this migration, the existing Tag It endpoints must still work. All existing rows have `game_type='tag_it'` by default. The `daily_challenge` PK change means queries must include `game_type` in WHERE clauses. Update ALL existing Tag It queries in `game.py` that touch `daily_challenge` to add `AND game_type = 'tag_it'`.

### Part 2 — Backend: Update Existing Endpoints + Add Chain It Endpoints

**Update existing Tag It endpoints in `game.py`**:

- `GET /game/daily`: Add `AND game_type = 'tag_it'` to the daily_challenge query. Add `game_type = 'tag_it'` to the INSERT. Add `AND game_type = 'tag_it'` to the already_played check.
- `POST /game/result`: Accept optional `game_type` field in body (default `'tag_it'`). Store it. Update the duplicate check to include `AND game_type = :gt`.
- `GET /game/stats`: Group results by `game_type` as well as `mode`. Return `{tag_it: {daily: {...}, free: {...}}, chain_it: {daily: {...}, free: {...}}}`.

**New endpoint: `GET /game/history`**:
```python
@router.get("/game/history")
async def game_history(
    game_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
```
- Query `game_result` for this user, optionally filtered by `game_type`
- JOIN `film` to get titles + poster_urls for `film_id`, `origin_film_id`, `target_film_id`
- Order by `played_at DESC`
- Return paginated: `{items: [{id, game_type, mode, played_at, stars, completed, tags_used, chain_length, lives_remaining, jokers_used, film: {film_id, title, poster_url}, origin_film?: {...}, target_film?: {...}}], total, page, per_page, total_pages}`

**New Chain It endpoints**:

**`GET /game/chain/daily`**:
- Check `daily_challenge` for today + `game_type='chain_it'`
- If not exists: pick origin + target pair using `_pick_chain_pair(db)`. The pair must: both have poster + summary + ≥5 tag dimensions, share ≥1 common tag, be "far apart" (pick two random eligible films, verify ≥1 shared tag, retry up to 10 times if no shared tag). Store in `daily_challenge` with `game_type='chain_it'`, `film_id=origin`, `target_film_id=target`.
- Fetch film data for both + origin's tags (all 9 dimensions).
- Check if user already played today's chain daily.
- Return: `{origin: {film_id, title, year, poster_url, tags: {dimension: [tag_names]}}, target: {film_id, title, year, poster_url}, pool_size: int, already_played: {...} | null}`

**`GET /game/chain/random?year_min=&year_max=&language=`**:
- Same as chain/daily but picks a fresh random pair with optional pool filters.
- Return same shape (without `already_played`).

**`POST /game/chain/check-tag`**:
- Body: `{target_film_id: int, dimension: str, value: str}`
- Check if the target film has this tag: query the junction table.
- Return: `{correct: bool}`

**`POST /game/chain/get-films`**:
- Body: `{tags: [{dimension, value}], exclude_film_ids: [int], target_film_id: int, pool_filters?: {}}`
- Build WHERE clauses from accumulated tags using `_build_tag_clauses()`.
- Apply pool_filters using `_apply_pool_filters()`.
- Get total pool_size (COUNT).
- Determine if target is visible: `pool_size - len(exclude_film_ids) <= 10`. If yes, include target in results. If no, also exclude target from results.
- Always exclude `exclude_film_ids` from results.
- Fetch up to 20 films from the visible pool, ordered by `weighted_score DESC NULLS LAST`.
- Return: `{films: [GameFilm], pool_size: int, target_visible: bool}`

**`POST /game/chain/get-tags`**:
- Body: `{film_id: int}`
- For each dimension in `DIMENSION_TABLE_MAP`, query the film's tags.
- Return: `{tags: {categories: ["drama", "sci-fi"], themes: ["quest", "evolution"], ...}}`

**`POST /game/chain/joker/synopsis`** — same as existing Tag It joker/synopsis (reuse).

**`POST /game/chain/joker/reveal-tag`**:
- Body: `{target_film_id: int, used_dimensions: [str]}`
- Get all target tags. Filter to dimensions NOT in `used_dimensions`.
- Pick one randomly.
- Return: `{dimension: str, tag: str}`

**`POST /game/chain/result`** — save chain result. Same pattern as Tag It's `/game/result` but with `game_type='chain_it'` + additional fields: `chain_length`, `origin_film_id`, `target_film_id`. The `tag_sequence` JSONB stores: `[{step: int, film_id: int, film_title: str, dimension: str, tag: str, correct: bool}]`.

### Part 3 — Frontend: Route Restructure + Game Hub

**Rename** `frontend/src/pages/GamePage.tsx` → `frontend/src/pages/TagItPage.tsx`. Update component name. No logic changes.

**Create `frontend/src/pages/GameHubPage.tsx`**:
- Two game cards in a responsive grid (side by side desktop, stacked mobile):
  - **Tag It**: `Target` icon, "Isolate a film using as few tags as possible", daily badge if not played, "Play" → `/game/tag-it`
  - **Chain It**: `Link` icon, "Connect two distant films through shared tags", daily badge, "Play" → `/game/chain-it`
- Below: "My Stats & History →" link to `/game/stats` (authenticated only)
- Dark theme, no sidebar, full-width

**Update `App.tsx`** routes:
```tsx
<Route path="/game" element={<GameHubPage />} />
<Route path="/game/tag-it" element={<TagItPage />} />
<Route path="/game/chain-it" element={<ChainItPage />} />
<Route path="/game/stats" element={<GameStatsPage />} />
```

**Update `Header.tsx`**: game link → `/game` hub.

**Update `TagItPage.tsx`**: Add "← Back to Games" link. Remove inline stats, replace with "View all stats →" → `/game/stats`.

### Part 4 — Frontend: Chain It Page + Components

**Create `frontend/src/pages/ChainItPage.tsx`**: State machine setup → playing → result. State includes originFilm (with tags), targetFilm (no tags), currentFilm (with tags), chain (steps), accumulatedTags, lives, jokers, displayedFilms, poolSize, targetVisible. Renders ChainSetup, ChainBoard, or ChainResult.

**Create `frontend/src/components/game/ChainSetup.tsx`**:
- Mode toggle: Daily / Free Play
- Daily: origin + target posters side by side, "Connect these films →" button
- Free play: decade/language filters + Start
- "← Back to Games" link

**Create `frontend/src/components/game/ChainBoard.tsx`**:
- Top bar: origin (mini) → ChainProgress → target (mini with "?"). Lives + jokers.
- Main area split: current film panel (poster + tags as clickable chips) | film list panel (poster grid)
- Tag click → `chain/check-tag` → correct: green, refresh film list | wrong: life lost, red strikethrough
- Film click → if target: WIN | otherwise: becomes new current film, load its tags, update chain
- Already-accumulated tags greyed/disabled. Already-wrong tags crossed out.
- Jokers: synopsis (modal), reveal tag (highlight), shuffle (re-randomize list)

**Create `frontend/src/components/game/ChainProgress.tsx`**:
- Horizontal scrollable chain: `[Toy Story] →quest→ [Megalopolis] →sci-fi→ ...`
- Small posters (40px) with tag labels between
- Origin highlighted, target shows "?" until won

**Create `frontend/src/components/game/FilmPickList.tsx`**:
- Scrollable poster grid (4-5 columns), clickable
- Pool size shown: "N films matching"
- Target card gets amber border/glow when `targetVisible` is true

**Create `frontend/src/components/game/ChainResult.tsx`**:
- Victory: full chain visualization (posters + tags), stars, share button
- Game over: partial chain, "ran out of lives", share button
- Share format: `🔗 CineTag Chain #17\n🎬 Film1 → Film2 → ... → Target\n📏 N steps | ❤️❤️🖤 | ⭐⭐⭐⭐\nhttps://cinetag.eu/game`
- "View all stats →" + "Play again" / "Back to Games"

### Part 5 — Frontend: Unified Game Stats Page

**Create `frontend/src/pages/GameStatsPage.tsx`**:
- Requires auth, redirect if anonymous
- Tab bar: "Tag It" / "Chain It"
- "← Back to Games" link
- Each tab: stats summary cards (total games, wins, avg stars, best score, daily streak) + paginated history table (date, film(s) with posters linking to `/films/:id`, mode, tags/chain length, lives, stars, result)

### Part 6 — Frontend: API Client + Types

Add Chain It types to `types/api.ts`: ChainGameFilm, ChainStep, ChainSetupResponse, ChainCheckTagResult, ChainGetFilmsResult, ChainGetTagsResult, ChainRevealTagResult, GameHistoryItem, PaginatedGameHistory.

Add to `client.ts`: fetchChainDaily, fetchChainRandom, chainCheckTag, chainGetFilms, chainGetTags, chainJokerSynopsis, chainJokerRevealTag, saveChainResult, fetchGameHistory.

Update existing `saveGameResult` to accept `game_type` parameter (default `'tag_it'`).

### Verification
- `/game` shows Game Hub with two game cards + stats link
- Clicking "Tag It" → `/game/tag-it` works exactly as before (no regressions)
- Header game link now goes to `/game` hub
- Chain It daily: shows origin + target, starting a game loads origin's tags
- Picking a correct tag: chip turns green, film list refreshes with matching films
- Picking a wrong tag: life lost, chip red, message shown, same film stays current
- Clicking a film from the list: becomes new current film, its tags load, chain progress updates
- Target appears in film list when pool ≤ 10 (with special amber border)
- Clicking target in the list → victory screen with full chain visualization
- 0 lives → game over with partial chain shown
- Share button copies chain text to clipboard
- Jokers: synopsis shows target summary, reveal tag shows one target tag, shuffle re-randomizes film list
- Chain It daily: same origin+target for everyone, can only play once (localStorage + backend)
- Free play: decade/language filters work
- `/game/stats`: shows per-game tabs with stats + paginated history with film posters
- Game history items link to film detail pages
- All Tag It functionality unchanged after route rename to `/game/tag-it`
