"""
Film API endpoints — list (paginated + filtered), detail, search, create, update, stats.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.film import (
    AwardOut,
    CastMember,
    CrewMember,
    FilmCreate,
    FilmDetail,
    FilmListItem,
    FilmRelation,
    FilmSetPlaceOut,
    FilmTitle,
    FilmUpdate,
    PaginatedFilms,
    SourceOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["films"])


# =============================================================================
# GET /api/films — Paginated + filtered list
# =============================================================================


@router.get("/films", response_model=PaginatedFilms)
async def list_films(
    q: str | None = None,
    categories: list[str] | None = Query(None),
    themes: list[str] | None = Query(None),
    atmospheres: list[str] | None = Query(None),
    messages: list[str] | None = Query(None),
    characters: list[str] | None = Query(None),
    character_contexts: list[str] | None = Query(None),
    motivations: list[str] | None = Query(None),
    cinema_types: list[str] | None = Query(None),
    cultural_movements: list[str] | None = Query(None),
    time_periods: list[str] | None = Query(None),
    place_contexts: list[str] | None = Query(None),
    year_min: int | None = None,
    year_max: int | None = None,
    director: str | None = None,
    location: str | None = None,
    country: str | None = None,
    language: str | None = None,
    vu: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("year", pattern="^(year|title|duration|budget|revenue)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {}
    where_clauses: list[str] = []

    # Taxonomy filters via subqueries
    _taxonomy_filters = [
        (categories, "film_genre", "category_id", "category", "category_id", "category_name"),
        (themes, "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
        (atmospheres, "film_atmosphere", "atmosphere_id", "atmosphere", "atmosphere_id", "atmosphere_name"),
        (messages, "film_message", "message_id", "message_conveyed", "message_id", "message_name"),
        (characters, "film_characters", "character_type_id", "characters_type", "character_type_id", "type_name"),
        (motivations, "film_motivation", "motivation_id", "motivation_relation", "motivation_id", "motivation_name"),
        (cinema_types, "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        (cultural_movements, "film_movement", "movement_id", "cultural_movement", "movement_id", "movement_name"),
        (time_periods, "film_period", "time_context_id", "time_context", "time_context_id", "time_period"),
        (character_contexts, "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
        (place_contexts, "film_place", "place_context_id", "place_context", "place_context_id", "environment"),
    ]

    for i, (values, junc_table, junc_fk, lookup_table, lookup_pk, lookup_name) in enumerate(_taxonomy_filters):
        if not values:
            continue
        param_key = f"tax_{i}"
        where_clauses.append(
            f"""f.film_id IN (
                SELECT jt.film_id FROM {junc_table} jt
                JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                WHERE lt.{lookup_name} = ANY(:{param_key})
            )"""
        )
        params[param_key] = values

    # Director filter
    if director:
        where_clauses.append(
            """f.film_id IN (
                SELECT c.film_id FROM crew c
                JOIN person p ON c.person_id = p.person_id
                JOIN person_job pj ON c.job_id = pj.job_id
                WHERE pj.role_name = 'Director'
                  AND (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE :director
            )"""
        )
        params["director"] = f"%{director}%"

    # Location filter (replaces old country filter; country kept as alias)
    loc = location or country
    if loc:
        where_clauses.append(
            """f.film_id IN (
                SELECT fsp.film_id FROM film_set_place fsp
                JOIN geography g ON fsp.geography_id = g.geography_id
                WHERE g.country ILIKE :location
                   OR g.state_city ILIKE :location
                   OR g.continent ILIKE :location
            )"""
        )
        params["location"] = f"%{loc}%"

    # Language filter (original language)
    if language:
        where_clauses.append(
            """f.film_id IN (
                SELECT fl.film_id FROM film_language fl
                JOIN language l ON fl.language_id = l.language_id
                WHERE fl.is_original = TRUE
                  AND l.language_name ILIKE :language
            )"""
        )
        params["language"] = f"%{language}%"

    # Year range
    if year_min is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) >= :year_min")
        params["year_min"] = year_min
    if year_max is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) <= :year_max")
        params["year_max"] = year_max

    # Vu filter
    if vu is not None:
        where_clauses.append("f.vu = :vu")
        params["vu"] = vu

    # Full-text search
    if q:
        where_clauses.append(
            """(
                f.original_title ILIKE :q
                OR f.summary ILIKE :q
                OR f.film_id IN (
                    SELECT fl.film_id FROM film_language fl WHERE fl.film_title ILIKE :q
                )
                OR f.film_id IN (
                    SELECT ca.film_id FROM casting ca
                    JOIN person p ON ca.person_id = p.person_id
                    WHERE (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE :q
                )
                OR f.film_id IN (
                    SELECT cr.film_id FROM crew cr
                    JOIN person p ON cr.person_id = p.person_id
                    WHERE (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE :q
                )
            )"""
        )
        params["q"] = f"%{q}%"

    where_sql = (" AND ".join(where_clauses)) if where_clauses else "TRUE"

    # Sort mapping
    sort_col_map = {
        "year": "f.first_release_date",
        "title": "f.original_title",
        "duration": "f.duration",
        "budget": "f.budget",
        "revenue": "f.revenue",
    }
    sort_col = sort_col_map[sort_by]
    order = sort_order.upper()

    # Count query
    count_sql = f"SELECT COUNT(*) FROM film f WHERE {where_sql}"
    result = await db.execute(text(count_sql), params)
    total = result.scalar_one()

    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    # Main query
    list_sql = f"""
        SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
               f.poster_url, f.vu
        FROM film f
        WHERE {where_sql}
        ORDER BY {sort_col} {order} NULLS LAST, f.film_id ASC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = per_page
    params["offset"] = offset

    result = await db.execute(text(list_sql), params)
    rows = result.fetchall()

    # Gather film_ids for batch loading categories and directors
    film_ids = [r[0] for r in rows]
    items: list[FilmListItem] = []

    if film_ids:
        # Batch load categories
        cat_sql = """
            SELECT fg.film_id, c.category_name
            FROM film_genre fg
            JOIN category c ON fg.category_id = c.category_id
            WHERE fg.film_id = ANY(:film_ids) AND c.historic_subcategory_name IS NULL
            ORDER BY fg.film_id, c.category_name
        """
        cat_result = await db.execute(text(cat_sql), {"film_ids": film_ids})
        cat_map: dict[int, list[str]] = {}
        for fid, cname in cat_result.fetchall():
            cat_map.setdefault(fid, []).append(cname)

        # Batch load directors
        dir_sql = """
            SELECT cr.film_id, COALESCE(p.firstname, '') || ' ' || p.lastname AS director_name
            FROM crew cr
            JOIN person p ON cr.person_id = p.person_id
            JOIN person_job pj ON cr.job_id = pj.job_id
            WHERE cr.film_id = ANY(:film_ids) AND pj.role_name = 'Director'
            ORDER BY cr.film_id
        """
        dir_result = await db.execute(text(dir_sql), {"film_ids": film_ids})
        dir_map: dict[int, str] = {}
        for fid, dname in dir_result.fetchall():
            if fid not in dir_map:
                dir_map[fid] = dname
            else:
                dir_map[fid] += f", {dname}"

        for r in rows:
            fid = r[0]
            items.append(
                FilmListItem(
                    film_id=fid,
                    original_title=r[1],
                    first_release_date=r[2],
                    duration=r[3],
                    poster_url=r[4],
                    vu=r[5] or False,
                    categories=cat_map.get(fid, []),
                    director=dir_map.get(fid),
                )
            )

    return PaginatedFilms(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        items=items,
    )


# =============================================================================
# GET /api/films/{film_id} — Full detail
# =============================================================================


@router.get("/films/{film_id}", response_model=FilmDetail)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    # Core film
    result = await db.execute(
        text("SELECT * FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    film = result.mappings().first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")

    # Helper to load simple taxonomy names
    async def load_names(sql: str) -> list[str]:
        r = await db.execute(text(sql), {"fid": film_id})
        return [row[0] for row in r.fetchall()]

    # Titles
    title_rows = await db.execute(
        text("""
            SELECT l.language_code, l.language_name, fl.film_title, fl.is_original
            FROM film_language fl
            JOIN language l ON fl.language_id = l.language_id
            WHERE fl.film_id = :fid
            ORDER BY fl.is_original DESC
        """),
        {"fid": film_id},
    )
    titles = [
        FilmTitle(language_code=r[0], language_name=r[1], title=r[2], is_original=r[3])
        for r in title_rows.fetchall()
    ]

    # Categories (only base categories, no subcategory rows)
    categories = await load_names(
        "SELECT DISTINCT c.category_name FROM film_genre fg "
        "JOIN category c ON fg.category_id = c.category_id "
        "WHERE fg.film_id = :fid ORDER BY c.category_name"
    )

    cinema_types = await load_names(
        "SELECT ct.technique_name FROM film_technique ft "
        "JOIN cinema_type ct ON ft.cinema_type_id = ct.cinema_type_id "
        "WHERE ft.film_id = :fid ORDER BY ct.technique_name"
    )

    cultural_movements = await load_names(
        "SELECT cm.movement_name FROM film_movement fm "
        "JOIN cultural_movement cm ON fm.movement_id = cm.movement_id "
        "WHERE fm.film_id = :fid ORDER BY cm.movement_name"
    )

    themes_list = await load_names(
        "SELECT tc.theme_name FROM film_theme fth "
        "JOIN theme_context tc ON fth.theme_context_id = tc.theme_context_id "
        "WHERE fth.film_id = :fid ORDER BY tc.theme_name"
    )

    characters_list = await load_names(
        "SELECT ct.type_name FROM film_characters fc "
        "JOIN characters_type ct ON fc.character_type_id = ct.character_type_id "
        "WHERE fc.film_id = :fid ORDER BY ct.type_name"
    )

    character_contexts_list = await load_names(
        "SELECT cc.context_name FROM film_character_context fcc "
        "JOIN character_context cc ON fcc.character_context_id = cc.character_context_id "
        "WHERE fcc.film_id = :fid ORDER BY cc.context_name"
    )

    motivations_list = await load_names(
        "SELECT mr.motivation_name FROM film_motivation fm "
        "JOIN motivation_relation mr ON fm.motivation_id = mr.motivation_id "
        "WHERE fm.film_id = :fid ORDER BY mr.motivation_name"
    )

    atmospheres_list = await load_names(
        "SELECT a.atmosphere_name FROM film_atmosphere fa "
        "JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id "
        "WHERE fa.film_id = :fid ORDER BY a.atmosphere_name"
    )

    messages_list = await load_names(
        "SELECT mc.message_name FROM film_message fmsg "
        "JOIN message_conveyed mc ON fmsg.message_id = mc.message_id "
        "WHERE fmsg.film_id = :fid ORDER BY mc.message_name"
    )

    time_periods_list = await load_names(
        "SELECT tc.time_period FROM film_period fp "
        "JOIN time_context tc ON fp.time_context_id = tc.time_context_id "
        "WHERE fp.film_id = :fid ORDER BY tc.time_period"
    )

    place_contexts_list = await load_names(
        "SELECT pc.environment FROM film_place fpl "
        "JOIN place_context pc ON fpl.place_context_id = pc.place_context_id "
        "WHERE fpl.film_id = :fid ORDER BY pc.environment"
    )

    # Set places (geography)
    sp_rows = await db.execute(
        text("""
            SELECT g.continent, g.country, g.state_city, fsp.place_type
            FROM film_set_place fsp
            JOIN geography g ON fsp.geography_id = g.geography_id
            WHERE fsp.film_id = :fid
            ORDER BY g.continent, g.country
        """),
        {"fid": film_id},
    )
    set_places = [
        FilmSetPlaceOut(continent=r[0], country=r[1], state_city=r[2], place_type=r[3])
        for r in sp_rows.fetchall()
    ]

    # Crew
    crew_rows = await db.execute(
        text("""
            SELECT p.person_id, p.firstname, p.lastname, pj.role_name, p.photo_url
            FROM crew cr
            JOIN person p ON cr.person_id = p.person_id
            JOIN person_job pj ON cr.job_id = pj.job_id
            WHERE cr.film_id = :fid
            ORDER BY pj.role_name, p.lastname
        """),
        {"fid": film_id},
    )
    crew = [
        CrewMember(person_id=r[0], firstname=r[1], lastname=r[2], role=r[3], photo_url=r[4])
        for r in crew_rows.fetchall()
    ]

    # Cast
    cast_rows = await db.execute(
        text("""
            SELECT p.person_id, p.firstname, p.lastname, ca.character_name, ca.cast_order, p.photo_url
            FROM casting ca
            JOIN person p ON ca.person_id = p.person_id
            WHERE ca.film_id = :fid
            ORDER BY ca.cast_order NULLS LAST
        """),
        {"fid": film_id},
    )
    cast = [
        CastMember(person_id=r[0], firstname=r[1], lastname=r[2], character_name=r[3], cast_order=r[4], photo_url=r[5])
        for r in cast_rows.fetchall()
    ]

    # Studios
    studios = await load_names(
        "SELECT s.studio_name FROM production pr "
        "JOIN studio s ON pr.studio_id = s.studio_id "
        "WHERE pr.film_id = :fid ORDER BY s.studio_name"
    )

    # Sources
    src_rows = await db.execute(
        text("""
            SELECT s.source_type, s.source_title, s.author
            FROM film_origin fo
            JOIN source s ON fo.source_id = s.source_id
            WHERE fo.film_id = :fid
        """),
        {"fid": film_id},
    )
    sources = [
        SourceOut(source_type=r[0], source_title=r[1], author=r[2])
        for r in src_rows.fetchall()
    ]

    # Awards
    award_rows = await db.execute(
        text("""
            SELECT festival_name, category, award_year, result
            FROM award WHERE film_id = :fid
            ORDER BY award_year, festival_name
        """),
        {"fid": film_id},
    )
    awards = [
        AwardOut(festival_name=r[0], category=r[1], year=r[2], result=r[3])
        for r in award_rows.fetchall()
    ]

    # Streaming platforms
    streaming = await load_names(
        "SELECT sp.platform_name FROM film_exploitation fe "
        "JOIN stream_platform sp ON fe.platform_id = sp.platform_id "
        "WHERE fe.film_id = :fid ORDER BY sp.platform_name"
    )

    # Sequels / related films
    seq_rows = await db.execute(
        text("""
            SELECT fs.related_film_id, f2.original_title, fs.relation_type
            FROM film_sequel fs
            JOIN film f2 ON fs.related_film_id = f2.film_id
            WHERE fs.film_id = :fid
            UNION
            SELECT fs.film_id, f2.original_title, fs.relation_type
            FROM film_sequel fs
            JOIN film f2 ON fs.film_id = f2.film_id
            WHERE fs.related_film_id = :fid
        """),
        {"fid": film_id},
    )
    sequels = [
        FilmRelation(related_film_id=r[0], related_film_title=r[1], relation_type=r[2])
        for r in seq_rows.fetchall()
    ]

    return FilmDetail(
        film_id=film["film_id"],
        original_title=film["original_title"],
        duration=film["duration"],
        color=film["color"] if film["color"] is not None else True,
        first_release_date=film["first_release_date"],
        summary=film["summary"],
        vu=film["vu"] or False,
        poster_url=film["poster_url"],
        backdrop_url=film["backdrop_url"],
        imdb_id=film["imdb_id"],
        tmdb_id=film["tmdb_id"],
        budget=film["budget"],
        revenue=film["revenue"],
        titles=titles,
        categories=categories,
        cinema_types=cinema_types,
        cultural_movements=cultural_movements,
        themes=themes_list,
        characters=characters_list,
        character_contexts=character_contexts_list,
        motivations=motivations_list,
        atmospheres=atmospheres_list,
        messages=messages_list,
        time_periods=time_periods_list,
        place_contexts=place_contexts_list,
        set_places=set_places,
        crew=crew,
        cast=cast,
        studios=studios,
        sources=sources,
        awards=awards,
        streaming_platforms=streaming,
        sequels=sequels,
    )


# =============================================================================
# POST /api/films — Create a new film
# =============================================================================


@router.post("/films", response_model=dict, status_code=201)
async def create_film(film_data: FilmCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new film with all relations. Follows the same insertion pattern
    as scripts/db_inserter.py.
    """
    film = film_data.film
    enrichment = film_data.enrichment
    tmdb_id = film.get("tmdb_id")

    if not tmdb_id:
        raise HTTPException(status_code=400, detail="tmdb_id is required")

    # Check if film already exists
    result = await db.execute(
        text("SELECT film_id FROM film WHERE tmdb_id = :tmdb_id"),
        {"tmdb_id": tmdb_id},
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Film with tmdb_id={tmdb_id} already exists")

    # Insert film
    result = await db.execute(
        text("""
            INSERT INTO film (
                original_title, duration, color, first_release_date, summary,
                poster_url, backdrop_url, imdb_id, tmdb_id, budget, revenue
            ) VALUES (
                :original_title, :duration, :color, :first_release_date, :summary,
                :poster_url, :backdrop_url, :imdb_id, :tmdb_id, :budget, :revenue
            ) RETURNING film_id
        """),
        {
            "original_title": film.get("original_title"),
            "duration": film.get("duration"),
            "color": film.get("color", True),
            "first_release_date": film.get("first_release_date"),
            "summary": film.get("summary"),
            "poster_url": film.get("poster_url"),
            "backdrop_url": film.get("backdrop_url"),
            "imdb_id": film.get("imdb_id"),
            "tmdb_id": tmdb_id,
            "budget": film.get("budget"),
            "revenue": film.get("revenue"),
        },
    )
    film_id = result.scalar_one()

    # Insert titles
    for title_entry in film_data.titles:
        code = title_entry.get("language_code", "")
        title_text = title_entry.get("title", "")
        if not code or not title_text:
            continue
        r = await db.execute(
            text("SELECT language_id FROM language WHERE language_code = :code"),
            {"code": code},
        )
        lang_id = r.scalar_one_or_none()
        if not lang_id:
            r = await db.execute(
                text("""
                    INSERT INTO language (language_code, language_name)
                    VALUES (:code, :name)
                    ON CONFLICT (language_code) DO UPDATE SET language_name = EXCLUDED.language_name
                    RETURNING language_id
                """),
                {"code": code, "name": code},
            )
            lang_id = r.scalar_one()
        await db.execute(
            text("""
                INSERT INTO film_language (film_id, language_id, film_title, is_original, has_dubbing)
                VALUES (:fid, :lid, :title, :is_original, FALSE)
                ON CONFLICT DO NOTHING
            """),
            {
                "fid": film_id, "lid": lang_id,
                "title": title_text,
                "is_original": title_entry.get("is_original", False),
            },
        )

    # Insert taxonomy junctions from enrichment
    taxonomy_junctions = [
        ("categories", "film_genre", "category_id", "category", "category_id", "category_name"),
        ("cinema_type", "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        ("cultural_movement", "film_movement", "movement_id", "cultural_movement", "movement_id", "movement_name"),
        ("themes", "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
        ("characters_type", "film_characters", "character_type_id", "characters_type", "character_type_id", "type_name"),
        ("character_context", "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
        ("atmosphere", "film_atmosphere", "atmosphere_id", "atmosphere", "atmosphere_id", "atmosphere_name"),
        ("motivations", "film_motivation", "motivation_id", "motivation_relation", "motivation_id", "motivation_name"),
        ("message", "film_message", "message_id", "message_conveyed", "message_id", "message_name"),
        ("time_context", "film_period", "time_context_id", "time_context", "time_context_id", "time_period"),
        ("place_environment", "film_place", "place_context_id", "place_context", "place_context_id", "environment"),
    ]

    for enr_key, junc_table, junc_fk, lookup_table, lookup_pk, lookup_name in taxonomy_junctions:
        values = enrichment.get(enr_key, [])
        if not isinstance(values, list):
            continue
        for val in values:
            if not val or (isinstance(val, str) and val.startswith("[NEW]")):
                continue
            r = await db.execute(
                text(f"SELECT {lookup_pk} FROM {lookup_table} WHERE {lookup_name} = :name"),
                {"name": val},
            )
            lid = r.scalar_one_or_none()
            if lid:
                await db.execute(
                    text(f"INSERT INTO {junc_table} (film_id, {junc_fk}) VALUES (:fid, :lid) ON CONFLICT DO NOTHING"),
                    {"fid": film_id, "lid": lid},
                )

    # Insert awards
    for award in enrichment.get("awards", []):
        if not isinstance(award, dict) or not award.get("festival_name"):
            continue
        if award.get("result") not in ("won", "nominated"):
            continue
        await db.execute(
            text("""
                INSERT INTO award (film_id, festival_name, category, award_year, result)
                VALUES (:fid, :festival, :category, :year, :result)
            """),
            {
                "fid": film_id,
                "festival": award["festival_name"],
                "category": award.get("category"),
                "year": award.get("year"),
                "result": award["result"],
            },
        )

    # Insert streaming platforms
    for platform_name in film_data.streaming_platforms:
        if not platform_name:
            continue
        r = await db.execute(
            text("SELECT platform_id FROM stream_platform WHERE platform_name = :name"),
            {"name": platform_name},
        )
        pid = r.scalar_one_or_none()
        if pid:
            await db.execute(
                text("INSERT INTO film_exploitation (film_id, platform_id) VALUES (:fid, :pid) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "pid": pid},
            )

    # Insert crew
    for member in film_data.crew:
        person_id = await _find_or_create_person(db, member)
        role = member.get("role")
        if not role:
            continue
        r = await db.execute(
            text("SELECT job_id FROM person_job WHERE role_name = :role"),
            {"role": role},
        )
        job_id = r.scalar_one_or_none()
        if job_id:
            await db.execute(
                text("INSERT INTO crew (film_id, person_id, job_id) VALUES (:fid, :pid, :jid) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "pid": person_id, "jid": job_id},
            )

    # Insert cast
    for member in film_data.cast:
        person_id = await _find_or_create_person(db, member)
        await db.execute(
            text("""
                INSERT INTO casting (film_id, person_id, character_name, cast_order)
                VALUES (:fid, :pid, :char, :ord)
            """),
            {
                "fid": film_id,
                "pid": person_id,
                "char": member.get("character_name", ""),
                "ord": member.get("cast_order"),
            },
        )

    # Insert studios
    for studio in film_data.studios:
        name = studio.get("name")
        if not name:
            continue
        r = await db.execute(
            text("SELECT studio_id FROM studio WHERE studio_name = :name"),
            {"name": name},
        )
        sid = r.scalar_one_or_none()
        if not sid:
            r = await db.execute(
                text("INSERT INTO studio (studio_name, country_name) VALUES (:name, :country) RETURNING studio_id"),
                {"name": name, "country": studio.get("country", "")},
            )
            sid = r.scalar_one()
        await db.execute(
            text("INSERT INTO production (film_id, studio_id) VALUES (:fid, :sid) ON CONFLICT DO NOTHING"),
            {"fid": film_id, "sid": sid},
        )

    # Insert source
    source = enrichment.get("source")
    if isinstance(source, dict) and source.get("type"):
        r = await db.execute(
            text("INSERT INTO source (source_type, source_title, author) VALUES (:type, :title, :author) RETURNING source_id"),
            {"type": source["type"], "title": source.get("title"), "author": source.get("author")},
        )
        source_id = r.scalar_one()
        await db.execute(
            text("INSERT INTO film_origin (film_id, source_id) VALUES (:fid, :sid) ON CONFLICT DO NOTHING"),
            {"fid": film_id, "sid": source_id},
        )

    # Insert geography
    for geo in enrichment.get("geography", []):
        if not isinstance(geo, dict):
            continue
        place_type = geo.get("place_type", "diegetic")
        if place_type not in ("diegetic", "shooting", "fictional"):
            place_type = "diegetic"
        r = await db.execute(
            text("""
                SELECT geography_id FROM geography
                WHERE continent IS NOT DISTINCT FROM :continent
                  AND country IS NOT DISTINCT FROM :country
                  AND state_city IS NOT DISTINCT FROM :state_city
            """),
            {"continent": geo.get("continent"), "country": geo.get("country"), "state_city": geo.get("state_city")},
        )
        geo_id = r.scalar_one_or_none()
        if not geo_id:
            r = await db.execute(
                text("""
                    INSERT INTO geography (continent, country, state_city)
                    VALUES (:continent, :country, :state_city)
                    ON CONFLICT (continent, country, state_city) DO UPDATE SET continent = EXCLUDED.continent
                    RETURNING geography_id
                """),
                {"continent": geo.get("continent"), "country": geo.get("country"), "state_city": geo.get("state_city")},
            )
            geo_id = r.scalar_one()
        await db.execute(
            text("INSERT INTO film_set_place (film_id, geography_id, place_type) VALUES (:fid, :gid, :pt) ON CONFLICT DO NOTHING"),
            {"fid": film_id, "gid": geo_id, "pt": place_type},
        )

    await db.commit()
    return {"film_id": film_id, "message": "Film created successfully"}


# =============================================================================
# PUT /api/films/{film_id} — Update a film
# =============================================================================


@router.put("/films/{film_id}", response_model=dict)
async def update_film(film_id: int, update: FilmUpdate, db: AsyncSession = Depends(get_db)):
    # Check film exists
    result = await db.execute(
        text("SELECT film_id FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")

    # Update core film fields
    core_fields = {
        "original_title": update.original_title,
        "duration": update.duration,
        "color": update.color,
        "first_release_date": update.first_release_date,
        "summary": update.summary,
        "vu": update.vu,
        "poster_url": update.poster_url,
        "backdrop_url": update.backdrop_url,
        "budget": update.budget,
        "revenue": update.revenue,
    }
    set_clauses = []
    params: dict = {"fid": film_id}
    for key, value in core_fields.items():
        if value is not None:
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

    if set_clauses:
        await db.execute(
            text(f"UPDATE film SET {', '.join(set_clauses)} WHERE film_id = :fid"),
            params,
        )

    # Update taxonomy junctions (clear and re-insert pattern)
    junction_updates = [
        (update.categories, "film_genre", "category_id", "category", "category_id", "category_name"),
        (update.cinema_types, "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        (update.cultural_movements, "film_movement", "movement_id", "cultural_movement", "movement_id", "movement_name"),
        (update.themes, "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
        (update.characters, "film_characters", "character_type_id", "characters_type", "character_type_id", "type_name"),
        (update.character_contexts, "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
        (update.motivations, "film_motivation", "motivation_id", "motivation_relation", "motivation_id", "motivation_name"),
        (update.atmospheres, "film_atmosphere", "atmosphere_id", "atmosphere", "atmosphere_id", "atmosphere_name"),
        (update.messages, "film_message", "message_id", "message_conveyed", "message_id", "message_name"),
        (update.time_periods, "film_period", "time_context_id", "time_context", "time_context_id", "time_period"),
        (update.place_contexts, "film_place", "place_context_id", "place_context", "place_context_id", "environment"),
    ]

    for values, junc_table, junc_fk, lookup_table, lookup_pk, lookup_name in junction_updates:
        if values is None:
            continue
        # Clear existing
        await db.execute(text(f"DELETE FROM {junc_table} WHERE film_id = :fid"), {"fid": film_id})
        # Re-insert
        for val in values:
            if not val:
                continue
            r = await db.execute(
                text(f"SELECT {lookup_pk} FROM {lookup_table} WHERE {lookup_name} = :name"),
                {"name": val},
            )
            lid = r.scalar_one_or_none()
            if lid:
                await db.execute(
                    text(f"INSERT INTO {junc_table} (film_id, {junc_fk}) VALUES (:fid, :lid) ON CONFLICT DO NOTHING"),
                    {"fid": film_id, "lid": lid},
                )

    # Streaming platforms
    if update.streaming_platforms is not None:
        await db.execute(text("DELETE FROM film_exploitation WHERE film_id = :fid"), {"fid": film_id})
        for pname in update.streaming_platforms:
            if not pname:
                continue
            r = await db.execute(
                text("SELECT platform_id FROM stream_platform WHERE platform_name = :name"),
                {"name": pname},
            )
            pid = r.scalar_one_or_none()
            if pid:
                await db.execute(
                    text("INSERT INTO film_exploitation (film_id, platform_id) VALUES (:fid, :pid) ON CONFLICT DO NOTHING"),
                    {"fid": film_id, "pid": pid},
                )

    await db.commit()
    return {"film_id": film_id, "message": "Film updated successfully"}


# =============================================================================
# GET /api/stats — Database statistics
# =============================================================================


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    stats: dict = {}

    # Total films
    r = await db.execute(text("SELECT COUNT(*) FROM film"))
    stats["total_films"] = r.scalar_one()

    # Seen vs unseen
    r = await db.execute(text("SELECT COUNT(*) FROM film WHERE vu = TRUE"))
    stats["seen"] = r.scalar_one()
    stats["unseen"] = stats["total_films"] - stats["seen"]

    # By decade
    r = await db.execute(text("""
        SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
               COUNT(*) AS count
        FROM film
        WHERE first_release_date IS NOT NULL
        GROUP BY decade
        ORDER BY decade
    """))
    stats["by_decade"] = [{"decade": int(row[0]), "count": row[1]} for row in r.fetchall()]

    # Top 10 categories
    r = await db.execute(text("""
        SELECT c.category_name, COUNT(*) AS count
        FROM film_genre fg
        JOIN category c ON fg.category_id = c.category_id
        WHERE c.historic_subcategory_name IS NULL
        GROUP BY c.category_name
        ORDER BY count DESC
        LIMIT 10
    """))
    stats["top_categories"] = [{"name": row[0], "count": row[1]} for row in r.fetchall()]

    # Top 10 countries
    r = await db.execute(text("""
        SELECT g.country, COUNT(DISTINCT fsp.film_id) AS count
        FROM film_set_place fsp
        JOIN geography g ON fsp.geography_id = g.geography_id
        WHERE g.country IS NOT NULL
        GROUP BY g.country
        ORDER BY count DESC
        LIMIT 10
    """))
    stats["top_countries"] = [{"name": row[0], "count": row[1]} for row in r.fetchall()]

    return stats


# =============================================================================
# Helper: find or create person
# =============================================================================


async def _find_or_create_person(db: AsyncSession, person: dict) -> int:
    tmdb_id = person.get("tmdb_id")
    if tmdb_id:
        r = await db.execute(
            text("SELECT person_id FROM person WHERE tmdb_id = :tmdb_id"),
            {"tmdb_id": tmdb_id},
        )
        existing = r.scalar_one_or_none()
        if existing:
            return existing

    r = await db.execute(
        text("""
            INSERT INTO person (firstname, lastname, tmdb_id, photo_url)
            VALUES (:firstname, :lastname, :tmdb_id, :photo_url)
            ON CONFLICT (tmdb_id) DO UPDATE SET
                firstname = EXCLUDED.firstname,
                lastname = EXCLUDED.lastname,
                photo_url = COALESCE(EXCLUDED.photo_url, person.photo_url)
            RETURNING person_id
        """),
        {
            "firstname": person.get("firstname", ""),
            "lastname": person.get("lastname", ""),
            "tmdb_id": tmdb_id,
            "photo_url": person.get("photo_url"),
        },
    )
    return r.scalar_one()
