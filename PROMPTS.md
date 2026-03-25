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
- API client with Vite proxy (/api → port 8000), repeated keys for array params
- 8 shadcn/ui components: badge, button, input, scroll-area, select, separator, sheet, skeleton
- Also: scripts/refresh_posters.py (TMDB CDN refresh), fixed La Haine tmdb_id (3405→406)

---
