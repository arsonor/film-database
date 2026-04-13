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

