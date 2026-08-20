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
- 1–15 Years & eras: future 1, contemporary 2, 2000-2010's 3, 1980-90's 4, 1950-60-70's 5, WW2 6, 1920-30's 7, WW1 8, 1900-1910's 9, 19th 10, modern age 11, medieval 12, antiquity 13, prehistoric 14, undetermined 15
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
- 300s Social status: ordinary 300, poor/marginal 301, wealthy 302, star/celebrity 303, sex worker 304, outcast/misfit 305
- 400s Traits & conditions: genius 400, simpleton/fool 401, loser 402, disabled 403, disturbed/madness 404, psychopath 405
- 500s Narrative devices: double 500, cross-dressing 501, unreliable narrator 502
- 600s Archetypes — human > Figures & roles: super hero 600, chosen one 601, antihero 602, mentor 603, scientist/researcher 604, witch/wizard 605, femme fatale 606
- 700s Archetypes — human > Law & crime: cop 700, detective 701, secret agent 702, vigilante 703, gangster 704
- 800s Archetypes — human > Fighters: soldier 800, warrior 801, knight 802, samurai 803, pirate 804, viking 805
- 900s Non-human & creatures: animal 900, monster/terrestrial creature 901, devil 902, ghost/spirit 903, vampire 904, zombie 905, alien 906, android/robot 907, vehicle 908

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
  - time_periods: 0 Years & eras · 1 Time span · 2 Seasons
  - place_contexts: 1 Environments · 2 Buildings & institutions · 3 Narrative settings · 4 Vehicles · 5 (empty label — "no particular")
  - atmospheres: 1 Light / Joyful · 2 Dark / Extreme · 3 Pace, Tension & Scale · 4 Artistic Directing
  - characters: 1 Group structure · 2 Age & identity · 3 Social status · 4 Traits & conditions · 5 Narrative devices · 6 Figures & roles (parent "Archetypes — human") · 7 Law & crime (A—h) · 8 Fighters (A—h) · 9 Non-human & creatures
  - cinema_types: 1 Visual techniques · 2 Industry & culture · 3 Sequencing (parent "Narrative techniques") · 4 Voice & Dialogue (NT) · 5 Movements & eras

### Part 3 — FilterSection.tsx group headers

Replace the bare `<Separator>` at block boundaries with a group header: when `Math.floor(sort_order/100)` changes, render a full-width label row — parent label (if any and different from the previous block's parent) as a tiny uppercase muted line, then the block label as a small semibold muted line — looked up from `TAXONOMY_GROUPS[dimension]`. Blocks without a label entry fall back to the current plain separator. Keep chips, lock logic and tooltips unchanged. The first block's label also renders (including "Main" for Genre and "Years & eras" for Time Period).

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

---

## Step 22 Prompt — Taxonomy v2: Deferred Surfaces

Prerequisite: Steps 21a–21c done, local DB migrated.

Rewire the four surfaces Step 21 deferred, then drop the dissolved tables.

- **22a `services/recommender.py`** — 7 dimensions in `_DIM_SQL`; rebalance
  `DIMENSION_WEIGHTS` for what each dimension now holds; replace the hardcoded
  `phase1[:9]` / `phase3[11]` gather-unpacking indices with `len(_DIM_KEYS)`;
  similar-film cards restrict genres to `sort_order < 200`.
- **22b `routers/stats.py` + `components/stats/`** — replace the two message
  views with the *Values & Reflection* theme block (`sort_order` 200–299); add a
  sub-genre × decade view; prune `CINEMA_MOVEMENT_NAMES` of the tags that moved
  to Genre; restrict every genre-keyed query to `sort_order < 200`; replace
  `PersonTagsResponse.top_messages` with `top_genres` + `top_cinema_types`.
- **22c `routers/game.py` + `components/game/`** — 7 dimensions in
  `DIMENSION_TABLE_MAP` / `_GUESS_DIM_LABELS`; order film tags by `sort_order`;
  delete the duplicated group-label maps in `dimensions.ts` and delegate to
  `lib/taxonomyGroups.ts`.
- **22d** — `database/migrations/027_drop_dissolved_taxonomy.sql` guarded on the
  four tables being empty; purge them from `schema.sql`, the models and every
  script; re-tag `reference_films_fallback.json` from `REFERENCE_EXAMPLES`.

See PLAN.md Step 22 for the applied outcome.
- `npm run build` passes; games/dashboard pages still load (degraded data acceptable)

---

## Step 23 Prompt — Enrichment Pipeline Hardening + Prompt Caching

Read `CLAUDE.md`, then `PLAN.md` (Step 23), then these files:
- `backend/app/services/claude_enricher.py` (main target)
- `backend/app/services/taxonomy_config.py` (context — do NOT change any tag list)
- `backend/app/services/tmdb_service.py` (`GENRE_TO_CATEGORY`, `map_tmdb_genre_to_category`)
- `backend/app/services/tmdb_mapper.py` (`_map_genres`, `map_film_to_db`)
- `backend/app/routers/add_film.py`
- `backend/app/routers/films.py` (`create_film` and `update_film` — compare their colour handling)
- `backend/app/schemas/add_film.py`
- `frontend/src/pages/AddFilmPage.tsx` (`ReviewScreen.handleSave`)
- `scripts/claude_enrichment_runner.py`, `scripts/claude_batch_enrichment.py`

**This step changes NO taxonomy.** Do not add, rename, remove or reorder a single
tag, and do not touch `seed_taxonomy.sql` or any migration. If something looks
like it needs a taxonomy change, stop and report instead.

---

### Part A — Restructure the prompt for caching (`claude_enricher.py`)

Today `_build_user_prompt()` returns one big string, rebuilt per call (and again
on every JSON-retry), with `## Film Metadata` at the top and ~15k tokens of
constant content after it. Restructure into a constant prefix + per-film suffix.

1. **Build the static prefix once.** In `__init__`, after `self.tag_definitions`
   is loaded, set `self._static_prefix = self._build_static_prefix()`. That
   method returns, in order: the existing `_build_taxonomy_section()` output
   (dimension lists + Source + Awards + the Tag Usage Guide), then
   `_build_examples_section()`, then the `## Output Format` JSON skeleton.
   Nothing film-specific may appear in it.

2. **`_build_film_block(tmdb_mapped_data)`** returns only the `## Film Metadata`
   section (same fields as now) followed by a short closing instruction, e.g.
   *"Classify the film above using the taxonomy and definitions provided.
   Respond with ONLY the JSON object described in the Output Format section."*

3. **Assemble with cache breakpoints** in `enrich_film`:

   ```python
   system=[{
       "type": "text",
       "text": ENRICHMENT_SYSTEM_PROMPT,
       "cache_control": {"type": "ephemeral"},
   }],
   messages=[{"role": "user", "content": [
       {"type": "text", "text": self._static_prefix,
        "cache_control": {"type": "ephemeral"}},
       {"type": "text", "text": film_block},
   ]}],
   ```

   Two breakpoints only (the API allows four). The film block must be **last**
   and must NOT be cached.

4. **Retry path must not break the cache.** The JSON-parse retry currently
   rebuilds the whole prompt and appends a stricter instruction. Change it to
   rebuild **only the film block** and append the stricter wording there, so the
   two cached blocks stay byte-identical across retries.

5. **Log cache usage** on every call, next to the existing `output_tokens` log:
   `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`
   (read them defensively with `getattr(response.usage, ..., 0)` — they may be
   absent on older SDK versions).

Keep `_build_user_prompt` as a thin wrapper (`prefix + "\n\n" + film_block`) if
anything else calls it — grep first; `scripts/claude_batch_enrichment.py` and
`scripts/test_enrichment_pipeline.py` are the likely callers. If the batch script
builds its own request bodies, give it the same two-breakpoint structure, since
caching stacks with the Batch API discount and that is the path Step 25 will use.

---

### Part B — Model default

Replace the hardcoded `model: str = "claude-sonnet-4-6"` default with a module
constant read from the environment:

```python
DEFAULT_ENRICHMENT_MODEL = os.getenv("CLAUDE_ENRICHMENT_MODEL", "claude-sonnet-5")
```

Sonnet 5 is both cheaper ($2/$10 vs $3/$15 per MTok) and stronger than Sonnet 4.6.
**Verify the exact model string against the installed `anthropic` SDK or the API
docs before committing it** — if `claude-sonnet-5` is rejected, report the error
rather than silently falling back. Add `CLAUDE_ENRICHMENT_MODEL` to `.env.example`
with a comment listing the alternatives (`claude-haiku-4-5-20251001` for cheap
bulk passes).

---

### Part C — Prompt dedup and confidence calibration

In `ENRICHMENT_SYSTEM_PROMPT`:

1. **Delete the "Awards rules" block** — fully duplicated by the
   `### Awards & Nominations` section, which also carries the festival list.
2. **Delete the "Source rules" block** — duplicated by `### Source / Origin`,
   which also carries the valid type list.
3. **Trim the `[NEW]` sentence** to a short cross-reference; the taxonomy section
   header already states the rule.
4. **Delete `"Do not force tags. An empty list is better than a wrong tag."`**
   The measured failure mode on the bulk import is under-tagging, and per-tag
   restraint is now enforced much more precisely by `tags_definition.md`.
   Replace with a scoped version, e.g. *"Geography, Source and Awards may
   legitimately be empty when the metadata does not support them. The tag
   dimensions should not be — apply every tag whose definition the film
   satisfies."*
   Keep `"Be comprehensive: assign ALL relevant values"` and keep the
   "DEFINING or SIGNIFICANT aspect" philosophy block — they now carry the
   balance on their own.
5. **Add a confidence calibration scale.** All three reference examples are
   canonical films scoring 0.85–0.95; with no other signal the model reproduces
   that band for obscure films, which makes
   `get_low_confidence_films(threshold=0.6)` inert. Do **not** falsify the
   example values — they are honest. Instead add explicit bands:

   ```
   Confidence calibration — these scores drive human review, so spread them:
   - 0.9-1.0: you know this film well; the classification is unambiguous.
   - 0.7-0.9: confident, but working partly from metadata rather than the film.
   - 0.5-0.7: plausible inference from the overview/keywords alone.
   - below 0.5: guessing; the film is obscure or the metadata is too thin.
   The reference examples below are famous films and score high for that reason.
   Do not treat their scores as a default.
   ```

Do not alter the dimension lists, the Genre main/sub rules, or the Time Context
year-range table.

---

### Part D1 — Genre edits are silently discarded (frontend)

In `AddFilmPage.tsx`, `ReviewScreen.handleSave` builds `updatedEnrichment` with
six dimensions but omits `categories`, sending edited genres to
`preview.categories` instead. `create_film` reads genres **only** from
`enrichment["categories"]`, so genre edits never reach the database, and when
`enrichment_failed` is true (`enrichment` is `{}`) a film is saved with **no
genres at all**.

Fix in the frontend: add `categories` to `updatedEnrichment` alongside the other
six. Keep `preview.categories` in sync too (it is part of `EnrichmentPreview`).
Do not change `create_film`'s read path — one source (`enrichment`) is correct.

Verify by adding and removing a genre on the review screen and confirming
`film_genre` matches after save.

---

### Part D2 — New B&W films saved as colour (backend)

`update_film` already syncs `film.color` from the `black and white` cinema_type
tag; `create_film` does not, and `TMDBMapper` always emits `color: True`.
Migration `019_backfill_color_flag.sql` fixed the historical rows but is a
one-shot, so every film added since is wrong again.

In `create_film`, after the taxonomy junctions are inserted, mirror
`update_film`'s logic: if the enrichment's `cinema_type` list contains
`black and white`, `UPDATE film SET color = FALSE WHERE film_id = :fid`.
Place it after the junction loop so it reflects the final saved tags, and add a
comment pointing at `update_film` as the sibling implementation.

---

### Part D3 — Remove `historic_subcategories`

Produced by `tmdb_mapper`, carried through `EnrichmentPreview` and merged in
`add_film.py`, then **ignored by `create_film`**. Dead since the v2 migration
made all genre rows flat (`historic_subcategory_name IS NULL`).

Remove the field from `schemas/add_film.py`, `add_film.py`, `tmdb_mapper.py` and
`frontend/src/types/api.ts`. Grep for `historic_subcategor` across the repo
afterwards. **Leave the `category.historic_subcategory_name` column and the
`IS NULL` guards in `create_film` / `update_film` alone** — the column still
exists and those guards are correct.

---

### Part E — Wire up the unused TMDB genre mapping

`TMDBService.map_tmdb_genre_to_category` returns a `note`
(War→`war`, Crime→`crime`, Mystery→`investigation`, Animation→`animation`,
Documentary→`documentary`) and a `subcategory` (Western→`western`), and nothing
consumes either. Under v2 those are real tags: `war`, `crime`, `investigation`,
`western` are Genre sub-genres, `animation` is a Cinema Type.

Read `_map_genres` in `tmdb_mapper.py` first, then:

- Route genre-valued notes and the Western subcategory into the mapper's
  `categories` list (deduplicated, main genres first).
- Route `animation` into a new `cinema_types` list on the mapper output.
- Drop the `documentary` note — `Documentary` is already a main genre via
  `GENRE_TO_CATEGORY`, so it would duplicate.
- Surface `cinema_types` through `EnrichmentPreview` and merge it in
  `add_film.py` with the **same precedence rule already used for categories**:
  Claude's list wins when non-empty, TMDB's is the fallback.

This matters most on the `enrichment_failed` path, which currently leaves the
review screen with no cinema types and (per D1) no genres either.

Validate the seeded names against `taxonomy_config.VALID_CATEGORIES` /
`VALID_CINEMA_TYPES` at module import and log a warning on mismatch, so a future
taxonomy edit can't silently reintroduce a dead mapping.

---

### Part F — Cost instrumentation

In `scripts/claude_enrichment_runner.py`, the pricing constants are stale
("Sonnet 4", $3/$15). Replace with a per-model table covering Sonnet 5 ($2/$10),
Haiku 4.5 ($1/$5) and Opus 5 ($5/$25), plus cache-read (0.1× input) and
5-minute cache-write (1.25× input) rates, and make the cost estimator read the
actual `cache_read_input_tokens` / `cache_creation_input_tokens` returned by the
API instead of assuming every input token is billed at full rate. Print a
running total and a cache hit-rate percentage in the progress output.

Add a `# Rates verified 2026-08-14` comment — these change.

---

### Verification

1. **Cache proof.** Enrich two different films in one process (a small script or
   `test_enrichment_pipeline.py`) and show the logged usage: call 1 should report
   a large `cache_creation_input_tokens`, call 2 a large `cache_read_input_tokens`
   (~15k) and a small `input_tokens`. Report the actual numbers — this is the
   headline result of the step.
2. **Prompt integrity.** Print the assembled prefix once and confirm the
   dimension lists, Genre rules, year-range table and tag guide are all still
   present and unchanged, and that nothing film-specific leaked into it.
3. **Add Film end to end** (local, admin): add a B&W film (e.g. a Bergman or
   Kurosawa title), edit one genre on the review screen, save. Confirm the edited
   genre is in `film_genre` and `film.color = FALSE`.
4. **Failure path.** Temporarily force `enrich_film` to raise, add a TMDB
   Animation or Western film, and confirm the review screen still shows seeded
   genres and `animation`, and that saving writes them.
5. `grep -rn "historic_subcategor" backend frontend scripts` returns only the
   `category` column references in `films.py` and `schema.sql`.
6. Backend boots; `npm run build` and `tsc --noEmit` pass.

Report the measured before/after cost per film. Do **not** run any bulk
re-enrichment — that is Step 24/25 and needs Martin's merge-policy decision first.

---

## Step 24 Prompt — Tag Weighting Foundation + Re-tag Harness

Read `CLAUDE.md`, then `PLAN.md` (Steps 24 and 25 — the decision record matters,
not just the scope list), then:
- `backend/app/services/claude_enricher.py`
- `backend/app/services/taxonomy_config.py` (context — change no tag list)
- `backend/app/services/tmdb_service.py`, `tmdb_mapper.py`
- `backend/app/routers/films.py` (`create_film` / `update_film` junction loops)
- `database/schema.sql` (junction tables)
- `scripts/claude_enrichment_runner.py` (`MODEL_PRICES`, cost estimator)
- `scripts/claude_batch_enrichment.py` (**to be deleted** — read for its Batch
  submit/status/collect plumbing before removing it)
- `frontend/src/lib/taxonomyGroups.ts` (block layout — note `time_periods`
  block 0 is **"Years & eras"**)

**This step changes NO taxonomy and runs NO production enrichment.** It builds
the machinery Step 25 executes.

---

### Part A — Migration 029: the `weight` column

`database/migrations/029_tag_weight.sql`, one transaction.

Add `weight smallint` to all seven tag junctions:

| junction | lookup | fk | name column |
|---|---|---|---|
| `film_genre` | `category` | `category_id` | `category_name` |
| `film_theme` | `theme_context` | `theme_context_id` | `theme_name` |
| `film_technique` | `cinema_type` | `cinema_type_id` | `technique_name` |
| `film_character_context` | `character_context` | `character_context_id` | `context_name` |
| `film_atmosphere` | `atmosphere` | `atmosphere_id` | `atmosphere_name` |
| `film_period` | `time_context` | `time_context_id` | `time_period` |
| `film_place` | `place_context` | `place_context_id` | `environment` |

- `weight smallint NULL CHECK (weight IS NULL OR weight BETWEEN 1 AND 100)`
- NULL means "unscored legacy row" — do **not** backfill existing rows to a
  value. Everything before the re-tag is genuinely unscored, and a fake 50 would
  be indistinguishable from a real secondary later.
- Convention, documented in a comment on each column: **100 = defining,
  50 = secondary**. The range is wider than the two values in use so a third
  level or true percentages need no migration.
- One partial index per junction for the Step 26 "defining only" queries, e.g.
  `CREATE INDEX idx_film_theme_defining ON film_theme (theme_context_id) WHERE weight = 100;`

Mirror the columns into `database/schema.sql`. Apply to the **local DB only**.

---

### Part B — Enricher: the `defining` output key

**B1 — output format.** Add one key to `_build_output_format_section()`, after
`atmosphere` and before `source`:

```json
"defining": {
  "categories": ["..."],
  "cinema_type": ["..."],
  "time_context": ["..."],
  "place_environment": ["..."],
  "themes": ["..."],
  "character_context": ["..."],
  "atmosphere": ["..."]
}
```

Keep the flat tag lists exactly as they are. `defining` is a **subset** of them,
not a replacement — anything in a tag list but absent from `defining` is
secondary. This shape was chosen over per-tag objects because it costs far fewer
tokens and leaves `_validate_enrichment` almost untouched.

**B1b — the three reference examples must gain the key.** They are the few-shot
examples; if they lack `defining`, the model sees three complete outputs without
it and will omit it inconsistently. Add these to `taxonomy_config.REFERENCE_EXAMPLES`
**exactly as written** — they were hand-validated by Martin and are the
calibration standard for the entire run. Do not re-derive or "improve" them.

```python
# 2001 — 25 defining of 51 tags
"defining": {
    "categories": ["Science-Fiction"],
    "cinema_type": ["aesthetics", "art house", "chapters/multi-sequence",
                    "few/no dialogs", "slow cinema"],
    "time_context": ["future", "prehistoric"],
    "place_environment": ["space", "spaceship"],
    "themes": ["AI/technology", "philosophical", "metaphysical",
               "alien contact", "exploration", "transformation"],
    "character_context": ["solitary", "android/robot"],
    "atmosphere": ["contemplative/meditative", "epic", "mysterious",
                   "hypnotic/immersive", "psychedelic", "meticulous",
                   "symbolic"],
},

# La Haine — 25 defining of 46 tags
"defining": {
    "categories": ["Drama", "slice of life"],
    "cinema_type": ["black and white", "realism", "dialogs/punchline",
                    "slang dialogs"],
    "time_context": ["single day"],
    "place_environment": ["urban"],
    "themes": ["social", "societal", "political", "immigration",
               "class/culture clash", "police violence", "rebellion/revolt",
               "friendship"],
    "character_context": ["trio", "buddies", "teenager", "interracial",
                          "poor/marginal"],
    "atmosphere": ["violent", "oppressive", "gritty/realistic", "cityscape"],
},

# Mulholland Drive — 23 defining of 45 tags
"defining": {
    "categories": ["Drama", "psychological"],
    "cinema_type": ["aesthetics", "art house", "flashback/non linear",
                    "neo-noir"],
    "time_context": [],
    "place_environment": ["urban"],
    "themes": ["identity crisis", "amnesia", "dream", "art: cinema",
               "obsession", "greed/ambition"],
    "character_context": ["female lead", "tandem", "double",
                          "unreliable narrator", "disturbed/madness"],
    "atmosphere": ["dreamlike/surreal", "mysterious", "hypnotic/immersive",
                   "disturbing", "symbolic"],
},
```

Two patterns visible in those sets, worth preserving because they are correct:
**Time Period is rarely defining** unless the period is the subject (`single day`
on La Haine is structural; Mulholland Drive's `2000-2010's` is background, hence
the empty list), and **Genre skews secondary** — which is consistent with main
genres being excluded from identification anyway.

**B2 — prompt section.** Add to `ENRICHMENT_SYSTEM_PROMPT`, after the tag
selection philosophy block:

```
Defining vs secondary tags:
Every tag you assign must genuinely apply. Among those, mark the DEFINING ones —
the tags someone would use to describe this film in two sentences to a friend.
Test: if this tag disappeared, would that description still be accurate?
- John Wick: "fight" is defining — remove it and you have misdescribed the film.
- A family drama with one memorable brawl: "fight" applies, but is secondary.
Everything you list that is not marked defining is understood to be secondary.
A secondary tag is still a real tag: it is not a lower-confidence guess, it is
an accurate description of something the film contains without being about.
Typically 30-50% of the tags you assign will be defining. Judge each tag on its
own merits rather than to a quota — but if you are marking nearly everything, or
almost nothing, you have lost the distinction.
```

The 30–50% band is measured, not invented: the three reference films land at
49% / 54% / 51%, and they are unusually dense canonical works, so that is an
**upper** bound rather than the expected mean. Step 25's sample pass recalibrates
it against ordinary films.

> **Do not confuse two different things.** The *defining set* is ~20–25 tags per
> film, judged absolutely by Claude. The *minimum identifying set* is the 3–4
> tags that suffice to isolate the film among 4048 — a **derived subset**,
> computed in SQL in Step 26, never requested from the model. 2001's identifying
> set (`AI/technology`, `alien contact`, `contemplative/meditative`) is a subset
> of its 25 defining tags; `philosophical` and `space` are equally defining but
> add no discriminating power.

**B3 — validation.** In `_validate_enrichment`, after the list-dimension loop:
for each dimension, intersect `defining[dim]` with the validated tag list, drop
anything outside it with a warning, and normalise missing/malformed `defining`
to `{dim: [] for dim in list_dims}`. Add the same empty shape to
`_empty_enrichment()`. A defining tag that isn't in the tag list must **never**
be written.

**B4 — optional film context.** Give `_build_film_block` a
`extra_context: dict | None = None` parameter that renders extra `- Key: value`
lines at the end of the metadata block. Used by the re-tag script to pass the
known setting period; unused by Add Film. This is deliberately factual context
only — do NOT pass existing tags here (see PLAN.md Step 24 guardrail 4).

**B5 — writes carry weights.** In `films.py`, `create_film` and `update_film`
must write `weight` on every junction row. `create_film` reads
`enrichment["defining"]`; `update_film` has no defining input, so it writes
`NULL` — do not invent a value there. Keep `ON CONFLICT DO NOTHING` semantics.

---

### Part C — `scripts/retag_films.py`

Four separate commands. Generating must never write to the database, and
applying must never call the API.

**Shared:** import `ClaudeEnricher` and use its `_static_prefix` /
`_build_film_block`. Do **not** rebuild the prompt — that fork is what
`claude_batch_enrichment.py` did and why it drifted. Move `MODEL_PRICES` and the
cost helpers out of `claude_enrichment_runner.py` into a new `scripts/_pricing.py`
and import from both.

**`snapshot`** — `CREATE TABLE <junction>_pre_retag AS SELECT * FROM <junction>`
for all seven (drop-if-exists first, with a confirmation prompt since that
discards a previous snapshot). Print row counts and the exact `pg_dump` command
to run alongside. Print the restore procedure too.

**`generate`** — flags: `--sample FILE`, `--all`, `--batch`, `--limit N`,
`--resume`, `--sample-subset N`, `--exclude-reference` (**default on**).

Sample file format — plain text, one film per line, `#` starts a comment
(whole-line or trailing), blank lines skipped. Entries are either a bare
`film_id` or `Title (year)`; resolve titles against `film.original_title` and
`film_language.film_title`, and **abort with the ambiguous candidates listed**
rather than guessing when a title matches more than one row.

```
# --- films I know cold ---
1247
Barry Lyndon (1975)
# --- structural edge cases ---
892   # silent
1455  # documentary
```

`--sample-subset N` takes the first N resolved entries, for fast iteration on a
core group before running the full sample.

`--exclude-reference` skips the three films in `taxonomy_config.REFERENCE_EXAMPLES`
(match by title+year, resolve to film_id once and report it). Re-tagging a film
whose validated answer is already in the prompt as a few-shot example is
circular and teaches nothing. `--include-reference` overrides.

1. Select films from the **database** (`film_id`, `tmdb_id`, `original_title`).
2. Re-fetch TMDB details (`get_film_details` + `get_film_details_fr`) and map via
   `TMDBMapper.map_film_to_db()`. Cache each raw payload under
   `scripts/data/retag/tmdb/{tmdb_id}.json` and reuse it on re-runs — the sample
   pass will be run repeatedly and should not re-hit TMDB.
   *Why re-fetch rather than rebuild from the DB: TMDB **keywords are not
   stored** by `create_film`, and they are useful tagging signal. Re-fetching
   also makes the re-tag input identical in shape to the Add Film input, so the
   two paths behave the same.*
3. Read each film's current `time_context` tags with `sort_order < 100` and pass
   them as `extra_context={"Setting period": "..."}`.
4. Enrich; append to `scripts/data/retag/enriched.jsonl` as
   `{film_id, tmdb_id, title, enrichment, usage, model, generated_at}`.
   JSONL so a crash costs one line. `--resume` skips film_ids already present.
5. Print running cost and cache hit rate from `usage_totals`.

For `--batch`, port the submit/status/collect flow from
`claude_batch_enrichment.py` as `generate --batch` / `--batch-status ID` /
`--batch-collect ID`, using the enricher's two-breakpoint structure. **Check
whether a 1-hour cache TTL (`{"type": "ephemeral", "ttl": "1h"}`) is supported
by the installed SDK** — a 4048-film batch will not stay inside a 5-minute
window, and cache misses across the run are the single biggest cost risk. If
unsupported, say so in the output and fall back to the default TTL.

**`diff`** — reads the JSONL and the live DB, writes
`scripts/data/retag/diff_report.md` + `.json`. **Touches nothing.** Contents:

**Alarm rules — tags are partitioned into three buckets by their BEFORE count,
because one rule cannot serve all of them.** The ~38 tags introduced by
migration 026 start at zero, so any naive growth test fires on every one of
them, and a ratio test is meaningless on small numbers (5 → 20 films is 4x and
signifies nothing).

| Bucket | Before | Rule |
|---|---|---|
| **Cold start** | < 10 | Growth is the goal — report the absolute count, no alarm. One exception: landing above ~800 films means the definition is far too loose. |
| **Sparse** | 10–49 | Report only. Too noisy to judge in either direction. |
| **Established** | ≥ 50 | Alarm on losing >50% of its films, or on gaining >2.5x **and** more than 100 films in absolute terms. |

Report sections, in this order:

1. **Cold-start coverage** — first, because "did the 38 new tags get populated,
   and sensibly?" is one of the two questions this whole exercise exists to
   answer. Every tag with before < 10, its after count, and a sample of 5 films
   that gained it so the assignments can be eyeballed.
2. **Alarms** — established-bucket violations only, each with before/after and
   5 example films gained or lost.
3. **Per-tag table** — all tags across the seven dimensions: bucket, before,
   after, delta, gained, lost. Sorted by absolute delta.
4. **Per-dimension summary** — mean tags per film, before/after.
5. **Weight distribution** — share of assigned tags marked defining, overall and
   per dimension. Expected band **30–50%**; flag above 70% (distinction has
   collapsed) or below 15% (over-strict). Both thresholds are provisional and
   get recalibrated from the sample pass — say so in the report header.
6. **Biggest movers** — the 30 films with the most changes, tags listed.
7. **Time Period check** — assert no `sort_order < 100` row would be lost.

**`apply`** — `--dry-run` (default) and `--commit`. Per film, per dimension:
delete existing junction rows and insert the new set with weights, **except**
for `film_period`, where rows whose `time_context.sort_order < 100` are kept and
only `>= 100` rows are replaced. Skip `[NEW]`-prefixed values. **Do not touch
`award`, `source`/`film_origin`, or `film_set_place`** — the enrichment carries
them, but re-tag applies to tags only. Sync `film.color` from the
`black and white` tag as `create_film` does. One transaction per film, with a
progress counter and a final summary.

---

### Part D — Delete `scripts/claude_batch_enrichment.py`

After its batch plumbing is ported. Grep for references (`README.md`,
`CLAUDE.md`, `PROMPTS.md`) and update them. Git history keeps the file.

---

### Verification (no production run)

1. Migration applies; `\d film_theme` shows the column and index; existing rows
   are NULL.
2. `snapshot` creates seven tables with matching row counts.
3. `generate --limit 3` — report the returned `defining` sets and confirm cache
   reads of ~20 423 on calls 2 and 3.
4. Feed the validator a hand-made enrichment whose `defining` contains a tag
   absent from its list, and one with `defining` missing entirely — both must be
   cleaned, logged, and never crash.
5. `diff` on those 3 films produces both report files; DB unchanged.
6. `apply --commit` on **one** film: weights present on every row, its
   `sort_order < 100` time rows unchanged, its awards/set_places untouched.
   Restore that film from its `_pre_retag` snapshot afterwards and confirm the
   restore is exact.
7. Add Film end to end: still works, saved rows carry weights.
8. Backend imports clean.

Report the observed defining/secondary ratio on the 3 test films — that number
drives whether Step 25's sample pass starts by tuning the prompt. Compare it to
the 30–50% band; report it plainly whatever it is rather than adjusting the
prompt to hit the target, since the band itself is provisional.

---

## Step 25 Prompt — Re-tag Execution

**Do not start this until Martin has supplied the sample film list and reviewed
the Step 24 verification.** This step touches real data.

Read `PLAN.md` Step 25 first. The sequence is fixed:

1. `snapshot` + the printed `pg_dump`. Confirm both before continuing.
2. `generate --sample martin_sample.txt` — real-time, not batch (immediate
   feedback).
3. `diff` → present the report to Martin. **Stop. Do not apply.**
4. Iterate on `database/tags_definition.md` and the enricher prompt as Martin
   directs, re-running `generate --sample` (TMDB payloads are cached, so
   iterations only cost API tokens). Each iteration: report the defining ratio
   and the alarm section.
5. Once Martin approves, `generate --all --batch`.
6. `diff` on the full set → present. **Stop again.**
7. `apply --commit` only on explicit instruction.
8. Post-apply: re-run the verification queries, confirm the ~38 previously-empty
   tags now have associations, spot-check the three reference films against
   `taxonomy_config.REFERENCE_EXAMPLES`, and confirm `/films/{id}/similar`,
   `/stats/dashboard` and the three game endpoints still return 200.

Supabase is **not** touched by this step — Martin syncs manually once he is
satisfied with the local result.

If at any point the diff shows a tag losing more than half its films or more
than tripling, surface it prominently and stop rather than proceeding on
momentum.

---

## Step 24.1 Prompt — Definition Fixes + Union Apply Mode

The Step 24 three-film sample pass (`scripts/data/retag/diff_report.md`) worked:
it surfaced real defects before any data was touched. **Do not run the full
re-tag.** Fix the causes, re-run the same three films, report.

Read `CLAUDE.md`, then `PLAN.md` (Steps 24–25), then
`scripts/data/retag/diff_report.md`, then:
- `database/tags_definition.md`
- `backend/app/services/claude_enricher.py` (`ENRICHMENT_SYSTEM_PROMPT`,
  `_build_taxonomy_section`, `_validate_enrichment`)
- `backend/app/services/taxonomy_config.py` (context — change no tag list)
- `scripts/retag_films.py` (`apply`, `diff`)

**Absolute rule for this step: no film titles anywhere** — not in
`tags_definition.md`, not in the system prompt, not in a code comment that ends
up in the prompt. Martin removed them deliberately: a named example makes the
model match against that film instead of applying the definition, and the
current `fight` failure is a probable instance. Existing named references in the
`art house` entry are pre-existing; leave them, do not add more.

---

### Part A — System prompt: the restraint register

Every dimension whose guidance contains a restraint gate went **down** or barely
moved in the sample; every dimension without one went up. Genre fell 9.67 → 6.33
tags per film. Those gates were written when there was no way to say "this
applies but isn't central." There is now, and they are double-counting.

**A1 — terminology collision.** The philosophy block uses "DEFINING" to mean
*worth including at all*, while the newer block uses it to mean *the top
subset*. Same word, opposite operational consequence, forty lines apart. Replace
the block:

```
Tag selection philosophy — tags must characterize the film, not catalogue it:
- Assign a tag when the film genuinely satisfies its definition. Incidental
  background detail that no viewer would associate with the film does not qualify.
- Do not withhold a tag because it feels less central than others: the weighting
  step below exists precisely to record that. Withholding it loses the
  information entirely; marking it secondary keeps it.
- Tags with no entry in the Tag Usage Guide are not lesser tags. The guide
  defines only what needs disambiguating; apply undefined tags on their plain
  meaning, with the same willingness.
```

That third bullet addresses the sharpest finding in the sample: six of
Fellowship's fifteen losses are tags with **no entry in the guide**, including
both magic tags on a film whose most famous character is a wizard.

**A2 — drop the named example** from the "Defining vs secondary" block. Replace
the two bullets with:

```
- A film built around physical combat: "fight" is defining — remove it and the
  description is wrong.
- A film containing one memorable brawl: "fight" applies, but is secondary.
```

Same contrast, nothing to pattern-match against.

---

### Part B — Taxonomy section gates

**B1 — Genre.** Replace `- Add sub-genres ONLY when they clearly define the film`
with:

```
- Add every sub-genre the film genuinely satisfies; use the defining/secondary
  marking to record how central each one is.
```

**B2 — Themes.** The heading reads `(pick all that apply — be thorough, but only
CENTRAL themes)`. "Be thorough, but only central" is self-cancelling. Replace
with `(pick all that apply — be thorough; record centrality in the defining set,
not by omission)`.

**B3 — remove `franchise` from the prompt.** Franchise membership is **derivable**:
`film.tmdb_collection_id`. Asking a model to guess a fact you already store is
how a standalone film acquired the tag.

- Add a module-level `DERIVED_TAGS = {"cinema_type": {"franchise"}}` in
  `taxonomy_config.py`, with a comment explaining it stays a real, filterable
  taxonomy tag — it is simply not model-assigned.
- Filter it out of the `Valid:` list rendered by `_build_taxonomy_section`.
- Strip it in `_validate_enrichment` (debug-level log, not a warning — it is
  expected, not a defect).
- Delete its entry from `tags_definition.md`.
- **Do not** remove it from `VALID_CINEMA_TYPES`.

---

### Part C — `tags_definition.md`

**C1 — six missing definitions.** Add these verbatim, each under its correct
dimension heading and in existing sort order.

Characters:

> **witch/wizard** — a character whose identity is built on the practice of
> magic: spellcasting, enchantment, arcane knowledge. Covers folkloric witches
> and fantasy mages alike. Distinct from the Theme **sorcery** (magic as a
> subject of the film) and from **paranormal** (unnatural faculties held without
> an arcane tradition).
>
> **super hero** — a character with extraordinary powers or abilities who acts
> publicly as a protector figure, usually with a costumed or assumed identity.
>
> **elderly** — an old character is central to the film, and their age is
> relevant to who they are or to what the film is doing. Not for any film that
> happens to feature an old person.

Theme — Face to the unknown:

> **sorcery** — magic as a practised craft within the film: spells, enchantments,
> rituals, arcane power and the rules governing it. Distinct from **supernatural**
> (Genre), which structures the whole film, and from **paranormal**, where
> faculties are experienced rather than practised.
>
> **curse** — a malediction laid on a person, family, object or place, whose
> effects drive the narrative.

Atmosphere:

> **violent** — violence is frequent, graphic or sustained enough to mark the
> viewing experience. About the intensity of depiction, not the mere presence of
> conflict (see the Theme **fight**).

**C2 — `no particular` is exclusive.** It was added to all three sample films
*alongside* real place tags. The definition never says it excludes them, and in
the file it sits above the `### Environments` heading, so it reads as a
dimension-level note rather than a value. Move it under a `### None` heading at
the end of the Place section and rewrite:

> **no particular** — the setting is irrelevant or interchangeable; the film does
> not rely on any specific location for its identity. **Exclusive: use it alone,
> never alongside another Place tag.** If any environment, building, narrative
> setting or vehicle tag applies, this one does not.

**C3 — Environments needs a scope lead-in.** Every Place tag *gained* in the
sample belongs to a group with an explicit scope note; every Place tag *lost*
(`mountains`, `beach`, `underground`) is in Environments, the one group with no
lead-in — so the model applied a "primary setting" standard there and a
"significant setting" standard everywhere else. Add under `### Environments`:

> Applied when a significant portion of the film takes place there, including
> major set-pieces. Not restricted to the film's single primary setting — a film
> can legitimately carry several environments.

**C4 — `fight`.** The tag sits under Theme → Human Relations → *Interpersonal
conflict*, among tags that all describe relationships between characters who
have one. Combat against anonymous opponents fails that framing, so an
action-heavy film lost the tag. Append:

> Records the presence of physical combat regardless of whether the combatants
> have any prior relationship — fights against anonymous, impersonal or faceless
> opponents count fully. Despite its placement under Interpersonal conflict, this
> tag is about action content, not relational dynamics.

**C5 — `spy`.** Append to the existing entry: `Corporate and industrial
espionage qualify equally.`

**C6 — `gritty/realistic`.** The current definition leads with a visual checklist
(handheld, unflattering light, dirt, lived-in locations) that a weathered
fantasy production design satisfies while missing the intent. Replace:

> **gritty/realistic** — the film makes the viewer feel the physical and social
> harshness of a real, lived-in world: poverty, decay, bodily wear, unglamorous
> surroundings. A raw aesthetic (handheld camera, natural or unflattering light)
> serves that end but is not sufficient on its own. Does not apply to genre,
> fantasy or period films whose weathered production design is a visual style
> rather than a lived social condition. Distinct from **realism** (Cinema Type),
> which is membership of an identified cinematic movement — gritty/realistic is a
> texture available to any film of any era.

**C7 — `realism`,** symmetrically. Append:

> Distinct from the Atmosphere **gritty/realistic**: realism is a lineage a film
> belongs to, with a period attached; gritty/realistic is a felt texture any film
> of any era may have.

---

### Part D — Validation

**D1 — `no particular` exclusivity.** In `_validate_enrichment`, after the
list-dimension loop: if `place_environment` contains `no particular` **and** any
other value, drop `no particular` and log a warning. Belt and braces alongside C2.

**D2 — audit the existing data.** Report (do not modify) how many of the 287
films currently tagged `no particular` also carry another place tag. If the old
pipeline made the same mistake, Martin will want a cleanup migration — that is
his call, not yours.

---

### Part E — Derived franchise

In `retag_films.py apply`, after the tag junctions: for each film in scope, set
`franchise` in `film_technique` from `film.tmdb_collection_id IS NOT NULL`.

- Missing but should be present → **insert**, `weight = NULL` (derived, not
  model-judged).
- Present but should be absent → **do not delete.** Write it to the loss review
  (Part F) as `cinema_type:franchise (derived)`. A collection id can be absent
  from TMDB for a film that really is part of a series, so this is a review
  signal, not a truth.

---

### Part F — Union apply mode + per-tag loss review

The sample produced 73 gains and 42 losses across three films; Martin endorsed
roughly a quarter of the losses. Gains are safe, losses are where the damage is
— and losses aggregate well, so make the destructive operation reviewable at the
level where judgement is cheap.

**`apply --mode union` becomes the default.** Insert gains with their weights;
delete nothing. Existing tags the model did not propose keep `weight = NULL` —
do **not** write 50. The model never evaluated them, and recording an
unevaluated tag as "secondary" invents information. Consumers treat `weight =
100` as defining and everything else (50 or NULL) as secondary, so NULL is
already correct.

`--mode replace` stays available and keeps the existing Time Period preservation
rule, but is no longer the default.

**`loss_review.md`** — written by `apply` in union mode, grouped **by tag, not by
film**:

```
### themes:fight — would be removed from 340 films
Current count: 1341 → 1001
Sample: <up to 10 titles>
Approve with: retag_films.py apply --remove-tag themes:fight
```

Sorted by film count descending. `--remove-tag DIM:TAG` (repeatable) deletes
that tag from exactly the films in the current JSONL scope that lost it, in one
transaction, and logs what it removed. Reviewing ~50 tags is tractable;
reviewing 4048 films is not.

**`diff`** gains a scope-only per-tag view. At three films the library-wide table
is all noise — every row reads ±1 against a base of hundreds. Add a
"scope-only" column pair (films in scope holding the tag, before/after) and sort
the table by that when scope is under ~200 films.

---

### Part G — Re-run and report

1. Report the **measured** static-prefix token delta (before vs after). Estimate
   is +320 tokens (+1.6%), ≈ +$0.40 across 4048 films cached, partly offset by
   dropping `franchise` from the output. If the real delta exceeds +1000
   tokens, stop and report rather than proceeding — Martin re-evaluates pricing
   at that point.
2. `generate --sample` on the **same three films** (film_id 4, 5, 6). TMDB
   payloads are cached, so this costs about four cents.
3. `diff`, then report specifically:
   - Is `no particular` gone from all three?
   - Do the two magic tags return on the fantasy films?
   - Do `fight` and `spy` return on the espionage film?
   - Do `mountains` and `beach` return?
   - Is `gritty/realistic` gone from the fantasy film?
   - Is `franchise` absent from the model output entirely?
   - Genre mean per film — recovered toward the 9.67 baseline?
   - Defining share per dimension, against the 30–50% band.
4. `apply --dry-run --mode union` on the three films: show the gains that would
   land and the `loss_review.md` that would be written. **Apply nothing.**

Report results and stop. Martin decides whether the definitions are ready for
his ~40-film list.

---

## Step 24.2 Prompt — Genre Gate, Stranded Tags, Derived `no particular`

The Step 24.1 re-run fixed the magic tags, `gritty/realistic` and `franchise`,
and improved generosity substantially (Themes 12 → 17, Character 5.7 → 11,
Place 3.7 → 5.3 mean tags/film). Three defects remain, each with an identified
cause. **Do not run the full re-tag.** Fix, re-run the same three films, report.

Read `CLAUDE.md`, then `PLAN.md` (Steps 24–25), then
`scripts/data/retag/diff_report.md`, then:
- `database/tags_definition.md`
- `backend/app/services/claude_enricher.py`
- `backend/app/services/taxonomy_config.py` (`DERIVED_TAGS`)
- `backend/app/routers/films.py` (`create_film`, `update_film`)
- `scripts/retag_films.py` (`apply`)

**No film titles anywhere** — same absolute rule as Step 24.1.

---

### Part A — The duplicate Genre gate (this is why Genre didn't recover)

Step 24.1 B1 relaxed the sub-genre rule in `_build_taxonomy_section`. It missed
the **second copy**. `database/tags_definition.md` line 8 still reads:

> Main genres (…) are always assigned — at least one per film. The tags below are
> sub-genres: use them only when they clearly define the film.

Both strings enter the same prompt. The guide arrives later and is framed as
authoritative ("Follow these precisely"), so the strict twin plausibly overrode
the relaxed rule — which explains Genre moving only 6.33 → 6.67 while every
ungated dimension moved a lot.

Replace that sentence with:

> Main genres (…) are always assigned — at least one per film, usually one to
> three. The tags below are sub-genres: apply every one the film genuinely
> satisfies, and use the defining/secondary marking to record how central each
> one is.

**Then sweep for the same failure elsewhere.** Search **both**
`tags_definition.md` and `_build_taxonomy_section` for dimension-level or
group-level restraint gates — lead-in text that tells the model to withhold tags
across a whole dimension or group. Phrases to look for: "only when", "only
for", "do NOT include", "be thorough, but", "apply only". Report each one found
with its location and recommend a rewrite; apply the obvious ones.

**Critical distinction — do not over-apply this.** *Per-tag* hedging ("not simply
a sad film", "not for every film that contains conversations") is precision and
must be left completely alone. Only *dimension-level and group-level* gates are
in scope: those double-count against the weighting mechanism, which per-tag
boundaries do not.

---

### Part B — `fight`: a tag stranded in the wrong neighbourhood

Step 24.1 C4 added an explicit clause to the `fight` definition and it changed
nothing. That suggests the model is not rejecting the definition but never
reaching it: the guide is organised by group, `fight` sits under **Human
Relations > Interpersonal conflict** among tags that all describe relationships
between characters who have one, and on a film with no interpersonal-conflict
theme the model plausibly skips the entire group. A definition inside a skipped
group can say anything.

Moving the tag would mean reopening the taxonomy, which is closed. Test a
cross-pointer instead — a reference from a group the model *will* visit on an
action film. Append to the Atmosphere **violent** entry:

> A film with significant combat sequences also earns the Theme **fight**,
> whether or not the film has any interpersonal conflict as a subject.

This is an **experiment**, not a known fix. Report explicitly whether `fight`
returns on the espionage film. If it does, the same technique rescues any tag
stranded in a group that doesn't match its meaning, and that is worth recording
in PLAN.md as a reusable pattern. If it does not, say so plainly and do not
keep adding cross-pointers — Martin will decide whether `fight` is worth a
taxonomy move later.

Leave `spy` and `beach` alone. Corporate infiltration read as heist rather than
espionage is defensible, the limbo shore is genuinely marginal, and union mode
means neither was ever removed.

---

### Part C — Derive `no particular`

The model emitted it on all three films again despite the exclusivity rule; only
the D1 validator guard stopped it. Guarding against a problem on every call is
worse than removing the problem: like `franchise`, this value is **computable**
— it means "no other place tag applies", which is a fact about the output, not a
judgement about the film.

1. `DERIVED_TAGS` becomes
   `{"cinema_type": {"franchise"}, "place_environment": {"no particular"}}`.
   The existing filtering of derived tags out of the prompt's `Valid:` lists and
   the debug-level strip in `_validate_enrichment` then cover it automatically —
   verify both actually generalise rather than being hardcoded to `franchise`.
2. Delete the `### None` heading and the `no particular` entry from
   `tags_definition.md`.
3. Keep the D1 exclusivity guard as a cheap invariant; it should now never fire.
4. **Apply-time rule**, in `retag_films.py apply` and in both `create_film` and
   `update_film` (so Add Film stays consistent — factor it into one helper):
   after the place junction writes, if the film has zero `film_place` rows,
   insert `no particular` with `weight = NULL`; if it has any other place tag,
   remove `no particular`.

**On that removal and the union guarantee.** Union's no-delete rule protects
*model judgements*; derived tags are computed and are exempt. Note the asymmetry
with `franchise`, which is insert-only: a missing TMDB collection id is not proof
a film stands alone, so absence there is a review signal. Here, the presence of
another place tag **is** proof by definition. Record this reasoning in a comment
so the two rules don't get "harmonised" later.

---

### Part D — Migration 030: clean up the existing contradictions

The Step 24.1 D2 audit found **91 of 287** films carrying `no particular`
alongside another place tag — the old pipeline made the same mistake, and union
mode would preserve every one.

`database/migrations/030_no_particular_cleanup.sql`, one transaction:
- Delete `no particular` from any film that has another `film_place` row.
- Report, but do **not** insert for, films with zero place tags — give Martin
  the count so he can decide separately.
- Print before/after counts.

Run `--dry-run` equivalent first (a `SELECT` of what would be deleted), report
the numbers, and **wait for Martin's approval before committing.** Local DB
only; he syncs Supabase himself.

---

### Part E — Record two decisions in PLAN.md

Under Step 24, add a short "Decisions" subsection:

- **`ghost/spirit` stays undefined, deliberately.** Martin confirmed the tag
  should cover mental projections and hallucinations of the dead, not only
  literal ghosts. Adding a definition would narrow it. Do not "fix" this later.
- **Derived tags** and why the two rules differ (Part C reasoning, one or two
  lines).

---

### Part F — Re-run and report

1. Measured static-prefix token delta. Expect roughly neutral: the `no
   particular` entry and value leave, the Genre rewrite and the `violent`
   cross-pointer arrive. Same +1000 stop threshold as before.
2. `generate --sample` on film_id 4, 5, 6 (~$0.12).
3. `diff`, and report specifically:
   - **Genre mean per film** — the headline number. Baseline 9.67, last pass
     6.67. Also list which sub-genres returned.
   - Does `fight` return on the espionage film? (Part B experiment result.)
   - Is `no particular` absent from the model output entirely?
   - Any other dimension-level gates found in the Part A sweep.
   - Defining share per dimension — Genre and Cinema Type were 65% / 63%,
     above the 30–50% band. If Genre's count recovers, its share should fall
     toward the band on its own; report whether it did.
4. `apply --dry-run --mode union` on the three films. **Apply nothing.**

Report and stop. Note in the report that per-film **output** tokens are now the
dominant cost at scale (generosity grew them), so the Step 25 full-run estimate
should be recomputed from this pass rather than from Step 24's figures.
