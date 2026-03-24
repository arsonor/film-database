# Film Database — Project Context for Claude Code

## Project Overview

A personal film database application with a rich filtering interface, recommendation engine, and agentic capabilities for adding/enriching films. The database contains ~2500+ films spanning from 1902 to 2026.

## Source Documents

Three reference documents define this project (located in the associated Claude.ai project):

1. **Films_list.docx** — Chronological filmography (~2500+ titles) organized by year, grouped by region (Francophone, Anglo-Saxon, Asian, Other). Includes franchise entries and animation. Titles are mostly in French.
2. **Film_attributes.docx** — Full taxonomy of classification attributes (see Taxonomy section below).
3. **Film_database.pdf** — Entity-Relationship diagram showing the relational schema.

## Tech Stack

- **Database:** PostgreSQL
- **Backend:** Python (FastAPI)
- **Frontend:** React + Tailwind CSS + shadcn/ui
- **Primary Data API:** TMDB (The Movie Database) — posters, cast/crew, genres, keywords, runtime, release dates, production companies, languages, overview. Supports French titles via locale parameter.
- **Complementary Sources:** Wikidata/Wikipedia (awards, cultural movements), OMDb (IMDb cross-reference)
- **Recommendation Engine:** Tag-based similarity scoring + Claude API for external suggestions
- **AI Enrichment:** Claude API for classifying films into the full taxonomy

## Database Design Principles

### Core Entity: FILM
Central table linked to all classification dimensions via junction tables (many-to-many relationships).

**Film attributes:**
- film_id, original_title, duration, color (boolean), first_release_date, summary, vu (boolean = seen by user), poster_url, backdrop_url, imdb_id, tmdb_id
- **budget** (production budget in USD)
- **revenue** (worldwide box office in USD)

### People & Roles
- `person` — id, firstname, lastname, gender, date_of_birth, date_of_death, nationality, tmdb_id, photo_url
- `person_job` — id, role_name (Director, Writer, Cinematographer, Composer, Producer, Editor, etc.)
- `crew` — film_id, person_id, job_id
- `casting` — id, film_id, person_id, character_name, cast_order (detailed: include secondary characters)

### Production
- `studio` — id, name, country
- `production` — film_id, studio_id

### Titles & Languages
- `language` — id, code, name
- `film_language` — film_id, language_id, film_title, is_original (boolean), has_dubbing (boolean)

### Classification Dimensions (all many-to-many)

#### Categories
Values: Action, Adventure, Comedy, Drama, Romance, Thriller, Horror, Science-Fiction, Fantasy, Musical, Disaster, Historical
Historical sub-categories: biopic, human interest story, judicial chronicle, western, peplum, swashbuckler

#### Cinematography / Cinema Type
Values: silent, animation, mixed animation, art house, blockbuster, sequence-shot, found footage, motion capture, multi-sequence, black_and_white (deliberate aesthetic choice), slow_cinema, non_linear_narrative

#### Cultural Movement
Values: expressionism, neo-realism, realism, noir, hollywood golden age, new hollywood, new wave, neo-noir, dogma, blaxploitation, wu xia pian, generational, popular culture, aesthetics, CGI, 3D, B, Z, Collection

#### Geography & Place Context
**Geography** — continent, country, state/city
**film_set_place** — film_id, geography_id, **place_type**: one of:
  - `diegetic` = location as depicted in the film's narrative
  - `shooting` = real physical shooting location
  - `fictional` = invented/fantasy location

**Place Environment:** no particular, urban, country-style, maritime, naval, island, forest, mountains, desert, beach, space, huis clos, road movie, school/university, company/factory, building, household/house/apartment, jail, hospital

#### Time Context
Values: undetermined, future, contemporary, end 20th, 30-year post-war boom, WW2, interwar, WW1, early 20th, 19th, modern age, medieval, antiquity, prehistoric
Seasonal: summer, winter, autumn, spring

#### Context / Theme
Values: social, societal, political, religion, business, trial, prison, apocalypse, war, tragedy, trauma, psychological, disease, accident, death, mourning, addiction/drugs, time passing, investigation, spy, crime, organized crime, delinquency, organized fraud, sex crime, mafia, gangster, serial killer, chase/escape, terrorism, sect, survival, slasher, futuristic, dystopia, tales and legends, supernatural, sorcery, alien contact, paranormal, time travel/loop, virtual reality, dream, nonsense, art (with sub-types: music, cinema, literature, fashion, painting, sculpture, theatre, radio), martial arts, sport, nature, technology, food/cooking, party, book
**Extended:** identity_crisis, police_violence, evolution, artificial_intelligence, amnesia, corruption, class_struggle, immigration, censorship

#### Characters Type
Values: solitary, tandem, couple, adult/child, trio, buddies, gang, relatives, generations, ensemble cast, animal/wildlife
**Character Context:** childhood, teenager, elderly, female, LGBT, cross-dressing, double, interracial
**Character Archetypes:** super hero, vigilante, cop, detective, samourai, pirate, viking, barbarian, psychopath, madness, idiot, looser, prostitute, freak/disabled, monster/terrestrial creature, ghost/spirit, evil, witch, vampire, zombie, android, alien
**Extended:** unreliable_narrator, antihero, femme_fatale

#### Motivations / Relations
Values: feelings, friendship, emancipation, solidarity, adultery, jealousy, sex, harassment, lie, doubt/dilemma, rivalry, power, perversion, manipulation, redemption, obsession, vengeance, rebellion/revolt, fight (reserved for physical body combat/confrontation), odyssey, quest, world saver

#### Atmosphere
Values: family, feel good, crazy/nutty, depressive/sad, sulfurous, mysterious, violent, trash, gore, awful/seedy/depraved, oppressive, disturbing, contemplative
**Extended:** hypnotic, psychedelic, ethereal, claustrophobic

#### Message Conveyed
Values: parodic, satirical, political, humanist, nostalgic, dreamlike, surreal, symbolic, philosophical, metaphysical, dialogs, slang dialogs, black comedy
**Extended:** anti_establishment, feminist, absurdist, ecological

### Film Relationships
- `film_sequel` — film_id, related_film_id, relation_type: sequel, prequel, remake, spinoff, reboot

### Source / Origin
- `source` — id, type (original screenplay, novel, comic, TV series, true story, play, video game, poem, short story, remake), source_title, author

### Exploitation
- `stream_platform` — id, platform_name
- `film_exploitation` — film_id, platform_id

### Awards
- `award` — film_id, festival/ceremony name, category, year, result (won/nominated)

## Important Design Notes

1. **Place Context Duality:** Always differentiate between diegetic (in-film narrative location) and shooting (real filming location). A film set in "Los Angeles" may have been shot in Vancouver.
2. **Cast Detail Level:** Include secondary characters, not just leads. Aim for top 10-15 cast members when available.
3. **Fight keyword:** Reserved strictly for physical body combat/confrontation scenes, not metaphorical struggles.
4. **Budget & Revenue:** Store in USD. TMDB provides this data for most films. Useful for profitability analysis.
5. **Taxonomy is extensible:** When a film's characteristics don't fit existing keywords, add new ones. The system should support dynamic taxonomy growth.
6. **French titles:** Many films in the list have French titles. Always store both original and French titles via film_language table.
7. **Awards:** Populated via Claude enrichment (major festivals and ceremonies: Oscars, Cannes, Venice, Berlin, César, BAFTA, Golden Globes). Claude knows award history for well-known films.
8. **Streaming:** Populated via TMDB watch/providers endpoint (`/movie/{id}/watch/providers`), mapped to our platform names. Streaming data is volatile — consider refreshing periodically.

## Three Reference Films (validated classification)

These serve as ground truth for the taxonomy classification pipeline:

### 2001: A Space Odyssey (1968)
- Categories: Science-Fiction, Drama, Adventure
- Cinematography: Blockbuster, Art house
- Cultural movement: New Hollywood (precursor), Aesthetics
- Themes: futuristic, alien contact, technology, odyssey, death, time passing, evolution
- Characters: solitary, tandem, android (HAL 9000), alien
- Motivations: quest, odyssey, power, doubt/dilemma, survival
- Atmosphere: contemplative, oppressive, mysterious, disturbing
- Message: philosophical, metaphysical, symbolic, surreal
- Time: prehistoric, 30-year post-war boom, future
- Place: space, desert (Africa)

### La Haine (1995)
- Categories: Drama, Thriller
- Cinematography: Art house, black_and_white
- Cultural movement: realism, generational
- Themes: social, societal, political, delinquency, tragedy, death, police_violence
- Characters: trio, buddies, interracial, teenager
- Motivations: friendship, solidarity, rebellion/revolt, vengeance
- Atmosphere: violent, oppressive, depressive/sad
- Message: political, humanist, slang dialogs, black comedy
- Time: contemporary, end 20th
- Place: urban (France, Île-de-France), Paris

### Mulholland Drive (2001)
- Categories: Drama, Thriller
- Cinematography: Art house
- Cultural movement: Aesthetics, neo_noir
- Themes: psychological, dream, art (cinema), crime, investigation, identity_crisis, accident, mafia
- Characters: tandem, couple, female, double, LGBT
- Motivations: feelings, obsession, jealousy, manipulation, lie, sex, adultery, vengeance
- Atmosphere: mysterious, sulfurous, disturbing, oppressive, hypnotic
- Message: surreal, dreamlike, symbolic, metaphysical
- Time: contemporary, end 20th
- Place: urban (USA, California, Los Angeles), Hollywood

## Project Structure

```
film-database/
├── CLAUDE.md              # This file — project context
├── PLAN.md                # Implementation plan & progress tracking
├── database/
│   ├── schema.sql         # PostgreSQL schema (DDL)
│   ├── seed_taxonomy.sql  # Pre-populate taxonomy reference tables
│   └── migrations/        # Schema migrations
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app entry
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic (TMDB, Claude, recommendations)
│   │   └── schemas/       # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Main views
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # Utilities, API client
│   ├── package.json
│   └── tailwind.config.js
├── scripts/
│   ├── parse_film_list.py # Parse Films_list.docx into structured data
│   ├── tmdb_fetcher.py    # TMDB API integration
│   ├── claude_enricher.py # Claude API taxonomy classification
│   └── bulk_ingest.py     # Orchestrate bulk film ingestion
└── .gitignore
```

## API Endpoints (planned)

| Endpoint | Method | Purpose |
|---|---|---|
| `/films` | GET | Paginated list with multi-filter query params |
| `/films/{id}` | GET | Full film detail with all relations |
| `/films/search` | GET | Full-text + faceted search across all taxonomy |
| `/films/{id}/recommendations` | GET | Similar films (in-DB + external via Claude) |
| `/films` | POST | Add new film (manual or from TMDB ID) |
| `/films/{id}` | PUT | Edit film metadata/tags |
| `/taxonomy/{type}` | GET | List all values for a taxonomy dimension |
| `/persons/{id}` | GET | Person filmography |
| `/films/enrich` | POST | Trigger Claude-based enrichment for a film |
