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

*(see git history for original prompts)*

---

## Step 20 Prompt — Game Mode "Guess It"

Read CLAUDE.md, then PLAN.md (Step 20), then these files:
- `backend/app/routers/game.py` (full file — Tag It + Chain It endpoints, DIMENSION_TABLE_MAP, helpers)
- `backend/app/services/recommender.py` (for similar films query — used for decoy selection)
- `frontend/src/pages/GameHubPage.tsx`
- `frontend/src/pages/GameStatsPage.tsx`
- `frontend/src/pages/ChainItPage.tsx` (for reference: game page pattern)
- `frontend/src/components/game/*.tsx` (existing game components)
- `frontend/src/api/client.ts` (existing game API functions)
- `frontend/src/types/api.ts` (existing game types)
- `frontend/src/App.tsx`
- `database/schema.sql`
- `database/migrations/023_chain_it.sql` (current game table structure)

### Overview

Build "Guess It" — the third game mode. The program picks a hidden target film and generates a 3×4 grid of 12 films (target + 11 decoys at varying similarity). The player reveals tags one at a time and eliminates films that don't match. Removing a film that actually matches all revealed tags costs a life. Removing the target = game over. The player can also risk an early guess at any point.

The backend leverages the existing recommender for smart decoy selection. The frontend follows the same page/component patterns as Tag It and Chain It. The Game Hub and Stats pages are updated to include the third game.

### Part 1 — Database: Migration 024

Create `database/migrations/024_guess_it.sql`:

```sql
-- Step 20: Guess It game — add decoy storage for daily challenges
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS decoy_film_ids INTEGER[];
```

No new tables — `game_result` already supports `game_type`. Guess It uses `game_type='guess_it'`. The `tags_used` column stores the number of tags revealed. The `tag_sequence` JSONB stores the order of revealed tags + elimination actions.

Update `database/schema.sql` to include the `decoy_film_ids` column in the `daily_challenge` definition.

### Part 2 — Backend: Guess It Endpoints

Add all new endpoints to `backend/app/routers/game.py`. Reuse existing helpers (`DIMENSION_TABLE_MAP`, `_build_tag_clauses`, `_fetch_films`, `_pick_eligible_film`, `_film_row_to_dict`).

**New helper: `_build_guess_grid(db, target_film_id, pool_filters=None)`**:

Builds the 12-film grid (target + 11 decoys) using a similarity gradient:

```python
async def _build_guess_grid(db: AsyncSession, target_film_id: int, pool_filters: dict | None = None) -> list[int]:
    """Build a 12-film grid: target + 11 decoys at varying similarity."""
    from backend.app.services.recommender import get_similar_films
    
    # Get similar films ranked by score
    similar = await get_similar_films(db, target_film_id, limit=50)
    # similar is a list of {film_id, score, ...} sorted by score desc
    
    similar_ids = [s["film_id"] for s in similar if s["film_id"] != target_film_id]
    
    decoys = []
    
    # 3 very similar (top 10)
    top_pool = similar_ids[:10]
    decoys.extend(random.sample(top_pool, min(3, len(top_pool))))
    
    # 4 moderately similar (rank 11-30)
    mid_pool = [fid for fid in similar_ids[10:30] if fid not in decoys]
    decoys.extend(random.sample(mid_pool, min(4, len(mid_pool))))
    
    # 4 loosely related (rank 31-50 or random)
    low_pool = [fid for fid in similar_ids[30:50] if fid not in decoys]
    if len(low_pool) >= 4:
        decoys.extend(random.sample(low_pool, 4))
    else:
        decoys.extend(low_pool)
        # Fill remaining with random films
        needed = 11 - len(decoys)
        if needed > 0:
            existing = set(decoys + [target_film_id])
            r = await db.execute(
                text("""SELECT film_id FROM film 
                        WHERE poster_url IS NOT NULL 
                        AND film_id <> ALL(:excl)
                        ORDER BY RANDOM() LIMIT :n"""),
                {"excl": list(existing), "n": needed}
            )
            decoys.extend([row[0] for row in r.fetchall()])
    
    # Shuffle target + decoys
    grid = [target_film_id] + decoys[:11]
    random.shuffle(grid)
    return grid
```

If `get_similar_films` is not easily callable from the router (it may use a different async pattern), alternatively: query the similar films endpoint's underlying SQL directly, or build a simpler similarity check using shared tag counts. The key requirement is the gradient — some decoys very similar, some loosely related.

**`GET /game/guess/daily`**:
```python
@router.get("/game/guess/daily")
async def get_guess_daily(
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
```
- Check `daily_challenge` for today + `game_type='guess_it'`
- If not exists:
  - Pick a random eligible target film (poster + summary + ≥5 dimensions) using `_pick_eligible_film`
  - Build the grid using `_build_guess_grid(db, target_id)`
  - Store: `daily_challenge(challenge_date=today, game_type='guess_it', film_id=target_id, decoy_film_ids=grid_without_target)`
  - Commit
- Fetch film data for all 12 films in the grid
- Reconstruct grid order: for daily, use a deterministic shuffle seeded by date + target_id so all players see the same grid arrangement
- Check if user already played today's guess daily
- Return: `{grid: [GameFilm], target_film_id: int, already_played: {...} | null}`

Note on security: `target_film_id` is sent to the frontend (needed for backend calls). A determined user could find it in network inspector. This is acceptable — same pattern as Tag It/Chain It.

**`GET /game/guess/random?year_min=&year_max=&language=`**:
```python
@router.get("/game/guess/random")
async def get_guess_random(
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
```
- Pick random eligible target from filtered pool
- Build grid using `_build_guess_grid(db, target_id, pool_filters)`
- Return: `{grid: [GameFilm], target_film_id: int}`

**`POST /game/guess/reveal-tag`**:
```python
@router.post("/game/guess/reveal-tag")
async def guess_reveal_tag(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
```
- Body: `{target_film_id: int, revealed_tags: [{dimension, value}], remaining_film_ids: [int]}`
- Get all target's tags (all 9 dimensions) minus already revealed tags
- For each candidate tag: count how many films in `remaining_film_ids` (excluding target) also have this tag
- Pick the tag with the **lowest count** (fewest decoys match → most films can be eliminated)
- If tied, prefer tags from dimensions not yet revealed (more variety)
- Return: `{dimension: str, tag: str, display: str}` where `display` is formatted like "Atmosphere: claustrophobic"

**`POST /game/guess/remove`**:
```python
@router.post("/game/guess/remove")
async def guess_remove_film(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
```
- Body: `{target_film_id: int, film_id_to_remove: int, revealed_tags: [{dimension, value}]}`
- If `film_id_to_remove == target_film_id`: return `{correct: false, is_target: true}` (game over)
- For each revealed tag, check if `film_id_to_remove` has that tag (query junction tables)
- If film matches ALL revealed tags: return `{correct: false, is_target: false}` (wrong removal, life lost)
- If film does NOT match at least one tag: return `{correct: true, is_target: false}` (valid removal)

**`POST /game/guess/early-guess`**:
```python
@router.post("/game/guess/early-guess")
async def guess_early(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
```
- Body: `{target_film_id: int, guessed_film_id: int}`
- Return: `{correct: bool}`

**`POST /game/guess/joker/synopsis`** — reuse existing synopsis pattern with target_film_id.

**`POST /game/guess/joker/decade`**:
```python
@router.post("/game/guess/joker/decade")
async def guess_joker_decade(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
```
- Body: `{target_film_id: int}`
- Query: `SELECT first_release_date FROM film WHERE film_id = :fid`
- Compute decade: `year // 10 * 10` → format as "1990s"
- Return: `{decade: str}`

**`POST /game/guess/joker/director`**:
```python
@router.post("/game/guess/joker/director")
async def guess_joker_director(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
```
- Body: `{target_film_id: int}`
- Query director from `film_crew` + `person` where role = 'Director'
- Return: `{director: str}` (first director name, or comma-separated if multiple)

**Save result**: Reuse existing `POST /game/result` endpoint with `game_type='guess_it'`. The `tags_used` field stores number of tags revealed. The `tag_sequence` JSONB stores: `[{action: "reveal"|"remove"|"wrong_remove"|"guess", dimension?: str, tag?: str, film_id?: int, film_title?: str}]`.

### Part 3 — Frontend: Guess It Page

**Create `frontend/src/pages/GuessItPage.tsx`**:

State machine: `"setup" | "playing" | "result"`

State:
```ts
const [phase, setPhase] = useState<Phase>("setup");
const [mode, setMode] = useState<"daily" | "free">("daily");
const [grid, setGrid] = useState<GameFilm[]>([]);              // all 12 films
const [targetFilmId, setTargetFilmId] = useState<number>(0);   // hidden target
const [revealedTags, setRevealedTags] = useState<{dimension: string, value: string, display: string}[]>([]);
const [removedFilmIds, setRemovedFilmIds] = useState<Set<number>>(new Set());
const [lives, setLives] = useState(3);
const [jokersRemaining, setJokersRemaining] = useState(3);
const [victory, setVictory] = useState(false);
const [actionLog, setActionLog] = useState<GuessAction[]>([]);  // for tag_sequence
```

Renders `<GuessSetup>`, `<GuessBoard>`, or `<GuessResult>` based on phase.

Add route in `App.tsx`: `<Route path="/game/guess-it" element={<GuessItPage />} />`

### Part 4 — Frontend: Guess It Components

**Create `frontend/src/components/game/GuessSetup.tsx`**:
- Mode toggle: Daily / Free Play
- Free play: optional decade/language filters
- Start button
- "← Back to Games" link

**Create `frontend/src/components/game/GuessBoard.tsx`**:

Layout:
- **Top area**: Revealed tags displayed as a growing row of tag badges (e.g. `[Atmosphere: claustrophobic] [Theme: psychological]`). Prominent "Reveal Tag" button with a count of tags revealed so far.
- **Lives** (3 hearts) + **Joker buttons** (Synopsis, Decade, Director)
- **Main grid**: 3×4 poster grid (responsive: 2×6 on mobile). Each cell is a `FilmGridCell`.

"Reveal Tag" button click:
1. Call `POST /game/guess/reveal-tag` with `{target_film_id, revealed_tags, remaining_film_ids}`
2. Add the returned tag to `revealedTags` state
3. Animate the new tag badge appearing

**Create `frontend/src/components/game/FilmGridCell.tsx`**:

Props:
```ts
interface FilmGridCellProps {
  film: GameFilm;
  removed: boolean;
  onRemove: (filmId: number) => void;
  onGuess: (filmId: number) => void;
}
```

States:
- **Present**: shows poster + title + year. On click, show two action buttons overlay: "✕ Remove" (red) and "⭐ This is it!" (amber/gold)
- **Removed**: faded out / empty cell with subtle border. Not clickable.
- **Wrong removal**: shake animation + red flash, then back to Present state.
- **Revealed as target (game over)**: highlighted with special border/glow.

On "Remove" click:
1. Call `POST /game/guess/remove` with `{target_film_id, film_id_to_remove, revealed_tags}`
2. If `is_target: true` → game over
3. If `correct: false` (matches all tags) → shake animation, life lost, show message "This film matches all revealed tags!"
4. If `correct: true` → fade out animation, add to `removedFilmIds`
5. Check if only 1 film remains → auto-win if it's the target

On "This is it!" click:
1. Call `POST /game/guess/early-guess` with `{target_film_id, guessed_film_id}`
2. If correct → victory
3. If wrong → game over, reveal the actual target

**Create `frontend/src/components/game/GuessResult.tsx`**:

Victory:
- Target film poster (big, celebratory animation)
- "Guessed in {N} tags, eliminated {M} films"
- Stars display
- List of revealed tags
- Share button

Game over:
- Target film revealed (poster + title)
- Reason: "You eliminated the target!" or "Wrong guess — it was [Film Title]"
- Tags revealed so far
- Share button

Share format:
```ts
function formatGuessShareResult(...): string {
  const header = mode === "daily"
    ? `🔍 CineTag Guess It #${challengeNumber}`
    : `🔍 CineTag Guess It`;
  const hearts = "❤️".repeat(livesRemaining) + "🖤".repeat(3 - livesRemaining);
  const stars = "⭐".repeat(starCount);
  const status = victory
    ? `🎯 Guessed in ${tagsRevealed} tags (${eliminated} eliminated)`
    : `❌ Game over after ${tagsRevealed} tags`;
  return `${header}\n${status}\n${hearts}\n${stars}\n\nhttps://cinetag.eu/game`;
}
```

### Part 5 — Frontend: Update Game Hub + Stats + Types

**Update `GameHubPage.tsx`**: Add third game card:
```tsx
<GameCard
  icon={Search}  // from lucide-react
  title="Guess It"
  emoji="🔍"
  tagline="Eliminate films as tags are revealed"
  description="Find the hidden film by removing decoys one by one. Wrong removals cost lives. 3 lives, 3 lifelines."
  onPlay={() => navigate("/game/guess-it")}
  accent="border-emerald-500/40 hover:border-emerald-500"
/>
```

Adjust grid to `md:grid-cols-3` for 3 cards on desktop. Update subtitle: "Three ways to test your cinema knowledge."

**Update `GameStatsPage.tsx`**: Add "Guess It" tab. Show `guess_it` stats from the existing grouped stats endpoint. History shows: date, result, tags revealed, films eliminated, lives, stars, mode.

**Add to `frontend/src/types/api.ts`**:
```ts
export interface GuessSetupResponse {
  grid: GameFilm[];
  target_film_id: number;
  already_played?: AlreadyPlayedDaily | null;
}

export interface GuessRevealTagResult {
  dimension: string;
  tag: string;
  display: string;
}

export interface GuessRemoveResult {
  correct: boolean;
  is_target: boolean;
}

export interface GuessEarlyGuessResult {
  correct: boolean;
}

export interface GuessAction {
  action: "reveal" | "remove" | "wrong_remove" | "guess";
  dimension?: string;
  tag?: string;
  film_id?: number;
  film_title?: string;
}
```

**Add to `frontend/src/api/client.ts`**:
```ts
export async function fetchGuessDaily(): Promise<GuessSetupResponse> { ... }
export async function fetchGuessRandom(yearMin?, yearMax?, language?): Promise<GuessSetupResponse> { ... }
export async function guessRevealTag(targetFilmId, revealedTags, remainingFilmIds): Promise<GuessRevealTagResult> { ... }
export async function guessRemoveFilm(targetFilmId, filmIdToRemove, revealedTags): Promise<GuessRemoveResult> { ... }
export async function guessEarlyGuess(targetFilmId, guessedFilmId): Promise<GuessEarlyGuessResult> { ... }
export async function guessJokerSynopsis(filmId): Promise<{synopsis: string}> { ... }
export async function guessJokerDecade(filmId): Promise<{decade: string}> { ... }
export async function guessJokerDirector(filmId): Promise<{director: string}> { ... }
```

### Verification
- `/game` hub shows 3 game cards (Tag It, Chain It, Guess It)
- Guess It daily: shows 3×4 grid of 12 film posters, "Reveal Tag" button, 3 lives, 3 jokers
- Clicking "Reveal Tag" shows a new tag badge and the tag is recorded
- Clicking a film shows "Remove" and "This is it!" actions
- Correct removal: film fades out from grid
- Wrong removal (film matches all tags): film shakes, snaps back, life lost, message shown
- Removing the target: game over, target revealed
- Early correct guess: victory with bonus celebration
- Early wrong guess: game over, target revealed
- Victory when last film standing: automatic win
- Jokers: synopsis modal, decade reveal, director reveal
- Score based on tags revealed + lives remaining
- Share button copies formatted text to clipboard
- Daily mode: same grid for everyone, one play per day (localStorage + backend)
- Free play with decade/language filters works
- `/game/stats` has Guess It tab with stats and history
- Tag It and Chain It unchanged (no regressions)
