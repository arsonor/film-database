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
| 20 | Game mode — "Guess It" | ✅ DONE | Eliminate films from a smart list by revealing tags, 3 lives, early guess risk/reward |

---

## Steps 1–17d: Core Build + Features (completed)

*(see git history for step details)*

---

## Step 18: Game Mode — "Tag It"

*(see git history for details)*

---

## Step 19: Game Mode — "Chain It" + Game Hub + Stats Page

*(see git history for details)*

---

## Step 20: Game Mode — "Guess It"

### Goal
Build a third game: "Guess It" — deduce a hidden film by eliminating decoys from a curated list as tags are progressively revealed. Tests film knowledge through elimination and deduction.

### Game Concept

**Setup**: The program picks a hidden target film. It generates a list of 12 films: the target + 11 decoys selected across a gradient of similarity (some very similar, some loosely related). The player sees all 12 as a poster grid but doesn't know which is the target.

**Each round**:
1. Player clicks "Reveal tag" → the program reveals one of the target's tags (chosen to maximize elimination potential: fewest remaining decoys share it).
2. The player removes films they believe do NOT match the revealed tags.
3. **Correct removal** (film does NOT match all revealed tags): film removed, no penalty.
4. **Wrong removal** (film DOES match all revealed tags but isn't target): film shakes, snaps back, "This film matches all revealed tags — it stays!", lose 1 life.
5. **Removing the target**: immediate game over.
6. **Early guess**: click a film + "This is the target!" — correct = win, wrong = game over.

**Win condition**: Last film standing, or correct early guess.

**Lives**: 3. Lost on wrong removal.

**Scoring**:

| Tags revealed | 3 lives | 2 lives | 1 life |
|---|---|---|---|
| 1–2 tags | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 3–4 tags | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 5+ tags | ⭐⭐⭐ | ⭐⭐ | ⭐ |

**Jokers** (3): Synopsis, Decade reveal, Director reveal.

**Shareable**:
```
🔍 CineTag Guess It #31
🎯 Guessed in 3 tags (8 eliminated)
❤️❤️🖤 ⭐⭐⭐⭐
https://cinetag.eu/game
```

### Decoy Selection

11 decoys from the similarity recommender (Step 16b), gradient:
- 3 very similar (rank 1–10, share 5+ tags)
- 4 moderately similar (rank 11–30, share 2–4 tags)
- 4 loosely related (rank 31–50 or random, share 0–1 tags)

### Tag Reveal Order

Reveal the target tag shared by the fewest remaining decoys → maximizes elimination.

### Database (Migration 024)

Add `decoy_film_ids INTEGER[]` to `daily_challenge`. No new tables.

### Backend: New endpoints in `game.py`

- `GET /game/guess/daily` — grid of 12 + target_film_id + already_played
- `GET /game/guess/random` — with pool filters
- `POST /game/guess/reveal-tag` — best next tag based on remaining films
- `POST /game/guess/remove` — validate removal (correct/wrong/is_target)
- `POST /game/guess/early-guess` — validate guess
- `POST /game/guess/joker/synopsis`, `joker/decade`, `joker/director`

### Frontend

- `/game/guess-it` → GuessItPage (Setup → Playing → Result)
- 4 new components: GuessSetup, GuessBoard, GuessResult, FilmGridCell
- Update GameHubPage (3rd card), GameStatsPage (3rd tab), App.tsx (route)

### Files Modified
- `database/migrations/024_guess_it.sql`
- `backend/app/routers/game.py`
- `frontend/src/pages/GuessItPage.tsx` — new
- `frontend/src/pages/GameHubPage.tsx` — 3rd card
- `frontend/src/pages/GameStatsPage.tsx` — 3rd tab
- `frontend/src/components/game/Guess*.tsx` — 3 new
- `frontend/src/components/game/FilmGridCell.tsx` — new
- `frontend/src/api/client.ts` + `types/api.ts`
- `frontend/src/App.tsx`
