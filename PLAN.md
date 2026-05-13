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
| 8.6 | Editable fields + person data | ✅ DONE | Editable categories/financials/awards, person gender in pipeline, backfill_person_details script |
| 9 | Bulk ingestion (~2500 films) | ✅ DONE | Parse Films_list.docx, batch TMDB + Claude + DB insert |
| 10 | UX: empty tags, year inputs, studio search, film relations | ✅ DONE | Editable related films with posters, collapsible sidebar |
| 10.5 | Film detail layout + Taxonomy admin page | ✅ DONE | Production in hero, related films with posters, /admin/taxonomy CRUD, export script |
| 10.6 | Delete film, seen toggle on grid, backfill optimization, README | ✅ DONE | DELETE endpoint + trash button, FilmCard vu toggle, filtered backfill script, README.md |
| 11 | Deployment + auth (Supabase + Render + Vercel) | ✅ DONE | Admin auth, CORS from env, frontend auth context, deploy to cloud |
| 12 | Taxonomy restructure | ✅ DONE | merge dimensions, add sort_order grouping, rebalance tags |
| 13 | Performance optimization (deployed) | ✅ DONE | Parallel DB queries, React Query caching, region fix |
| 14 | Advanced 'click on tag' behaviour | ✅ DONE | Addition of 'Exclude' and 'Or' on multi-select |
| 15a | Supabase Auth + user roles + vu migration | ✅ DONE | JWT auth, user_profile, user_film_status, migrate film.vu |
| 15b | Personal tracking UI + Collection + Nav menu | ✅ DONE | Favorites/watchlist/rating/notes, /collection page, header dropdown |
| 15c | Tier-gated taxonomy access | ✅ DONE | Dimension gating by tier, filter limits, OR/NOT gating, upgrade prompts |
| 16a | Recommender: "Refine in Browse" button | ✅ DONE | Smart tag preselection from a film's tags, IDF-ranked, tier-aware |
| 16b | Recommender: Similar Films algorithm (in-DB) | ✅ DONE | IDF-weighted Jaccard across 9 dims + structural bonuses, on-demand SQL |
| 16c | Recommender: SimilarFilmsCarousel UI | ✅ DONE | Replace placeholder, "Why?" tooltips, tier-gated 3/6/12 results |
| 17a | Stats Dashboard — Quick / Financials / People / Taxonomy (MVP) | ✅ DONE | New /stats page, 4 tabs, tier-gated, single bulk endpoint |
| 17b | Production-country + franchise data prep, sidebar overhaul, Top 20 franchises | ✅ DONE | tmdb_collection + film_production_country tables, backfill scripts, sidebar reorg, exact franchise filter |
| 17c | Stats Dashboard — Taxonomy enhancements (% heatmap fix + 2 new heatmaps + per-person tags + cross-tab) | ✅ DONE | 5 sections: Categories % heatmap, cinema-movements heatmap, messages % heatmap, person filmography tag breakdown, atmosphere×category cross-tab |
| 17d | Stats Dashboard — Geography tab (world map + set-place treemap) | ✅ DONE | Production-country choropleth, country click → top films panel, set-place treemap (continent→country→city), country count stat card |
| 18 | Game mode — "Tag It" | ✅ DONE | Daily + free play, narrow down films by tags, 3 lives, jokers, shareable scores |

---

## Steps 1–11: Core Build (completed)

*(see git history for step details)*

## Step 12: Taxonomy restructure ✅

  Merging characters_type + character_context, cinema_type + cultural_movement, moving Disaster to
  themes and dialogs to cinema, adding sort_order-based grouping to 7 dimensions, adding new theme
  values (curse, game), renaming gang → team/group/gang.

---

## Step 13: Performance Optimization (Deployed) ✅

  Backend: pool_size 5→10, asyncio.gather() for 18 parallel queries in get_film().
  Frontend: React Query caching (staleTime 30s browse, 60s detail, Infinity taxonomy).
  Infrastructure: Render moved from Oregon → Frankfurt (10ms vs 150ms to Supabase Paris).

---

## Step 14: Advanced 'click on tag' behaviour ✅

  Frontend: TagFilter type (include/exclude/mode), 3 chip states (off/include/exclude), right-click
  exclude, AND/OR toggle. Backend: _not and _mode query params for all 10 dimensions.

---

## Step 15a: Supabase Auth + User Roles + vu Migration ✅

  Supabase Auth (email/password + Google OAuth), user tiers (free/pro/admin), auto-profile creation,
  per-user film status (seen/favorite/watchlist/rating/notes), film.vu migrated to user_film_status.

---

## Step 15b: Personal Tracking UI + My Collection + Nav Menu ✅

*(see git history for details)*

---

## Step 15c: Tier-Gated Taxonomy Access

Restrict taxonomy filter access based on user tier. Anonymous and free users see all dimensions but can only interact with a subset. Pro users get full access. This creates the core value proposition for upgrading.

---

## Step 16: Recommender Engine (in-DB)

Two complementary surfaces driven by the same taxonomy-based similarity:
- **Carousel** ("Similar Films" section on each film page) — passive, top-N algorithm-curated.
- **Button** ("Refine in Browse →" inside the same section header) — active, drops the user on /browse with the most distinctive tags pre-selected so they can iterate manually.

### Step 16d (later, no separate ticket) — Tuning loop

Manual rating of top-12 results on 10 reference films, adjust weights and bonuses iteratively. Optional admin debug view exposing per-dimension contribution to score.

---

## Step 17a: Stats Dashboard — MVP (Quick + Financials + People + Taxonomy)

*(see git history for details)*

---

## Step 17b: Production-country + franchise data prep, sidebar overhaul, Top 20 franchises ✅

*(see git history for details)*

---

## Step 17c: Stats Dashboard — Taxonomy enhancements ✅

*(see git history for details)*

---

## Step 17d: Stats Dashboard — Geography tab (world map + set-place treemap)

*(see git history for details)*

---

## Step 18: Game Mode — "Tag It"

### Goal
Build a game where the player picks a film and must isolate it from the full database by selecting taxonomy tags, minimizing the number of tags used. This is the primary differentiator from LLM-based film search — it requires a structured, verified, countable taxonomy that no chatbot can replicate.

### Game concept

**Core mechanic**: Player sees 3 random films (poster + title + year). Picks the one they know best. Then selects tags one by one across all 9 taxonomy dimensions to narrow the matching film count from ~4,000 down to 1. Fewest tags = best score.

**Lives system**: 3 lives (❤️❤️❤️). Selecting a tag that eliminates the target film = lose 1 life. The tag is blocked (not applied) and crossed out in red. At 0 lives = game over, revealing the optimal tag path.

**Jokers** (3 per round):
- **"Show remaining"** — reveals the list of films still matching current tags
- **"Hint tag"** — highlights the tag that would reduce the count the most while keeping the target film
- **"Synopsis peek"** — shows the target film's synopsis to jog memory

**Scoring**:

| Tags used | 3 lives | 2 lives | 1 life |
|---|---|---|---|
| 3–4 tags | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 5–6 tags | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 7+ tags | ⭐⭐⭐ | ⭐⭐ | ⭐ |

Jokers don't affect score but "clean wins" (no jokers) tracked separately.

**Two modes**:
- **Daily challenge**: Same film for everyone each day. Shareable result (like Wordle):
  ```
  🎬 CineTag Daily #42
  🎯 Found in 5 tags
  ❤️❤️🖤
  ⭐⭐⭐
  🟧🟧🟦🟧🟩⬛⬛⬛⬛
  ```
  Colored squares = dimensions used (without revealing actual tags).
- **Free play**: Unlimited rounds with random films. Optional filters to restrict the film pool.

**Pool filters** (free play only):
- By decade: 1950s, 1960s, ... 2020s
- By language: French, English, Japanese, Korean, etc.
- Combo allowed (e.g. "1970s + French")
- Minimum pool size enforced: if filtered pool < 50 films, show "Not enough films — broaden your filters"

### Database changes (Migration 012)

```sql
-- Daily challenge: one film per day
CREATE TABLE IF NOT EXISTS daily_challenge (
    challenge_date DATE PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Game results per user
CREATE TABLE IF NOT EXISTS game_result (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profile(id) ON DELETE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film(film_id),
    mode TEXT NOT NULL CHECK (mode IN ('daily', 'free')),
    challenge_date DATE,               -- only for daily mode
    tags_used INTEGER NOT NULL,
    lives_remaining INTEGER NOT NULL,   -- 0-3
    jokers_used INTEGER DEFAULT 0,
    stars INTEGER NOT NULL,             -- 1-5
    tag_sequence JSONB,                 -- ordered list of tags selected [{dim, tag, remaining_count, correct}]
    completed BOOLEAN DEFAULT TRUE,     -- false if game over
    played_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_result_user ON game_result(user_id);
CREATE INDEX IF NOT EXISTS idx_game_result_daily ON game_result(challenge_date);
CREATE INDEX IF NOT EXISTS idx_game_result_mode ON game_result(user_id, mode);
```

### Backend changes

**New router: `backend/app/routers/game.py`**

Endpoints:
- `GET /api/game/daily` — today's daily challenge (3 films + pool size), auto-created if missing
- `GET /api/game/random?year_min=&year_max=&language=` — 3 random films from filtered pool + pool size
- `POST /api/game/check` — core mechanic: receives tags, returns remaining_count + target_included + victory
- `POST /api/game/joker/remaining` — list of remaining films (max 20)
- `POST /api/game/joker/hint` — best next tag to pick
- `POST /api/game/joker/synopsis` — target film synopsis
- `POST /api/game/result` — save completed game (requires auth)
- `GET /api/game/stats` — user game statistics (requires auth)

### Frontend changes

**New page: `/game` — GamePage.tsx** with 3 states: Setup → Playing → Result

**7 new components** in `frontend/src/components/game/`:
- GameSetup, GameBoard, GameResult, LivesDisplay, RemainingCounter, JokerButton, ShareResult

**Navigation**: "Play" link in header, prominent, available to all users

### Access rules
- Daily challenge: available to everyone (anonymous + free + pro + admin) — viral hook, no gating
- Free play: requires authentication (free tier and above)
- Game stats/history: requires authentication
- All taxonomy dimensions available in game mode regardless of tier

### Files modified
- `database/migrations/012_game_mode.sql` — new tables
- `database/schema.sql` — updated for fresh installs
- `backend/app/routers/game.py` — new router (all game endpoints)
- `backend/app/main.py` — register game router
- `frontend/src/pages/GamePage.tsx` — new page
- `frontend/src/components/game/*.tsx` — 7 new components
- `frontend/src/api/client.ts` — game API functions
- `frontend/src/types/api.ts` — game types
- `frontend/src/components/layout/Header.tsx` — add game link to nav
- `frontend/src/App.tsx` — add /game route
