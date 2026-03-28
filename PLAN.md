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
| 9 | Bulk ingestion (~2500 films) | 🔄 IN PROGRESS | Parse Films_list.docx, batch TMDB + Claude + DB insert |
| 10 | Recommendation engine (in-DB) | 🔲 TODO | Tag similarity scoring |
| 11 | Claude-powered recommendations | 🔲 TODO | External film suggestions |
| 12 | Dashboard & stats | 🔲 TODO | Analytics, charts, coverage |

---

## Step 1: PostgreSQL Schema ✅

- `database/schema.sql` (603 lines) — Full DDL, 40+ indexes, updated_at trigger
- `database/seed_taxonomy.sql` (445 lines) — All lookup tables pre-populated

## Step 2: TMDB Integration Module ✅

- `backend/app/services/tmdb_service.py` — Async TMDB client
- `backend/app/services/tmdb_mapper.py` — TMDB → DB mapper
- `scripts/parse_film_list.py` — Films_list.docx parser
- `scripts/tmdb_resolver.py` — Batch resolver with resume

## Step 3: Claude Enrichment Module ✅

- `backend/app/services/claude_enricher.py` — Taxonomy classification via Claude API
- `backend/app/services/taxonomy_config.py` — All valid taxonomy values + reference examples
- `scripts/claude_enrichment_runner.py` — CLI batch enrichment
- `scripts/db_inserter.py` — Full DB insertion pipeline
- `scripts/test_enrichment_pipeline.py` — Validation against reference films

## Step 4: Seed 3 Reference Films ✅

- `scripts/data/reference_films_fallback.json` — Complete pre-built data for 3 films
- `scripts/seed_reference_films.py` — Orchestration (full + offline modes)
- `scripts/verify_db.py` — 14 verification queries + PASS/FAIL
- `database/setup_db.sh` + `database/setup_db.py` — DB setup scripts

## Step 4.5: Fix Awards + Streaming Support ✅

*(see PLAN.md git history for details)*

## Step 5: Backend API (FastAPI) ✅

*(see PLAN.md git history for details)*

## Step 5.5: API Enhancements — Geography, Language & Missing Filters ✅

*(see PLAN.md git history for details)*

## Step 6: Frontend — Browse, Search & Filter ✅

*(see PLAN.md git history for details)*

## Step 6.5: Taxonomy Refinements + Filter UX Fixes ✅

- Migration `006_sort_order.sql` — sort_order columns, theme merges (trauma/accident, AI/technology), motivation cleanup
- Backend: AND logic (HAVING COUNT) in all taxonomy filters, parent expansion for hierarchical dims (themes, categories)
- Backend: Categories filter handles composite "Parent: sub" format, studios filter + taxonomy dimension
- Frontend: Director filter removed, dual-handle year range slider, studios dropdown, theme/time group separators

## Step 7: Film Detail View + Edit ✅

- Full detail page with cinematic hero section (backdrop gradient, poster, meta, vu toggle, external links)
- Cast/crew sections with TMDB photos, clickable → `/browse?q=Name`
- All taxonomy sections with inline editing (EditableTagSection)
- Awards table, streaming badges, related films, similar films placeholder
- Backend: PATCH `/films/{id}/vu` for lightweight toggle
- Bug fixes: tag dropdown cap removed (was limited to 15), person photo tmdb_id mismatch fixed
- New script: `refresh_person_photos.py` (name-based matching against TMDB movie credits)

## Step 8: Add Film Workflow ✅

- Backend: `add_film.py` router with GET `/add-film/search` and POST `/add-film/enrich`
- Frontend: `AddFilmPage.tsx` 3-step wizard (Search → Enrich → Review → Save)
- Enrichment quality: rewritten system prompt, new taxonomy values (migration 007), underscore renames (migration 008)

## Step 8.5: Auto-link Franchise Sequels via TMDB Collection ✅

- Migration 009: `tmdb_collection_id` column + auto-linking in `create_film()`
- New scripts: `backfill_collection_ids.py`, `refresh_streaming.py`

## Step 8.6: Editable Fields + Person Data ✅

- Frontend: `EditableTagSection` for categories, `EditableFinancials` component, editable `AwardsTable` (won/nominated toggle + remove)
- Backend: awards in `FilmUpdate` + clear-and-reinsert in `update_film()`, gender in `_find_or_create_person()`
- Pipeline: `tmdb_mapper.py` passes gender (TMDB_GENDER_MAP) in cast/crew dicts
- New script: `backfill_person_details.py` (gender, birth/death dates, nationality from TMDB /person/{id})

---

## Step 9: Bulk Ingestion (~2500 films)

### Goal

Ingest the full ~2500-film collection from `Films_list.docx` into the database using the existing 4-stage pipeline: parse → resolve (TMDB) → enrich (Claude) → insert (DB). All scripts already exist from steps 2-3 — this step is about running them at scale and handling the results.

### Pipeline Overview

The pipeline runs as **4 sequential stages**, each producing a JSON file that feeds the next. Every stage has resume/checkpoint capability — if interrupted, re-running picks up where it left off.

```
Films_list.docx
    ↓  parse_film_list.py
parsed_films.json (~2500 entries: title, year, region)
    ↓  tmdb_resolver.py (TMDB API, free)
resolved_films.json + unresolved_films.json
    ↓  claude_enrichment_runner.py (Anthropic API, ~$30-85)
enriched_films.json + enrichment_review.json
    ↓  db_inserter.py (local DB)
PostgreSQL database (fully populated)
```

### Stage 1: Parse the docx → `parsed_films.json`

```bash
# Copy Films_list.docx to scripts/data/ first
python scripts/parse_film_list.py
```

**Output:** `scripts/data/parsed_films.json` — structured list of ~2500 entries with `title`, `year`, `region`, `notes`, `original_title_hint`.

**Cost:** Free, instant. Verify the count and spot-check a few entries.

### Stage 2: Resolve against TMDB → `resolved_films.json`

```bash
python scripts/tmdb_resolver.py --batch-size 50
```

**What it does:** For each parsed film, searches TMDB in both fr-FR and en-US locales, picks the best match by popularity (±1 year tolerance), fetches full details + French title + credits + keywords.

**Output:** `scripts/data/resolved_films.json` (matched) + `scripts/data/unresolved_films.json` (no TMDB match found).

**Cost:** Free (TMDB API has no cost). Rate-limited at 40 req/10s, so ~2500 films takes ~15-30 minutes.

**Resume:** Saves checkpoints every 50 films. If interrupted, re-run the same command — already-resolved films are skipped.

**After completion:** Check `unresolved_films.json`. These are films TMDB couldn't match (obscure titles, spelling variations). Options: fix titles manually in `parsed_films.json` and re-run, or use `--retry-unresolved`.

### Stage 3: Claude enrichment → `enriched_films.json`

This is the **expensive step** — each film requires one Claude API call (~3k input + ~800 output tokens).

```bash
# Standard (real-time, ~$30-85 for 2500 films)
python scripts/claude_enrichment_runner.py --batch-size 10

# Or process in chunks (e.g., 100 films at a time)
python scripts/claude_enrichment_runner.py --start-index 0 --end-index 100
python scripts/claude_enrichment_runner.py --start-index 100 --end-index 200
# etc.
```

**Cost estimate (claude-sonnet-4-20250514 at $3/$15 per MTok):**
- ~2500 films × ~3000 input tokens = ~7.5M input tokens → ~$22.50
- ~2500 films × ~800 output tokens = ~2.0M output tokens → ~$30.00
- **Total: ~$50-55** (real-time standard API)

**With Anthropic Batch API (50% discount, 24h turnaround):** ~$25-28. Requires a separate batch submission script (not yet built — would need to create `scripts/claude_batch_enrichment.py`).

**With prompt caching:** The system prompt (~2000 tokens) is identical for every request. With caching, input cost drops by ~90% for the cached portion. Combined with batching: potentially ~$20-25 total.

**Resume:** Saves checkpoint every 10 films. Already-enriched films (by tmdb_id) are skipped on re-run.

**Output:** `scripts/data/enriched_films.json` (all enriched) + `scripts/data/enrichment_review.json` (low-confidence or errored).

**After completion:** Review `enrichment_review.json` for films with low confidence scores or errors. These can be re-enriched with `--review-only`.

### Stage 4: Insert into database

```bash
# Dry run first (validates data, no DB changes)
python scripts/db_inserter.py --dry-run

# Actual insertion
python scripts/db_inserter.py --batch-size 20
```

**What it does:** For each enriched film, inserts the film + all junction tables (cast, crew, studios, titles, taxonomy tags, awards, streaming, geography, source). Each film is one transaction.

**Duplicate detection:** Yes — checks `tmdb_id` against existing films in the DB. Already-present films are **skipped** (not overwritten). The 4+ films you've already added manually will not be duplicated.

**Cost:** Free, local DB. ~2500 inserts takes a few minutes.

**Output:** Summary with inserted/skipped/error counts.

### Post-Ingestion Maintenance

After the 4 stages complete:

```bash
# Backfill person details (gender, birth/death, nationality)
python scripts/backfill_person_details.py

# Backfill TMDB collection IDs + auto-link sequels
python scripts/backfill_collection_ids.py

# Refresh streaming platform data
python scripts/refresh_streaming.py

# Verify database integrity
python scripts/verify_db.py
```

### Monitoring Progress

Each script prints progress bars (via tqdm) and saves checkpoints. You can monitor:
- **Stage 2:** Watch `resolved_films.json` grow, check `unresolved_films.json` for problem titles
- **Stage 3:** Watch `enriched_films.json` grow, check console for cost estimates
- **Stage 4:** Console shows inserted/skipped/error per batch

All intermediate JSON files are preserved — you can inspect, fix, and re-run any stage without losing previous work.