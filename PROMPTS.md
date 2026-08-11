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

*(see git history for original prompts)*

---

## Step 21a Prompt — Taxonomy v2: Database Migration + Seed Rewrite

Read CLAUDE.md, then PLAN.md (Step 21), then these files:
- `database/schema.sql` (dimension + junction table structure)
- `database/seed_taxonomy.sql` (current taxonomy — will be rewritten)
- `database/migrations/016_taxonomy_tag_updates.sql` (pattern reference for renames)
- `database/migrations/018_tag_descriptions.sql` (to learn the exact `tag_description.dimension` key format)

### Overview

Migrate the taxonomy from 9 dimensions to 7. The `motivation_relation` and `message_conveyed` dimensions are dissolved: their tags move into `category` (Genre), `theme_context` (Theme) and `atmosphere`. Many tags are renamed, some merged, ~40 new tags added, and every dimension gets a new sort_order layout (one block of 100 per named sub-dimension). **Every existing film↔tag association must be preserved** (4048 films). The target layout below is the single source of truth — transcribe it exactly (names are case-sensitive and include slashes/apostrophes; escape single quotes in SQL as doubled quotes, e.g. `2000-2010''s`).

Deliverables:
1. `database/migrations/026_taxonomy_v2.sql` — the full migration, wrapped in BEGIN/COMMIT
2. `database/seed_taxonomy.sql` — rewritten to produce the final state on a fresh DB (motivation_relation and message_conveyed seed sections removed)
3. `database/verify_taxonomy_v2.sql` — verification queries (see Part 5)
4. `database/Tags and taxonomy sort order.txt` — replaced with the new layout

Do NOT drop the `motivation_relation` / `message_conveyed` / `film_motivation` / `film_message` tables — they must remain (empty) so the recommender/dashboard/games keep working until Step 22. Add a `-- DEPRECATED (emptied in migration 026, dropped in a later step)` comment on those tables in `schema.sql`.

### Part 1 — Same-dimension renames (UPDATE lookup name, associations preserved)

`theme_context`: class struggle → class/culture clash · organized fraud → trafficking/fraud · mourning → grief/mourning · nature → nature/wildlife · art: music → art: music/dance
`place_context`: country → rural
`character_context`: female → female lead · prostitute → sex worker · witch → witch/wizard · animal/wildlife → animal · evil → devil · android → android/robot
`cinema_type`: multi-sequence → chapters/multi-sequence · non linear narrative → flashback/non linear · dialogs → dialogs/punchline
`time_context`: early 21st → 2000-2010's · end 20th → 1980-90's · 20th post-war → 1950-60-70's · interwar → 1920-30's · early 20th → 1900-1910's

### Part 2 — Cross-dimension moves (junction data migrated)

Pattern for each moved tag (write it as explicit repeated SQL, or a temp mapping table + one PL/pgSQL DO loop per source→target pair — your choice, but the temp-table approach is preferred for readability given ~60 moves):
1. Insert the tag name into the target lookup table (with its final sort_order from Part 4) — `ON CONFLICT DO NOTHING`
2. `INSERT INTO <target_junction> (film_id, <target_fk>) SELECT jt.film_id, <target_id> FROM <source_junction> jt JOIN <source_lookup> ... WHERE name = '<tag>' ON CONFLICT DO NOTHING`
3. `DELETE FROM <source_lookup> WHERE name = '<tag>'` (FK cascade cleans the source junction)

Note for `category` inserts: `INSERT INTO category (category_name, sort_order)` leaves `historic_subcategory_name` NULL — all Genre tags (main + sub) are flat rows.

**themes → categories** (19): tragedy, psychological, war, crime, investigation, spy, heist, serial killer, survival, chase/escape, disaster, apocalypse, trial/judicial chronicle, prison, supernatural, whimsical/zany, dystopia, tales and legends, martial arts
**messages → categories** (4): parodic, satirical, absurdist, revisionist/alternate history
**messages → themes** (9): humanist, feminist, nostalgic, ecological, patriotic, anti establishment, traditionalist/way of life, philosophical, metaphysical
**messages → atmospheres** (2): symbolic, poetic
**cinema_types → categories** (10): black comedy, biopic, fait divers/true incident, western, peplum, swashbuckler, costume drama, wu xia pian, slasher, docufiction
**cinema_types → themes** (1): generational
**motivations → themes** (24): love, friendship, solidarity, communication, power, manipulation, sex, adultery, jealousy, perversion, rivalry, fight, rebellion/revolt, vengeance, harassment, obsession, greed/ambition, doubt/dilemma, lie, sacrifice, honor/duty, emancipation, redemption, invasion
**atmospheres → categories** (1): gore

**Merges** (two source tags → one target tag; both junction sets migrate to the same target row, ON CONFLICT deduplicates; then delete both source rows):
- themes `mafia` + themes `organized crime` → categories `mafia/organized crime`
- motivations `odyssey` + motivations `quest` → categories `odyssey/quest`
- messages `dreamlike` + messages `surreal` → atmospheres `dreamlike/surreal`
- messages `political` → themes `political` (target already exists — junction migrate + delete source only)

**Delete** (associations discarded): motivations `world-saving`.

After Part 2, `motivation_relation` and `message_conveyed` must contain 0 rows (all 27 motivations and all 18 messages are accounted for above). Assert this in the verification script.

### Part 3 — New tags (no film associations)

categories: melodrama, coming of age, slice of life, jumpscare, body horror, gothic horror, folk horror
themes: conspiracy, family/parenthood, loneliness, guilt, contest, exploration
time_context: single day, several years, decades-spanning
place_context: small town, planet, castle, hotel, car/bus, train, airplane
atmosphere: edge of your seat
character_context: male ensemble, chosen one, secret agent, warrior, knight
cinema_type: real time, timelapse, slow-motion, split screen, musical montage, monologue, fourth wall break

(Insert them with their final sort_order directly — Part 4.)

### Part 4 — Final sort_order layout (authoritative — rewrite ALL sort_orders per dimension)

One UPDATE per tag (or a VALUES-join bulk UPDATE per dimension). Blocks of 100 = one named sub-dimension; the tag order inside each block follows the new document exactly.

**category (Genre)**
- 100s Main: Drama 100, Comedy 101, Romance 102, Historical 103, Action 104, Adventure 105, Thriller 106, Science-Fiction 107, Fantasy 108, Horror 109, Musical 110, Documentary 111
- 200s Drama/Romance: melodrama 200, coming of age 201, slice of life 202, tragedy 203
- 300s Comedy: parodic 300, satirical 301, absurdist 302, black comedy 303
- 400s Thriller/Adventure: psychological 400, war 401, crime 402, investigation 403, spy 404, heist 405, mafia/organized crime 406, serial killer 407, survival 408, chase/escape 409, odyssey/quest 410, disaster 411, apocalypse 412
- 500s Historical/Justice: trial/judicial chronicle 500, prison 501, biopic 502, fait divers/true incident 503, western 504, peplum 505, swashbuckler 506, costume drama 507, wu xia pian 508, revisionist/alternate history 509
- 600s Sci-fi/Fantasy: supernatural 600, whimsical/zany 601, dystopia 602, tales and legends 603
- 700s Horror: jumpscare 700, slasher 701, gore 702, body horror 703, gothic horror 704, folk horror 705
- 800s Miscellaneous: docufiction 800, martial arts 801

**theme_context (Theme)**
- 100s Society & World: social 100, societal 101, generational 102, political 103, religion 104, business 105, journalism/media 106, censorship 107, conspiracy 108, sect 109, immigration 110, colonialism 111, slavery 112, nature/wildlife 113, AI/technology 114
- 200s Values & Reflection: humanist 200, feminist 201, nostalgic 202, ecological 203, patriotic 204, anti establishment 205, traditionalist/way of life 206, philosophical 207, metaphysical 208
- 300s Bonds & attachments: love 300, friendship 301, solidarity 302, communication 303, family/parenthood 304
- 400s Desire & transgression: power 400, manipulation 401, sex 402, adultery 403, jealousy 404, perversion 405
- 500s Interpersonal conflict: class/culture clash 500, rivalry 501, fight 502, rebellion/revolt 503, vengeance 504, harassment 505
- 600s Crime & abuse of power: delinquency 600, police violence 601, sex crime 602, kidnapping/hostage 603, trafficking/fraud 604, corruption 605, terrorism 606
- 700s Wounds & burdens: trauma/accident 700, identity crisis 701, illness 702, amnesia 703, death 704, grief/mourning 705, addiction/drugs 706, loneliness 707, guilt 708
- 800s Drives & arcs: obsession 800, greed/ambition 801, doubt/dilemma 802, lie 803, sacrifice 804, honor/duty 805, emancipation 806, redemption 807, transformation 808, time passing 809, dream 810
- 900s Art: art 900, art: music/dance 901, art: cinema 902, art: literature 903, art: fashion 904, art: painting 905, art: sculpture 906, art: theatre 907, art: radio 908, art: architecture 909
- 1000s Sport: sport 1000, sport: individual 1001, sport: collective 1002, sport: tournament 1003, sport: motor 1004
- 1100s Entertainment: food/cooking 1100, party 1101, game 1102, gambling 1103, contest 1104
- 1200s Face to the unknown: sorcery 1200, alien contact 1201, paranormal 1202, curse 1203, time travel/loop 1204, virtual/parallel universe 1205, invasion 1206, exploration 1207

**time_context (Time Period)**
- 1–15 Chronological: future 1, contemporary 2, 2000-2010's 3, 1980-90's 4, 1950-60-70's 5, WW2 6, 1920-30's 7, WW1 8, 1900-1910's 9, 19th 10, modern age 11, medieval 12, antiquity 13, prehistoric 14, undetermined 15
- 100s Time span: single day 100, several years 101, decades-spanning 102
- 200s Seasons: spring 200, summer 201, autumn 202, winter 203

**place_context (Place)**
- 100s Environments: urban 100, small town 101, rural 102, forest 103, mountains 104, desert 105, beach 106, maritime 107, island 108, underground 109, space 110, planet 111
- 200s Buildings & institutions: building 200, household/house/apartment 201, company/factory 202, school/university 203, hospital 204, jail 205, military 206, naval 207, castle 208, hotel 209
- 300s Narrative settings: road movie 300, huis clos/confined setting 301
- 400s Vehicles: car/bus 400, train 401, airplane 402, ship 403
- 500: no particular 500

**atmosphere (Atmosphere)**
- 100s Light/Joyful: family-friendly 100, feel good 101, crazy/nutty 102, delicate/intimate 103
- 200s Dark/Extreme: depressive/sad 200, violent 201, disturbing 202, steamy 203, sordid 204
- 300s Pace, Tension & Scale: epic 300, edge of your seat 301, mysterious 302, oppressive 303, claustrophobic 304, contemplative/meditative 305
- 400s Artistic Directing: cityscape 400, pastoral 401, gritty/realistic 402, meticulous 403, hypnotic/immersive 404, psychedelic 405, ethereal 406, symbolic 407, dreamlike/surreal 408, poetic 409

**character_context (Character)**
- 100s Group structure: solitary 100, tandem 101, trio 102, couple 103, relatives 104, generations 105, buddies 106, team/group/gang 107, ensemble cast 108
- 200s Age & identity: childhood 200, teenager 201, elderly 202, adult/child 203, female lead 204, male ensemble 205, LGBT 206, interracial 207
- 300s Social status & traits: ordinary 300, poor/marginal 301, wealthy 302, genius 303, simpleton/fool 304, loser 305, star/celebrity 306, disturbed/madness 307, disabled 308, outcast/misfit 309, sex worker 310, psychopath 311
- 400s Narrative devices: double 400, cross-dressing 401, unreliable narrator 402
- 500s Archetypes — human: super hero 500, chosen one 501, antihero 502, scientist/researcher 503, mentor 504, cop 505, detective 506, secret agent 507, vigilante 508, gangster 509, soldier 510, warrior 511, knight 512, samurai 513, pirate 514, viking 515, witch/wizard 516, femme fatale 517
- 600s Non-human & creatures: animal 600, monster/terrestrial creature 601, devil 602, ghost/spirit 603, vampire 604, zombie 605, alien 606, android/robot 607, vehicle 608

**cinema_type (Cinema Type)**
- 100s Visual techniques: animation 100, mixed animation 101, CGI 102, 3D 103, motion capture 104, black and white 105, aesthetics 106, found footage 107, dogma 108
- 200s Industry & culture: blockbuster 200, art house 201, B 202, franchise 203, popular culture 204
- 300s Sequencing: chapters/multi-sequence 300, flashback/non linear 301, real time 302, timelapse 303, slow-motion 304, sequence-shot 305, split screen 306, musical montage 307
- 400s Voice & Dialogue: dialogs/punchline 400, slang dialogs 401, few/no dialogs 402, voiceover 403, monologue 404, fourth wall break 405
- 500s Movements & eras: silent 500, expressionism 501, realism 502, neo-realism 503, noir 504, hollywood golden age 505, new hollywood 506, new wave 507, slow cinema 508, neo-noir 509, blaxploitation 510, giallo 511

### Part 4b — tag_description table

In the same migration:
- For every rename in Part 1: `UPDATE tag_description SET tag_name = <new> WHERE tag_name = <old>` (scoped to the right dimension key).
- For every move in Part 2: `UPDATE tag_description SET dimension = <target key> WHERE dimension = <source key> AND tag_name = <tag>`.
- Delete rows for: world-saving, mafia, organized crime, odyssey, quest, dreamlike, surreal, and any remaining rows with dimension = motivations/messages keys.
Check `018_tag_descriptions.sql` first for the exact dimension key strings used (`themes`, `categories`, etc.) and use those.

### Part 5 — Verification (`database/verify_taxonomy_v2.sql`)

- Per-dimension listing: `SELECT name, sort_order FROM <lookup> ORDER BY sort_order` — must match Part 4 exactly (tag counts: category 62, theme 96, time_context 22, place_context 29, atmosphere 25, character_context 48, cinema_type 40 — recompute these from Part 4 while writing and correct if off).
- `SELECT COUNT(*) FROM motivation_relation` = 0; same for message_conveyed, film_motivation, film_message.
- No orphan junction rows; no duplicate names per lookup.
- Association preservation spot-checks: 2001: A Space Odyssey now has category `odyssey/quest` and themes `philosophical`/`metaphysical`; Mulholland Drive has atmosphere `dreamlike/surreal`, category `mafia/organized crime`, and themes love/obsession/jealousy/manipulation/lie/sex/adultery/vengeance; La Haine has themes friendship/solidarity/rebellion/revolt/vengeance/fight/political/humanist and category `tragedy` (its old theme `tragedy` moved to Genre).
- Global sanity: total distinct (film, tag-name) pairs across all 7 dimensions after ≥ (pairs across 9 dimensions before) − (world-saving count) − (merge-overlap dedups). Print before/after counts at the top and bottom of the migration using RAISE NOTICE or plain SELECTs.

### Part 6 — seed_taxonomy.sql rewrite

Rewrite the category, cinema_type, place_context, time_context, theme_context, character_context and atmosphere INSERT sections to match Part 4 exactly. Delete the motivation_relation and message_conveyed sections. Leave person_job, stream_platform and language sections untouched.

### Execution & validation

- Run `026_taxonomy_v2.sql` against the LOCAL database only (psql). Do NOT touch Supabase — Martin syncs manually after 21b/21c.
- Run `verify_taxonomy_v2.sql` and report results.
- Update `database/Tags and taxonomy sort order.txt` with the new layout.

### Success criteria

- Migration runs in one transaction with no errors on the local DB
- All verification checks pass; motivation/message tables empty but present
- A film that had `war` as a theme now has `war` as a genre (same film_id set)
- Re-running seed_taxonomy.sql on the migrated DB is a no-op (idempotent)

---

## Step 21b Prompt — Taxonomy v2: Backend

Prerequisite: Step 21a migration applied to the local DB.

Read CLAUDE.md, then PLAN.md (Step 21), then these files:
- `database/seed_taxonomy.sql` (NEW taxonomy — source of truth for names/sort_orders)
- `backend/app/services/taxonomy_config.py` (full rewrite target)
- `backend/app/services/claude_enricher.py`
- `backend/app/routers/taxonomy.py`
- `backend/app/routers/films.py`
- `backend/app/routers/add_film.py` (context only — should need no changes)
- `backend/app/schemas/film.py`
- `backend/app/tier_config.py`
- `scripts/review_tag.py`
- `database/tags_definition.md`

### Part 1 — taxonomy_config.py (rewrite)

- `VALID_GENRES_MAIN` (the 12 mains) and `VALID_GENRES_SUB` (all sub-genre tags), plus `VALID_CATEGORIES = VALID_GENRES_MAIN + VALID_GENRES_SUB` for validation.
- Rewrite `VALID_CINEMA_TYPES`, `VALID_PLACE_ENVIRONMENTS`, `VALID_TIME_CONTEXTS`, `VALID_THEMES`, `VALID_CHARACTERS`, `VALID_ATMOSPHERES` to match seed_taxonomy.sql exactly (same order, group comments per sub-dimension).
- Delete `VALID_MOTIVATIONS` and `VALID_MESSAGES`.
- `TAXONOMY_DIMENSIONS`: 7 keys only (categories, cinema_type, time_context, place_environment, themes, character_context, atmosphere).
- Rewrite `REFERENCE_EXAMPLES` (2001, La Haine, Mulholland Drive) under the new taxonomy: apply the rename/move/merge mapping mechanically to their old tags (e.g. 2001: categories gain `odyssey/quest`; motivations/message keys removed; `philosophical`, `metaphysical` become themes; `symbolic`, `surreal`→`dreamlike/surreal` become atmospheres; Mulholland Drive `non linear narrative`→`flashback/non linear`, `female`→`female lead`, `mafia`→category `mafia/organized crime`, `early 21st`→`2000-2010's`; La Haine `end 20th`→`1980-90's`, motivations→themes, `political`/`humanist`/`philosophical`→themes, `tragedy`→category). Drop the `motivations`/`message` keys from enrichment dicts and confidence dicts.

### Part 2 — claude_enricher.py

- Remove `motivations` and `message` everywhere: output-format JSON, confidence block, `list_dims` in `_validate_enrichment`, `_empty_enrichment`, prompt sections.
- Genre section of the prompt: explain main genres vs sub-genres — require at least ONE main genre; sub-genres only when clearly defining.
- Time Context section: add the year-range table verbatim: future 2030 onward · contemporary 2020–2029 · 2000-2010's 2000–2019 · 1980-90's 1980–1999 · 1950-60-70's 1946–1979 · WW2 1939–1945 · 1920-30's 1919–1938 · WW1 1914–1918 · 1900-1910's 1900–1913 · 19th 1800–1899 · modern age 1500–1799 · medieval 500–1500 · antiquity 3000 BC–500 AD · prehistoric before recorded civilization · undetermined no identifiable period. Also mention the Time span tags (single day / several years / decades-spanning) and Seasons.
- Update the docstring/system prompt mentions of dissolved dimensions.

### Part 3 — routers/taxonomy.py

- Remove `messages` and `motivations` entries from `DIMENSION_MAP`, `SORTED_DIMENSIONS`, `MANAGEABLE_DIMENSIONS`, `FREQ_DIMENSIONS`.
- Leave the hierarchical/categories special handling as is (harmless with NULL subcategories; `themes` still uses "art: X" / "sport: X" parent counting).

### Part 4 — routers/films.py

- Remove `messages*` and `motivations*` query params, their tier-clearing branches, their tuples in `_taxonomy_filters` / `_taxonomy_dim_names`, and their entries in `dim_sort_table_map`.
- Remove the motivations/messages queries from the film-detail `asyncio.gather` and the corresponding `FilmDetail(...)` fields.
- List endpoint: change the category batch-load WHERE clause from `historic_subcategory_name IS NULL` to `c.sort_order < 200` (main genres only on cards). Same fix in `/api/stats` `top_categories`.
- `create_film` / `update_film`: remove the motivations/message junction tuples.

### Part 5 — schemas/film.py + tier_config.py + review_tag.py

- `FilmDetail`, `FilmUpdate`: drop `motivations` and `messages` fields.
- `tier_config.py`: remove motivations/messages from all dicts. First calibration for the new blocks (Martin will adjust values later — implement exactly these for now):
  - anonymous: dimensions {categories, time_periods, atmospheres}; max sort_order: categories 199, time_periods 99, atmospheres 299
  - free: dimensions {categories, themes, time_periods, place_contexts, atmospheres, characters, cinema_types}; max sort_order: themes 699, atmospheres 299, place_contexts 299, characters 399, cinema_types 199 (categories and time_periods unrestricted)
  - pro/admin: all 7 dims + studios, no sort limits
  - films.py `dim_sort_table_map` must include `categories: ("category", "category_name")` and `time_periods: ("time_context", "time_period")` so the anonymous caps are enforced server-side (extend the per-dimension sort_order filtering loop accordingly).
- `scripts/review_tag.py`: remove messages/motivations from its `DIMENSION_MAP`.

### Part 6 — tags_definition.md (mechanical pass)

Apply renames to tag headings, move sections of relocated tags under their new dimension heading, delete world-saving and the merged source names (add stub headings for mafia/organized crime, odyssey/quest, dreamlike/surreal that keep the better of the two old definitions). Flag anything ambiguous with `<!-- TODO Martin -->` instead of guessing.

### Success criteria

- `uvicorn` starts; `GET /api/taxonomy/themes` returns the new tags in the new order; `/api/taxonomy/messages` returns 400
- `GET /api/films?themes=love` returns films (migrated from motivations); `?motivations=...` is rejected as unknown param (FastAPI ignores it — acceptable) without 500
- `GET /api/films/{id}` has no motivations/messages keys; categories include sub-genres; list cards show main genres only
- Anonymous request with `categories=melodrama` returns unfiltered-by-that-tag results (sort_order cap enforced)
- `/api/films/{id}/similar`, `/api/stats/dashboard`, and the 3 game setup endpoints still respond without 500 (degraded data is OK — do NOT modify recommender.py, stats.py, game.py)

---

## Step 21c Prompt — Taxonomy v2: Frontend

Prerequisite: Steps 21a + 21b done, backend running locally on the migrated DB.

Read CLAUDE.md, then PLAN.md (Step 21), then these files:
- `frontend/src/types/api.ts`
- `frontend/src/lib/utils.ts`, `frontend/src/lib/tierAccess.ts`
- `frontend/src/components/filters/FilterSection.tsx`, `FilterChip.tsx`, `ActiveFilters.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/hooks/useFilterState.ts`, `useTaxonomy.ts`
- `frontend/src/pages/FilmDetailPage.tsx`, `frontend/src/pages/AddFilmPage.tsx`, `frontend/src/pages/TaxonomyAdminPage.tsx`
- `frontend/src/components/films/EditableTagSection.tsx`, `FilmCard.tsx`
- `frontend/src/api/client.ts` (check for any explicit motivations/messages references)

### Part 1 — types/api.ts

- `TAXONOMY_DIMENSIONS` → `["categories", "themes", "time_periods", "place_contexts", "atmospheres", "characters", "cinema_types"]` (this is the new sidebar display order).
- `ARRAY_FILTER_KEYS` → same 7 + `"studios"`.
- Remove `motivations`/`messages` from `FilterState`, `DEFAULT_FILTER_STATE`, and the `FilmDetail` interface.

### Part 2 — New `frontend/src/lib/taxonomyGroups.ts`

Export:
- `MAIN_GENRES: string[]` — the 12 main genre names.
- `TAXONOMY_GROUPS: Record<string, { block: number; label: string; parent?: string }[]>` keyed by dimension. Blocks/labels (block = sort_order block number, i.e. `Math.floor(sort_order/100)`):
  - categories: 1 Main · 2 Drama / Romance · 3 Comedy · 4 Thriller / Adventure · 5 Historical / Justice · 6 Sci-fi / Fantasy · 7 Horror · 8 Miscellaneous (blocks 2–8 have parent "Sub-genres")
  - themes: 1 Society & World · 2 Values & Reflection · 3 Bonds & attachments (parent "Human Relations") · 4 Desire & transgression (HR) · 5 Interpersonal conflict (HR) · 6 Crime & abuse of power (HR) · 7 Wounds & burdens (parent "Personal / Inner conflict") · 8 Drives & arcs (PIC) · 9 Art (parent "Art, Sport & Entertainment") · 10 Sport (ASE) · 11 Entertainment (ASE) · 12 Face to the unknown
  - time_periods: 0 Chronological · 1 Time span · 2 Seasons
  - place_contexts: 1 Environments · 2 Buildings & institutions · 3 Narrative settings · 4 Vehicles · 5 (empty label — "no particular")
  - atmospheres: 1 Light / Joyful · 2 Dark / Extreme · 3 Pace, Tension & Scale · 4 Artistic Directing
  - characters: 1 Group structure · 2 Age & identity · 3 Social status & traits · 4 Narrative devices · 5 Archetypes — human · 6 Non-human & creatures
  - cinema_types: 1 Visual techniques · 2 Industry & culture · 3 Sequencing (parent "Narrative techniques") · 4 Voice & Dialogue (NT) · 5 Movements & eras

### Part 3 — FilterSection.tsx group headers

Replace the bare `<Separator>` at block boundaries with a group header: when `Math.floor(sort_order/100)` changes, render a full-width label row — parent label (if any and different from the previous block's parent) as a tiny uppercase muted line, then the block label as a small semibold muted line — looked up from `TAXONOMY_GROUPS[dimension]`. Blocks without a label entry fall back to the current plain separator. Keep chips, lock logic and tooltips unchanged. The first block's label also renders (including "Main" for Genre and "Chronological" for Time Period).

### Part 4 — Labels + tiers

- `dimensionLabel` in utils.ts → singular: categories "Genre", themes "Theme", time_periods "Time Period", place_contexts "Place", atmospheres "Atmosphere", characters "Character", cinema_types "Cinema Type" (studios unchanged). Remove motivations/messages entries.
- `tierAccess.ts`: mirror the new backend tier_config exactly (see Step 21b Part 5), including `categories: 199` and `time_periods: 99` caps for anonymous — which means `dimensionSortOrderMax` now applies to categories/time_periods too.

### Part 5 — FilmDetailPage.tsx

- Hero + mobile hero genre badges: show only `film.categories.filter(c => MAIN_GENRES.includes(c))`.
- Taxonomy section: remove the motivations and messages `EditableTagSection`s; new layout — row 1: time_periods / place_contexts / geography (unchanged); then categories (full width, all genres incl. sub-genres); then a 2-col grid: themes + atmospheres, characters + cinema_types.
- Anonymous teaser: "4 more dimensions" listing themes, atmospheres, characters, cinema_types.

### Part 6 — AddFilmPage.tsx

- Remove the Motivations and Messages `InlineTagEditor`s and their local state; stop writing `motivations`/`message` keys into `updatedEnrichment`.
- Relabel editors with the new singular names ("Genre", "Cinema Type", "Theme", "Character", "Atmosphere", "Time Period", "Place").

### Part 7 — Sweep

- `client.ts`, `ActiveFilters.tsx`, `useFilterState.ts`, `TaxonomyAdminPage.tsx`, `EditableTagSection.tsx`, `TagReviewPanel.tsx`: these are mostly generic over `ARRAY_FILTER_KEYS`/`TAXONOMY_DIMENSIONS` — verify with a project-wide grep for `motivations` and `messages` and remove any remaining explicit references OUTSIDE `components/game/`, `components/stats/`, `SimilarFilmsCarousel.tsx` and `hooks/useDashboardStats.ts` (those are Step 22 — leave them compiling as-is; if a type removal breaks them, keep a minimal local type shim rather than refactoring them).

### Success criteria

- Sidebar shows 7 dimensions in the new order, each with named sub-dimension group headers in the exact document order
- Genre section shows Main first, then labeled sub-genre groups; anonymous users see sub-genres locked
- Filtering by a migrated tag (e.g. Theme: love, Genre: war) returns films
- Film page taxonomy shows 7 dimensions; hero shows main genres only
- Add Film flow: enrichment returns 7 dimensions, review screen shows/edits them, save works end-to-end
- Manage tags page lists the 7 dimensions with correct ordering
- `npm run build` passes; games/dashboard pages still load (degraded data acceptable)
