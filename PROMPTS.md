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

## Step 7 Prompt — Film Detail View + Edit

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 7 specification (sections A through H). Then read ALL of the following files to understand the current codebase:

**Backend (what exists — minor changes):**
- `backend/app/routers/films.py` — Existing `GET /api/films/{film_id}` detail endpoint and `PUT /api/films/{film_id}` update endpoint
- `backend/app/schemas/film.py` — FilmDetail, FilmUpdate, CastMember, CrewMember, AwardOut, etc.

**Frontend (what you'll create/modify):**
- `frontend/src/pages/FilmDetailPage.tsx` — Current placeholder, to be replaced with full detail page
- `frontend/src/types/api.ts` — Add FilmDetail types (FilmTitle, CrewMember, CastMember, FilmSetPlace, SourceOut, AwardOut, FilmRelation, FilmDetail)
- `frontend/src/api/client.ts` — Add fetchFilmDetail, updateFilm, toggleVu functions
- `frontend/src/hooks/useFilmDetail.ts` — NEW: hook to fetch and manage film detail state
- `frontend/src/components/films/PersonCard.tsx` — NEW: clickable person card (photo + name + role)
- `frontend/src/components/films/EditableTagSection.tsx` — NEW: view/edit mode for taxonomy tags
- `frontend/src/components/films/SimilarFilmsCarousel.tsx` — NEW: placeholder for future recommendations
- `frontend/src/components/films/ExternalLinks.tsx` — NEW: TMDB, IMDb, Allociné, Wikipedia link buttons
- `frontend/src/components/films/AwardsTable.tsx` — NEW: formatted awards display
- `frontend/src/components/films/SectionHeading.tsx` — NEW: consistent section header with optional edit button
- `frontend/src/hooks/useFilterState.ts` — Verify q param is read from URL (should already work)
- `frontend/src/lib/utils.ts` — May need helpers: formatCurrency, formatPersonName, buildExternalUrl

**Existing UI components to reference for patterns:**
- `frontend/src/components/layout/Header.tsx` — Search bar pattern (for person click → search navigation)
- `frontend/src/components/films/FilmCard.tsx` — Current card linking to detail page
- `frontend/src/components/filters/FilterSection.tsx` — Collapsible section pattern
- `frontend/src/index.css` — Dark theme color variables (background, foreground, primary/amber, muted, card, border)

### Goal

Build a rich film detail page at `/films/:id` displaying all metadata from the API. The page has a cinematic hero section (backdrop + poster + key info), followed by organized content sections for synopsis, cast & crew, classification tags, settings, production, awards, streaming, and related films.

**Key interactions:**
1. **Seen/Unseen toggle** — prominent button in hero, optimistic update via `PUT /api/films/{id}` (or optional `PATCH /api/films/{id}/vu`)
2. **Person navigation** — clicking any cast/crew member navigates to `/browse?q=PersonName`, leveraging existing full-text search
3. **Tag editing** — each taxonomy section has an edit button; edit mode shows removable tags + autocomplete to add new ones from the taxonomy; save sends `PUT /api/films/{id}`
4. **External links** — TMDB, IMDb, Allociné (via Google search), Wikipedia links open in new tabs
5. **Similar Films placeholder** — empty carousel skeleton, ready for steps 9-10

### Implementation Priorities

1. Start with the page layout + hero section + all read-only data display. Get the full page rendering first.
2. Add the seen/unseen toggle.
3. Add person click navigation.
4. Add external links.
5. Add the editable tag sections last (most complex).
6. Add the similar films placeholder skeleton.

### Backend Addition (optional)

If helpful, add a lightweight PATCH endpoint for the vu toggle in `films.py`:
```python
@router.patch("/films/{film_id}/vu")
async def toggle_vu(film_id: int, vu: bool = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("UPDATE film SET vu = :vu WHERE film_id = :fid RETURNING film_id"),
        {"fid": film_id, "vu": vu}
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")
    await db.commit()
    return {"film_id": film_id, "vu": vu}
```

### New shadcn/ui Components to Install

```bash
cd frontend
npx shadcn@latest add dialog
npx shadcn@latest add tabs
npx shadcn@latest add tooltip
npx shadcn@latest add toggle
npx shadcn@latest add command
npx shadcn@latest add popover
npx shadcn@latest add toast
```

Only install what's actually needed — skip any that aren't used in the final implementation.

### Design Requirements

- Dark theme consistent with existing browse page (charcoal bg, amber accent)
- Backdrop image: full width, gradient overlay fading to background at bottom
- Poster: ~300px wide on desktop, full width on mobile, subtle shadow
- Cast photos: ~80px wide circles or rounded squares, horizontally scrollable
- Crew photos: ~60px, grouped by role
- Tags: use existing Badge component with same styling as browse page
- Edit mode: inline, no full-page form. Toggle between view and edit per section.
- Mobile: hero stacks vertically (poster above info), cast/crew scroll horizontally, sections full width

### Validation

1. `/films/1` renders full detail for first seeded film
2. Backdrop + poster + title + year + duration display correctly
3. All taxonomy sections show populated tags
4. Cast photos render from TMDB CDN (or fallback placeholder)
5. Clicking a person → `/browse?q=Name` → browse shows their films
6. Seen toggle works (visual + API call)
7. TMDB/IMDb links open correct external pages
8. Edit mode: remove a tag, add a tag, save → detail refreshes with changes
9. Awards display or "no awards" message
10. Related films link to other detail pages (if any in DB)
11. "Similar Films" placeholder section visible
12. Back to browse preserves filter state
13. Responsive on mobile

Do NOT run the server or npm commands yourself. Just create/modify the files correctly. The user will run and test manually.
