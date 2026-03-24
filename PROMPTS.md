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

Read CLAUDE.md for full project context. Then read ALL of the following files to understand the current codebase:

- `database/schema.sql` — see the `award` and `stream_platform`/`film_exploitation` tables
- `database/seed_taxonomy.sql` — see the seeded streaming platforms
- `backend/app/services/tmdb_service.py` — current TMDB client
- `backend/app/services/tmdb_mapper.py` — current mapper output structure
- `backend/app/services/claude_enricher.py` — current enrichment prompt and output format
- `backend/app/services/taxonomy_config.py` — current taxonomy dimensions and reference examples
- `scripts/db_inserter.py` — current insertion logic (see what's missing)
- `scripts/data/reference_films_fallback.json` — current reference data structure
- `scripts/verify_db.py` — current verification queries

*(Full prompt preserved in previous conversation — see 'Implementation part 1' chat history)*

---

## Step 5 Prompt — Backend API (FastAPI)

Read CLAUDE.md for full project context. Then read PLAN.md for the Step 5 specification. Then read ALL of the following files to understand the current codebase:

- `database/schema.sql` — Full PostgreSQL DDL (all tables, columns, types, constraints, indexes)
- `database/seed_taxonomy.sql` — All lookup table values (you'll need these for taxonomy endpoints)
- `backend/requirements.txt` — Already installed: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic, python-dotenv, httpx
- `backend/app/services/tmdb_service.py` — Existing TMDB client (understand the async pattern used)
- `scripts/db_inserter.py` — Existing DB insertion logic (understand how junction tables are populated — the API's create/update endpoints must follow the same pattern)
- `.env` — DATABASE_URL format: `postgresql+asyncpg://postgres:postgre26@localhost:5432/film_database`

### Goal

Implement the complete FastAPI backend API for the film database. This API will be consumed by a React frontend (step 6). It must expose film data with rich multi-filter support, CRUD operations, taxonomy lists for filter dropdowns, person filmography, and basic stats.

### A. Database Connection — `backend/app/database.py`

Create async database connection management:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

### B. SQLAlchemy ORM Models — `backend/app/models/__init__.py`

Create ORM models that mirror `database/schema.sql` exactly. **Read schema.sql carefully** — every table, every column, every foreign key.

Key tables to model (non-exhaustive, read schema.sql for the complete list):
- `film` — Central entity (all columns including budget, revenue, vu, poster_url, etc.)
- `person`, `person_job`, `crew`, `casting`
- `studio`, `production`
- `language`, `film_language` (has `film_title`, `is_original`, `has_dubbing`)
- `category`, `film_genre`
- `cinema_type`, `film_technique`
- `cultural_movement`, `film_movement`
- `geography`, `film_set_place` (has `place_type` and `environment`)
- `time_period`, `film_period`
- `place_context`, `film_place`
- `theme_context`, `film_theme`
- `characters_type`, `film_characters`
- `character_context`, `film_character_context`
- `atmosphere`, `film_atmosphere`
- `message_conveyed`, `film_message`
- `motivation`, `film_motivation`
- `source`, `film_origin`
- `stream_platform`, `film_exploitation`
- `award`
- `film_sequel`

Use SQLAlchemy 2.0 declarative style with `mapped_column`. Use `relationship()` where it simplifies querying (especially for the film→junction→lookup pattern).

**Important:** Do NOT try to define every possible relationship — focus on the ones needed by the API (film detail page needs to load all junctions; person page needs to load their films).

### C. Pydantic Schemas — `backend/app/schemas/`

**`backend/app/schemas/film.py`:**

```python
# FilmListItem — compact, for grid display
class FilmListItem(BaseModel):
    film_id: int
    original_title: str
    first_release_date: date | None
    duration: int | None
    poster_url: str | None
    vu: bool
    categories: list[str]  # Just the names, e.g. ["Drama", "Thriller"]
    # Maybe director name(s) for quick display

# FilmDetail — full, for detail page
class FilmDetail(BaseModel):
    film_id: int
    original_title: str
    duration: int | None
    color: bool
    first_release_date: date | None
    summary: str | None
    vu: bool
    poster_url: str | None
    backdrop_url: str | None
    imdb_id: str | None
    tmdb_id: int | None
    budget: int | None
    revenue: int | None
    titles: list[FilmTitle]           # All language titles
    categories: list[str]
    cinema_types: list[str]
    cultural_movements: list[str]
    themes: list[str]
    characters: list[str]
    character_contexts: list[str]
    motivations: list[str]
    atmospheres: list[str]
    messages: list[str]
    time_periods: list[str]
    place_contexts: list[str]
    set_places: list[FilmSetPlaceOut] # geography name + place_type + environment
    crew: list[CrewMember]            # person name + role
    cast: list[CastMember]            # person name + character + order
    studios: list[str]
    sources: list[SourceOut]          # type + title + author
    awards: list[AwardOut]            # festival + category + year + result
    streaming_platforms: list[str]
    sequels: list[FilmRelation]       # related film title + relation type

# FilmSearchParams — query parameters for GET /api/films
class FilmSearchParams(BaseModel):
    q: str | None = None              # Full-text search
    categories: list[str] | None = None
    themes: list[str] | None = None
    atmospheres: list[str] | None = None
    messages: list[str] | None = None
    characters: list[str] | None = None
    motivations: list[str] | None = None
    cinema_types: list[str] | None = None
    cultural_movements: list[str] | None = None
    time_periods: list[str] | None = None
    year_min: int | None = None
    year_max: int | None = None
    director: str | None = None
    country: str | None = None
    vu: bool | None = None
    page: int = 1
    per_page: int = 20
    sort_by: str = "year"             # year, title, duration, budget, revenue
    sort_order: str = "desc"          # asc, desc
```

**`backend/app/schemas/taxonomy.py`:**
```python
class TaxonomyItem(BaseModel):
    id: int
    name: str
    film_count: int | None = None  # Optional: how many films use this value

class TaxonomyList(BaseModel):
    dimension: str
    items: list[TaxonomyItem]
```

**`backend/app/schemas/person.py`:**
```python
class PersonSummary(BaseModel):
    person_id: int
    firstname: str | None
    lastname: str
    photo_url: str | None

class PersonDetail(PersonSummary):
    gender: str | None
    date_of_birth: date | None
    date_of_death: date | None
    nationality: str | None
    tmdb_id: int | None
    filmography: list[FilmographyEntry]  # film title + year + role(s)
```

### D. Film Router — `backend/app/routers/films.py`

This is the most complex router. Key endpoints:

**`GET /api/films`** — Paginated + filtered list.
- Accept all FilmSearchParams as query parameters. Use FastAPI's `Query()` for list params (e.g., `categories: list[str] | None = Query(None)`)
- Build the SQL dynamically: start with a base SELECT on film, then LEFT JOIN junction+lookup tables only for the dimensions that have active filters
- For each taxonomy filter, add a subquery: `film_id IN (SELECT film_id FROM film_genre fg JOIN category c ON fg.category_id = c.category_id WHERE c.category_name IN (:values))`
- For `director` filter: join through `crew` + `person` + `person_job` WHERE role_name = 'Director' AND (firstname || ' ' || lastname) ILIKE :director
- For `q` (full-text): search across `film.original_title`, all titles in `film_language`, `film.summary`, and person names in `casting`/`crew`
- For `year_min`/`year_max`: filter on `EXTRACT(YEAR FROM first_release_date)`
- Return: paginated response with `total`, `page`, `per_page`, `items: list[FilmListItem]`
- For each FilmListItem, include the category names (subquery or lateral join) and the director name

**`GET /api/films/{film_id}`** — Full detail.
- Single film with ALL related data loaded. This requires many JOINs or subqueries.
- **Approach:** First fetch the film row, then run separate queries for each junction dimension (categories, themes, cast, crew, awards, etc.). Assemble into FilmDetail.
- This is cleaner than one massive 20-JOIN query that would produce massive cartesian products.

**`POST /api/films`** — Create a new film.
- Accept a JSON body with film data + all taxonomy arrays.
- Follow the same insertion pattern as `scripts/db_inserter.py` — insert film first, get film_id, then insert all junctions.
- This endpoint will be used by the "Add Film" workflow (step 8).

**`PUT /api/films/{film_id}`** — Update a film.
- Accept partial updates. For junction tables: clear existing and re-insert (same approach as db_inserter).
- Only update fields that are present in the request body.

**`GET /api/stats`** — Basic database statistics.
- Film count total, count by decade, count by category (top 10), count by country (top 10), count seen vs unseen.

### E. Taxonomy Router — `backend/app/routers/taxonomy.py`

**`GET /api/taxonomy/{dimension}`** — List all values for a taxonomy dimension.

Supported dimensions and their corresponding tables:
- `categories` → `category` (category_id, category_name)
- `cinema_types` → `cinema_type` (cinema_type_id, type_name)
- `cultural_movements` → `cultural_movement` (movement_id, movement_name)
- `themes` → `theme_context` (theme_id, theme_name)
- `characters` → `characters_type` (character_type_id, type_name)
- `character_contexts` → `character_context` (context_id, context_name)
- `atmospheres` → `atmosphere` (atmosphere_id, atmosphere_name)
- `messages` → `message_conveyed` (message_id, message_name)
- `motivations` → `motivation` (motivation_id, motivation_name)
- `time_periods` → `time_period` (period_id, period_name)
- `place_contexts` → `place_context` (context_id, context_name)
- `streaming_platforms` → `stream_platform` (platform_id, platform_name)
- `person_jobs` → `person_job` (job_id, role_name)

Each should return the list of values with their IDs, sorted alphabetically. Optionally include `film_count` (how many films are tagged with each value) — this is useful for the frontend to show counts in filter sidebars.

Use a mapping dict to route the dimension name to the correct table/column names, then build the query dynamically. Do NOT create 15 separate endpoints.

### F. Person Router — `backend/app/routers/persons.py`

**`GET /api/persons/{person_id}`** — Person detail with filmography.
- Return person info + list of films they appear in (as cast or crew), with their role/character for each film.

**`GET /api/persons/search?q=kubrick`** — Search persons by name.
- ILIKE search on firstname + lastname. Return list of PersonSummary.

### G. App Entry Point — `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.database import engine
from backend.app.routers import films, taxonomy, persons

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: engine pool is created on first use, nothing special needed
    yield
    # Shutdown: dispose engine pool
    await engine.dispose()

app = FastAPI(
    title="Film Database API",
    description="Personal film database with rich taxonomy classification",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(films.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(persons.router, prefix="/api")
```

### H. Important Technical Notes

1. **Import paths:** The project runs from the repo root. Use `backend.app.xxx` import paths. The uvicorn command is `uvicorn backend.app.main:app --reload` from the project root.

2. **Async sessions:** Every endpoint should use `db: AsyncSession = Depends(get_db)`. Use `await db.execute(text(...))` for raw SQL and `await db.execute(select(...))` for ORM queries.

3. **Don't over-engineer the ORM:** For the complex filtered list query, raw SQL via `text()` is simpler and faster than trying to build it with SQLAlchemy's ORM query builder across 15 junction tables. Use ORM for simple CRUD, raw SQL for the complex filter query.

4. **Pagination response shape:**
```json
{
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3,
  "items": [...]
}
```

5. **Error handling:** Return proper HTTP status codes — 404 for film/person not found, 400 for invalid filter params, 422 for validation errors (Pydantic handles this automatically).

6. **Add `__init__.py`** files in `backend/app/models/`, `backend/app/schemas/`, `backend/app/routers/` (they may already exist but be empty).

7. **No authentication** for now — this is a personal, single-user application.

### Validation

After all files are created:

1. Run `uvicorn backend.app.main:app --reload` from the project root — it should start without import errors
2. Open `http://localhost:8000/docs` — Swagger UI should display all endpoints
3. Test `GET /api/films` — should return the 3 seeded reference films
4. Test `GET /api/films?categories=Drama` — should return films tagged as Drama
5. Test `GET /api/films/1` — should return full film detail with all taxonomy data populated
6. Test `GET /api/taxonomy/categories` — should return all seeded category values
7. Test `GET /api/taxonomy/themes` — should return all seeded theme values
8. Test `GET /api/persons/search?q=kubrick` — should find Stanley Kubrick

Do NOT run the server yourself — just ensure the code is correct and all imports resolve. The user will test manually.

---
