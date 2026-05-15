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
| 19 | Game mode — "Chain It" + Game Hub + Stats page | ✅ DONE | Chain films through shared tags, game selection hub, unified stats + history |

---

## Steps 1–11: Core Build (completed)

*(see git history for step details)*

## Step 12–17d: Feature Development (completed)

*(see git history for step details)*

---

## Step 18: Game Mode — "Tag It"

*(see git history for details)*

---

## Step 19: Game Mode — "Chain It" + Game Hub + Stats Page

### Goal
1. Build a second game: "Chain It" — connect two distant films by building a chain through shared tags.
2. Restructure `/game` into a Game Hub with game selection.
3. Create a unified Game Stats page with per-game stats and game history.

### Chain It — Game Concept

**Setup**: The system picks an origin film and a target film. They must share at least 1 tag (so the game is winnable) but have low similarity (so it's not trivial). The player sees both films (poster + title + year) but only the origin's tags are visible. The target's tags are hidden.

**Each round**:
1. Player sees the current film's tags (all 9 dimensions). Pick ONE tag you believe the target also has.
2. If correct: tag is accumulated into the chain. The system displays a list of films matching ALL accumulated tags (sorted by popularity, excluding target + current film + all previous chain films).
3. If wrong: life lost, tag crossed out, not applied. Try another tag from the same film.
4. Player picks a film from the displayed list. That film becomes the new "current film," its tags are revealed.
5. Pick another tag (not already accumulated), and so on.
6. The target film is hidden from the display list until the matching pool (minus chain films) drops to ≤ 10 films. Then the target starts appearing in the list.
7. **Win**: player clicks the target film when it appears in the list.

**Lives**: 3 (same as Tag It). Wrong tag = lose 1 life. 0 lives = game over.

**Jokers** (3 per round):
- **"Synopsis"** — show the target film's synopsis
- **"Reveal tag"** — reveal one random tag of the target film (from a dimension not yet used in the chain)
- **"Shuffle"** — re-randomize the displayed film list (show different films from the same pool)

**Scoring**: Based on chain length (number of intermediate films, not counting origin and target) + lives remaining:

| Chain length | 3 lives | 2 lives | 1 life |
|---|---|---|---|
| 2–3 films | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 4–5 films | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 6+ films | ⭐⭐⭐ | ⭐⭐ | ⭐ |

**Display list size**: Show up to 20 films from the matching pool, sorted by popularity (weighted_score). Shuffle joker re-randomizes from the full pool.

**Two modes**: Daily challenge (fixed origin+target pair for everyone) + Free play (random pair, with optional decade/language pool filters).

**Shareable result**:
```
🔗 CineTag Chain #17
🎬 Toy Story → Megalopolis → Close Encounters → Annihilation → Solaris → 2001 → Stalker
📏 5 steps | ❤️❤️🖤 | ⭐⭐⭐⭐

https://cinetag.eu/game
```

### Pair Selection Algorithm

Both films must have poster + summary + ≥5 tag dimensions. Must share ≥1 common tag. Must have low similarity (not in each other's top-50 similar, or ≤3 shared tags total).

### Database Changes (Migration 023)

Add `game_type` + `target_film_id` columns to `daily_challenge`, recreate PK as `(challenge_date, game_type)`. Add `game_type` + `chain_length` + `origin_film_id` + `target_film_id` to `game_result`. Update unique index.

### Backend: New Chain Endpoints

- `GET /game/chain/daily` — origin + target pair + origin's tags
- `GET /game/chain/random` — random pair with optional pool filters
- `POST /game/chain/check-tag` — verify if a tag exists on the target
- `POST /game/chain/get-films` — matching films for accumulated tags (target hidden until pool ≤ 10)
- `POST /game/chain/get-tags` — all tags for a film
- `POST /game/chain/joker/synopsis`, `joker/reveal-tag`
- `GET /game/history` — paginated game history with film details

### Frontend: Route Restructure

- `/game` → GameHubPage (game selection)
- `/game/tag-it` → TagItPage (renamed)
- `/game/chain-it` → ChainItPage (new)
- `/game/stats` → GameStatsPage (new, unified stats + history)

### Files Modified
- `database/migrations/023_chain_it.sql`
- `backend/app/routers/game.py` — chain endpoints + game_type + history
- `frontend/src/pages/GameHubPage.tsx` — new
- `frontend/src/pages/TagItPage.tsx` — renamed
- `frontend/src/pages/ChainItPage.tsx` — new
- `frontend/src/pages/GameStatsPage.tsx` — new
- `frontend/src/components/game/Chain*.tsx` — 5 new components
- `frontend/src/api/client.ts` + `types/api.ts` — chain types + API functions
- `frontend/src/App.tsx` — new routes
- `frontend/src/components/layout/Header.tsx` — link to hub
