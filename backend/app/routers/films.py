"""
Film API endpoints — list (paginated + filtered), detail, search, create, update, stats.
"""

import asyncio
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import UserInfo, get_current_user, require_admin
from backend.app.database import engine, get_db
from backend.app.tier_config import (
    TIER_ALLOWED_DIMENSIONS,
    TIER_CAN_USE_OR_NOT,
    TIER_MAX_FILTERS,
    TIER_DIMENSION_MAX_SORT_ORDER,
)
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
    SimilarFilm,
    SimilarFilmsResponse,
    SourceOut,
    UserFilmStatus,
)
from backend.app.services import recommender

logger = logging.getLogger(__name__)

router = APIRouter(tags=["films"])


# =============================================================================
# GET /api/films — Paginated + filtered list
# =============================================================================


@router.get("/films", response_model=PaginatedFilms)
async def list_films(
    q: str | None = None,
    categories: list[str] | None = Query(None),
    categories_not: list[str] | None = Query(None),
    categories_mode: str | None = Query(None, pattern="^(or|and)$"),
    themes: list[str] | None = Query(None),
    themes_not: list[str] | None = Query(None),
    themes_mode: str | None = Query(None, pattern="^(or|and)$"),
    atmospheres: list[str] | None = Query(None),
    atmospheres_not: list[str] | None = Query(None),
    atmospheres_mode: str | None = Query(None, pattern="^(or|and)$"),
    messages: list[str] | None = Query(None),
    messages_not: list[str] | None = Query(None),
    messages_mode: str | None = Query(None, pattern="^(or|and)$"),
    characters: list[str] | None = Query(None),
    characters_not: list[str] | None = Query(None),
    characters_mode: str | None = Query(None, pattern="^(or|and)$"),
    motivations: list[str] | None = Query(None),
    motivations_not: list[str] | None = Query(None),
    motivations_mode: str | None = Query(None, pattern="^(or|and)$"),
    cinema_types: list[str] | None = Query(None),
    cinema_types_not: list[str] | None = Query(None),
    cinema_types_mode: str | None = Query(None, pattern="^(or|and)$"),
    time_periods: list[str] | None = Query(None),
    time_periods_not: list[str] | None = Query(None),
    time_periods_mode: str | None = Query(None, pattern="^(or|and)$"),
    place_contexts: list[str] | None = Query(None),
    place_contexts_not: list[str] | None = Query(None),
    place_contexts_mode: str | None = Query(None, pattern="^(or|and)$"),
    studios: list[str] | None = Query(None),
    studios_not: list[str] | None = Query(None),
    studios_mode: str | None = Query(None, pattern="^(or|and)$"),
    year_min: int | None = None,
    year_max: int | None = None,
    director: str | None = None,
    location: str | None = None,
    country: str | None = None,
    language: str | None = None,
    source: str | None = None,
    seen: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("year", pattern="^(year|title|duration|budget|revenue|popularity|random)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    params: dict = {}
    where_clauses: list[str] = []

    # --- Tier-based filter validation ---
    tier = user.tier if user else "anonymous"
    allowed_dims = TIER_ALLOWED_DIMENSIONS.get(tier, TIER_ALLOWED_DIMENSIONS["anonymous"])

    # Silently clear disallowed dimensions
    dim_var_map: dict[str, str] = {
        "categories": "categories", "themes": "themes", "atmospheres": "atmospheres",
        "messages": "messages", "characters": "characters", "motivations": "motivations",
        "cinema_types": "cinema_types", "time_periods": "time_periods",
        "place_contexts": "place_contexts", "studios": "studios",
    }
    if "categories" not in allowed_dims:
        categories = None; categories_not = None
    if "themes" not in allowed_dims:
        themes = None; themes_not = None
    if "atmospheres" not in allowed_dims:
        atmospheres = None; atmospheres_not = None
    if "messages" not in allowed_dims:
        messages = None; messages_not = None
    if "characters" not in allowed_dims:
        characters = None; characters_not = None
    if "motivations" not in allowed_dims:
        motivations = None; motivations_not = None
    if "cinema_types" not in allowed_dims:
        cinema_types = None; cinema_types_not = None
    if "time_periods" not in allowed_dims:
        time_periods = None; time_periods_not = None
    if "place_contexts" not in allowed_dims:
        place_contexts = None; place_contexts_not = None
    if "studios" not in allowed_dims:
        studios = None; studios_not = None

    # Force AND mode and clear excludes for tiers without OR/NOT
    if not TIER_CAN_USE_OR_NOT.get(tier, False):
        categories_mode = "and"; categories_not = None
        themes_mode = "and"; themes_not = None
        atmospheres_mode = "and"; atmospheres_not = None
        messages_mode = "and"; messages_not = None
        characters_mode = "and"; characters_not = None
        motivations_mode = "and"; motivations_not = None
        cinema_types_mode = "and"; cinema_types_not = None
        time_periods_mode = "and"; time_periods_not = None
        place_contexts_mode = "and"; place_contexts_not = None
        studios_mode = "and"; studios_not = None

    # Per-dimension sort_order filtering
    dim_sort_limits = TIER_DIMENSION_MAX_SORT_ORDER.get(tier, {})
    dim_sort_table_map = {
        "themes": ("theme_context", "theme_name"),
        "atmospheres": ("atmosphere", "atmosphere_name"),
        "place_contexts": ("place_context", "environment"),
        "characters": ("character_context", "context_name"),
        "motivations": ("motivation_relation", "motivation_name"),
        "cinema_types": ("cinema_type", "technique_name"),
    }
    for dim_key, max_order in dim_sort_limits.items():
        vals = locals().get(dim_key)
        if not vals:
            continue
        tbl, col = dim_sort_table_map[dim_key]
        result = await db.execute(
            text(f"SELECT {col}, sort_order FROM {tbl} WHERE {col} = ANY(:names)"),
            {"names": vals},
        )
        allowed = [row[0] for row in result.fetchall() if row[1] is not None and row[1] <= max_order]
        if dim_key == "themes":
            themes = allowed if allowed else None
        elif dim_key == "atmospheres":
            atmospheres = allowed if allowed else None
        elif dim_key == "place_contexts":
            place_contexts = allowed if allowed else None
        elif dim_key == "characters":
            characters = allowed if allowed else None
        elif dim_key == "motivations":
            motivations = allowed if allowed else None
        elif dim_key == "cinema_types":
            cinema_types = allowed if allowed else None

    # Filter count enforcement
    max_filters = TIER_MAX_FILTERS.get(tier)
    if max_filters is not None:
        filter_count = 0
        for vals in [categories, themes, atmospheres, messages, characters, motivations,
                     cinema_types, time_periods, place_contexts, studios]:
            if vals:
                filter_count += len(vals)
        if location: filter_count += 1
        if language: filter_count += 1
        if source: filter_count += 1
        if filter_count > max_filters:
            raise HTTPException(
                status_code=400,
                detail=f"Filter limit exceeded (max {max_filters} for your tier)",
            )

    # --- Categories filter (special: composite key with historic_subcategory_name) ---
    if categories:
        cat_mode = categories_mode or "or"

        # Build WHERE conditions for each selected category value
        specific_ids_conditions = []
        parent_values = []
        for val in categories:
            if ": " in val:
                parent, sub = val.split(": ", 1)
                specific_ids_conditions.append(
                    f"(c.category_name = :cat_p_{len(specific_ids_conditions)} "
                    f"AND c.historic_subcategory_name = :cat_s_{len(specific_ids_conditions)})"
                )
                params[f"cat_p_{len(specific_ids_conditions) - 1}"] = parent
                params[f"cat_s_{len(specific_ids_conditions) - 1}"] = sub
            else:
                parent_values.append(val)

        parent_conditions = []
        for j, pv in enumerate(parent_values):
            parent_conditions.append(f"c.category_name = :cat_parent_{j}")
            params[f"cat_parent_{j}"] = pv

        all_conditions = specific_ids_conditions + parent_conditions
        if all_conditions:
            or_clause = " OR ".join(all_conditions)

            if cat_mode == "and":
                # AND: film must match ALL selected values
                case_parts = []
                for idx, val in enumerate(categories):
                    if ": " in val:
                        parent, sub = val.split(": ", 1)
                        case_parts.append(
                            f"WHEN c.category_name = :cat_case_p_{idx} "
                            f"AND c.historic_subcategory_name = :cat_case_s_{idx} "
                            f"THEN :cat_case_v_{idx}"
                        )
                        params[f"cat_case_p_{idx}"] = parent
                        params[f"cat_case_s_{idx}"] = sub
                        params[f"cat_case_v_{idx}"] = val
                    else:
                        case_parts.append(
                            f"WHEN c.category_name = :cat_case_p_{idx} THEN :cat_case_v_{idx}"
                        )
                        params[f"cat_case_p_{idx}"] = val
                        params[f"cat_case_v_{idx}"] = val

                case_expr = "CASE " + " ".join(case_parts) + " END"
                where_clauses.append(
                    f"""f.film_id IN (
                        SELECT fg.film_id FROM film_genre fg
                        JOIN category c ON fg.category_id = c.category_id
                        WHERE {or_clause}
                        GROUP BY fg.film_id
                        HAVING COUNT(DISTINCT {case_expr}) = :cat_count
                    )"""
                )
                params["cat_count"] = len(categories)
            else:
                # OR: film must match ANY selected value
                where_clauses.append(
                    f"""f.film_id IN (
                        SELECT fg.film_id FROM film_genre fg
                        JOIN category c ON fg.category_id = c.category_id
                        WHERE {or_clause}
                    )"""
                )

    # Categories NOT exclusion
    if categories_not:
        not_conditions = []
        for idx, val in enumerate(categories_not):
            if ": " in val:
                parent, sub = val.split(": ", 1)
                not_conditions.append(
                    f"(c.category_name = :cat_not_p_{idx} AND c.historic_subcategory_name = :cat_not_s_{idx})"
                )
                params[f"cat_not_p_{idx}"] = parent
                params[f"cat_not_s_{idx}"] = sub
            else:
                not_conditions.append(f"c.category_name = :cat_not_v_{idx}")
                params[f"cat_not_v_{idx}"] = val
        not_or = " OR ".join(not_conditions)
        where_clauses.append(
            f"""f.film_id NOT IN (
                SELECT fg.film_id FROM film_genre fg
                JOIN category c ON fg.category_id = c.category_id
                WHERE {not_or}
            )"""
        )

    # --- Generic taxonomy filters (OR/AND mode + NOT exclusions) ---
    HIERARCHICAL_FILTER_DIMS = {"themes"}

    _taxonomy_filters = [
        (themes, themes_not, themes_mode, "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
        (atmospheres, atmospheres_not, atmospheres_mode, "film_atmosphere", "atmosphere_id", "atmosphere", "atmosphere_id", "atmosphere_name"),
        (messages, messages_not, messages_mode, "film_message", "message_id", "message_conveyed", "message_id", "message_name"),
        (characters, characters_not, characters_mode, "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
        (motivations, motivations_not, motivations_mode, "film_motivation", "motivation_id", "motivation_relation", "motivation_id", "motivation_name"),
        (cinema_types, cinema_types_not, cinema_types_mode, "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        (time_periods, time_periods_not, time_periods_mode, "film_period", "time_context_id", "time_context", "time_context_id", "time_period"),
        (place_contexts, place_contexts_not, place_contexts_mode, "film_place", "place_context_id", "place_context", "place_context_id", "environment"),
        (studios, studios_not, studios_mode, "production", "studio_id", "studio", "studio_id", "studio_name"),
    ]

    _taxonomy_dim_names = [
        "themes", "atmospheres", "messages", "characters", "motivations",
        "cinema_types", "time_periods", "place_contexts", "studios",
    ]

    for i, (values, not_values, mode_param, junc_table, junc_fk, lookup_table, lookup_pk, lookup_name) in enumerate(_taxonomy_filters):
        dim_name = _taxonomy_dim_names[i]
        mode = mode_param or "or"

        # Include filter
        if values:
            param_key = f"tax_{i}"
            count_key = f"tax_{i}_count"

            is_hierarchical = dim_name in HIERARCHICAL_FILTER_DIMS
            hier_parents = [v for v in values if ": " not in v] if is_hierarchical else []

            if mode == "and":
                # AND: film must match ALL selected values
                if hier_parents:
                    parent_like_conditions = []
                    for j, pv in enumerate(hier_parents):
                        pkey = f"{param_key}_parent_{j}"
                        parent_like_conditions.append(f"lt.{lookup_name} LIKE :{pkey}")
                        params[pkey] = f"{pv}: %"

                    case_parts = []
                    for j, pv in enumerate(hier_parents):
                        pkey = f"{param_key}_parent_{j}"
                        case_parts.append(f"WHEN lt.{lookup_name} LIKE :{pkey} THEN :tax_{i}_pv_{j}")
                        params[f"tax_{i}_pv_{j}"] = pv
                    case_parts.append(f"WHEN lt.{lookup_name} = ANY(:{param_key}) THEN lt.{lookup_name}")
                    case_expr = "CASE " + " ".join(case_parts) + " END"

                    or_likes = " OR ".join(parent_like_conditions)
                    where_clauses.append(
                        f"""f.film_id IN (
                            SELECT jt.film_id FROM {junc_table} jt
                            JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                            WHERE lt.{lookup_name} = ANY(:{param_key})
                               OR {or_likes}
                            GROUP BY jt.film_id
                            HAVING COUNT(DISTINCT {case_expr}) = :{count_key}
                        )"""
                    )
                else:
                    where_clauses.append(
                        f"""f.film_id IN (
                            SELECT jt.film_id FROM {junc_table} jt
                            JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                            WHERE lt.{lookup_name} = ANY(:{param_key})
                            GROUP BY jt.film_id
                            HAVING COUNT(DISTINCT lt.{lookup_name}) = :{count_key}
                        )"""
                    )
                params[count_key] = len(values)
            else:
                # OR: film must match ANY selected value
                if hier_parents:
                    parent_like_conditions = []
                    for j, pv in enumerate(hier_parents):
                        pkey = f"{param_key}_parent_{j}"
                        parent_like_conditions.append(f"lt.{lookup_name} LIKE :{pkey}")
                        params[pkey] = f"{pv}: %"
                    or_likes = " OR ".join(parent_like_conditions)
                    where_clauses.append(
                        f"""f.film_id IN (
                            SELECT jt.film_id FROM {junc_table} jt
                            JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                            WHERE lt.{lookup_name} = ANY(:{param_key})
                               OR {or_likes}
                        )"""
                    )
                else:
                    where_clauses.append(
                        f"""f.film_id IN (
                            SELECT jt.film_id FROM {junc_table} jt
                            JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                            WHERE lt.{lookup_name} = ANY(:{param_key})
                        )"""
                    )

            params[param_key] = values

        # NOT exclusion filter
        if not_values:
            not_key = f"tax_{i}_not"
            where_clauses.append(
                f"""f.film_id NOT IN (
                    SELECT jt.film_id FROM {junc_table} jt
                    JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{lookup_pk}
                    WHERE lt.{lookup_name} = ANY(:{not_key})
                )"""
            )
            params[not_key] = not_values

    # Director filter (kept for API backward compatibility)
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

    # Source filter
    if source:
        where_clauses.append(
            """f.film_id IN (
                SELECT fo.film_id FROM film_origin fo
                JOIN source s ON fo.source_id = s.source_id
                WHERE s.source_type ILIKE :source
            )"""
        )
        params["source"] = source

    # Year range
    if year_min is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) >= :year_min")
        params["year_min"] = year_min
    if year_max is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) <= :year_max")
        params["year_max"] = year_max

    # Seen filter (per-user)
    if seen is not None and user:
        if seen:
            where_clauses.append(
                "f.film_id IN (SELECT film_id FROM user_film_status WHERE user_id = :uid AND seen = TRUE)"
            )
        else:
            where_clauses.append(
                "f.film_id NOT IN (SELECT film_id FROM user_film_status WHERE user_id = :uid AND seen = TRUE)"
            )
        params["uid"] = user.id

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
        "popularity": "f.weighted_score",
    }
    if sort_by == "random":
        order_clause = "RANDOM()"
    else:
        sort_col = sort_col_map[sort_by]
        order = sort_order.upper()
        order_clause = f"{sort_col} {order} NULLS LAST, f.film_id ASC"

    # Count query
    count_sql = f"SELECT COUNT(*) FROM film f WHERE {where_sql}"
    result = await db.execute(text(count_sql), params)
    total = result.scalar_one()

    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    # Main query
    user_join = ""
    user_cols = "NULL AS seen, NULL AS favorite, NULL AS watchlist, NULL AS rating"
    if user:
        user_join = "LEFT JOIN user_film_status ufs ON f.film_id = ufs.film_id AND ufs.user_id = :user_id"
        user_cols = "ufs.seen, ufs.favorite, ufs.watchlist, ufs.rating"
        params["user_id"] = user.id
    list_sql = f"""
        SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
               f.poster_url, {user_cols}
        FROM film f
        {user_join}
        WHERE {where_sql}
        ORDER BY {order_clause}
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
            # r[5]=seen, r[6]=favorite, r[7]=watchlist, r[8]=rating
            u_status = None
            if user and r[5] is not None:
                u_status = UserFilmStatus(
                    seen=r[5] or False,
                    favorite=r[6] or False,
                    watchlist=r[7] or False,
                    rating=r[8],
                )
            items.append(
                FilmListItem(
                    film_id=fid,
                    original_title=r[1],
                    first_release_date=r[2],
                    duration=r[3],
                    poster_url=r[4],
                    user_status=u_status,
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
# GET /api/films/search-local — Lightweight title autocomplete (local DB)
# =============================================================================


@router.get("/films/search-local")
async def search_local_films(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text("""
            SELECT film_id, original_title,
                   EXTRACT(YEAR FROM first_release_date)::int AS year
            FROM film
            WHERE LOWER(original_title) LIKE :pattern
            ORDER BY first_release_date DESC NULLS LAST
            LIMIT :lim
        """),
        {"pattern": f"%{q.lower()}%", "lim": limit},
    )
    return [
        {"film_id": r[0], "original_title": r[1], "year": r[2]}
        for r in rows.fetchall()
    ]


# =============================================================================
# GET /api/films/{film_id} — Full detail (parallelized queries)
# =============================================================================


_detail_semaphore = asyncio.Semaphore(6)


async def _parallel_query(sql: str, params: dict) -> list:
    """Run a single query using its own connection for true parallelism."""
    async with _detail_semaphore:
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            return result.fetchall()


@router.get("/films/{film_id}", response_model=FilmDetail)
async def get_film(
    film_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    # Core film — must run first to check existence
    result = await db.execute(
        text("SELECT * FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    film = result.mappings().first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")

    # Run all remaining queries in parallel
    params = {"fid": film_id}
    (
        title_rows, cat_rows, cinema_rows, theme_rows, char_rows,
        motiv_rows, atmos_rows, msg_rows, time_rows, place_rows,
        sp_rows, crew_rows, cast_rows, studio_rows, src_rows,
        award_rows, streaming_rows, seq_rows,
    ) = await asyncio.gather(
        _parallel_query(
            "SELECT l.language_code, l.language_name, fl.film_title, fl.is_original "
            "FROM film_language fl "
            "JOIN language l ON fl.language_id = l.language_id "
            "WHERE fl.film_id = :fid "
            "ORDER BY fl.is_original DESC",
            params,
        ),
        _parallel_query(
            "SELECT DISTINCT c.category_name, c.historic_subcategory_name "
            "FROM film_genre fg "
            "JOIN category c ON fg.category_id = c.category_id "
            "WHERE fg.film_id = :fid ORDER BY c.category_name",
            params,
        ),
        _parallel_query(
            "SELECT ct.technique_name FROM film_technique ft "
            "JOIN cinema_type ct ON ft.cinema_type_id = ct.cinema_type_id "
            "WHERE ft.film_id = :fid ORDER BY ct.sort_order, ct.technique_name",
            params,
        ),
        _parallel_query(
            "SELECT tc.theme_name FROM film_theme fth "
            "JOIN theme_context tc ON fth.theme_context_id = tc.theme_context_id "
            "WHERE fth.film_id = :fid ORDER BY tc.theme_name",
            params,
        ),
        _parallel_query(
            "SELECT cc.context_name FROM film_character_context fcc "
            "JOIN character_context cc ON fcc.character_context_id = cc.character_context_id "
            "WHERE fcc.film_id = :fid ORDER BY cc.sort_order, cc.context_name",
            params,
        ),
        _parallel_query(
            "SELECT mr.motivation_name FROM film_motivation fm "
            "JOIN motivation_relation mr ON fm.motivation_id = mr.motivation_id "
            "WHERE fm.film_id = :fid ORDER BY mr.motivation_name",
            params,
        ),
        _parallel_query(
            "SELECT a.atmosphere_name FROM film_atmosphere fa "
            "JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id "
            "WHERE fa.film_id = :fid ORDER BY a.atmosphere_name",
            params,
        ),
        _parallel_query(
            "SELECT mc.message_name FROM film_message fmsg "
            "JOIN message_conveyed mc ON fmsg.message_id = mc.message_id "
            "WHERE fmsg.film_id = :fid ORDER BY mc.message_name",
            params,
        ),
        _parallel_query(
            "SELECT tc.time_period FROM film_period fp "
            "JOIN time_context tc ON fp.time_context_id = tc.time_context_id "
            "WHERE fp.film_id = :fid ORDER BY tc.time_period",
            params,
        ),
        _parallel_query(
            "SELECT pc.environment FROM film_place fpl "
            "JOIN place_context pc ON fpl.place_context_id = pc.place_context_id "
            "WHERE fpl.film_id = :fid ORDER BY pc.environment",
            params,
        ),
        _parallel_query(
            "SELECT g.continent, g.country, g.state_city, fsp.place_type "
            "FROM film_set_place fsp "
            "JOIN geography g ON fsp.geography_id = g.geography_id "
            "WHERE fsp.film_id = :fid "
            "ORDER BY g.continent, g.country",
            params,
        ),
        _parallel_query(
            "SELECT p.person_id, p.firstname, p.lastname, pj.role_name, p.photo_url "
            "FROM crew cr "
            "JOIN person p ON cr.person_id = p.person_id "
            "JOIN person_job pj ON cr.job_id = pj.job_id "
            "WHERE cr.film_id = :fid "
            "ORDER BY pj.role_name, p.lastname",
            params,
        ),
        _parallel_query(
            "SELECT p.person_id, p.firstname, p.lastname, ca.character_name, ca.cast_order, p.photo_url "
            "FROM casting ca "
            "JOIN person p ON ca.person_id = p.person_id "
            "WHERE ca.film_id = :fid "
            "ORDER BY ca.cast_order NULLS LAST",
            params,
        ),
        _parallel_query(
            "SELECT s.studio_name FROM production pr "
            "JOIN studio s ON pr.studio_id = s.studio_id "
            "WHERE pr.film_id = :fid ORDER BY s.studio_name",
            params,
        ),
        _parallel_query(
            "SELECT s.source_type, s.source_title, s.author "
            "FROM film_origin fo "
            "JOIN source s ON fo.source_id = s.source_id "
            "WHERE fo.film_id = :fid",
            params,
        ),
        _parallel_query(
            "SELECT festival_name, category, award_year, result "
            "FROM award WHERE film_id = :fid "
            "ORDER BY award_year, festival_name",
            params,
        ),
        _parallel_query(
            "SELECT sp.platform_name FROM film_exploitation fe "
            "JOIN stream_platform sp ON fe.platform_id = sp.platform_id "
            "WHERE fe.film_id = :fid ORDER BY sp.platform_name",
            params,
        ),
        _parallel_query(
            "SELECT related_id, original_title, relation_type, poster_url "
            "FROM ("
            "  SELECT fs.related_film_id AS related_id, f2.original_title, fs.relation_type, f2.poster_url, f2.first_release_date "
            "  FROM film_sequel fs "
            "  JOIN film f2 ON fs.related_film_id = f2.film_id "
            "  WHERE fs.film_id = :fid "
            "  UNION "
            "  SELECT fs.film_id AS related_id, f2.original_title, fs.relation_type, f2.poster_url, f2.first_release_date "
            "  FROM film_sequel fs "
            "  JOIN film f2 ON fs.film_id = f2.film_id "
            "  WHERE fs.related_film_id = :fid "
            ") sub "
            "ORDER BY first_release_date ASC NULLS LAST",
            params,
        ),
    )

    # Process titles
    titles = [
        FilmTitle(language_code=r[0], language_name=r[1], title=r[2], is_original=r[3])
        for r in title_rows
    ]

    # Process categories — composite "Historical: biopic" for subcategories
    categories: list[str] = []
    seen_parents: set[str] = set()
    for cat_name, sub_name in cat_rows:
        if sub_name:
            categories.append(f"{cat_name}: {sub_name}")
            seen_parents.add(cat_name)
        else:
            categories.append(cat_name)
    categories = [
        c for c in categories
        if ": " in c or c not in seen_parents
    ]

    # Process simple name lists
    cinema_types = [r[0] for r in cinema_rows]
    themes_list = [r[0] for r in theme_rows]
    characters_list = [r[0] for r in char_rows]
    motivations_list = [r[0] for r in motiv_rows]
    atmospheres_list = [r[0] for r in atmos_rows]
    messages_list = [r[0] for r in msg_rows]
    time_periods_list = [r[0] for r in time_rows]
    place_contexts_list = [r[0] for r in place_rows]
    studios = [r[0] for r in studio_rows]
    streaming = [r[0] for r in streaming_rows]

    # Process structured rows
    set_places = [
        FilmSetPlaceOut(continent=r[0], country=r[1], state_city=r[2], place_type=r[3])
        for r in sp_rows
    ]
    crew = [
        CrewMember(person_id=r[0], firstname=r[1], lastname=r[2], role=r[3], photo_url=r[4])
        for r in crew_rows
    ]
    cast = [
        CastMember(person_id=r[0], firstname=r[1], lastname=r[2], character_name=r[3], cast_order=r[4], photo_url=r[5])
        for r in cast_rows
    ]
    sources = [
        SourceOut(source_type=r[0], source_title=r[1], author=r[2])
        for r in src_rows
    ]
    awards = [
        AwardOut(festival_name=r[0], category=r[1], year=r[2], result=r[3])
        for r in award_rows
    ]
    sequels = [
        FilmRelation(related_film_id=r[0], related_film_title=r[1], relation_type=r[2], poster_url=r[3])
        for r in seq_rows
    ]

    # Fetch per-user status if logged in
    u_status = None
    if user:
        us_result = await db.execute(
            text("SELECT seen, favorite, watchlist, rating, notes FROM user_film_status WHERE user_id = :uid AND film_id = :fid"),
            {"uid": user.id, "fid": film_id},
        )
        us_row = us_result.fetchone()
        if us_row:
            u_status = UserFilmStatus(
                seen=us_row[0] or False,
                favorite=us_row[1] or False,
                watchlist=us_row[2] or False,
                rating=us_row[3],
                notes=us_row[4],
            )

    return FilmDetail(
        film_id=film["film_id"],
        original_title=film["original_title"],
        duration=film["duration"],
        color=film["color"] if film["color"] is not None else True,
        first_release_date=film["first_release_date"],
        summary=film["summary"],
        user_status=u_status,
        poster_url=film["poster_url"],
        backdrop_url=film["backdrop_url"],
        imdb_id=film["imdb_id"],
        tmdb_id=film["tmdb_id"],
        budget=film["budget"],
        revenue=film["revenue"],
        tmdb_score=float(film["tmdb_score"]) if film["tmdb_score"] is not None else None,
        tmdb_vote_count=film["tmdb_vote_count"],
        weighted_score=float(film["weighted_score"]) if film["weighted_score"] is not None else None,
        titles=titles,
        categories=categories,
        cinema_types=cinema_types,
        themes=themes_list,
        characters=characters_list,
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
# GET /api/films/{film_id}/similar — Similar films
# =============================================================================


TIER_SIMILAR_LIMITS: dict[str, int] = {
    "anonymous": 3,
    "free": 6,
    "pro": 12,
    "admin": 12,
}


@router.get("/films/{film_id}/similar", response_model=SimilarFilmsResponse)
async def similar_films(
    film_id: int,
    limit: int = Query(12, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT film_id FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")

    tier = user.tier if user else "anonymous"
    max_limit = TIER_SIMILAR_LIMITS.get(tier, 3)
    capped = min(limit, max_limit)

    results = await recommender.get_similar_films(db, film_id, capped, tier)
    items = [SimilarFilm(**r) for r in results]
    return SimilarFilmsResponse(items=items)


# =============================================================================
# POST /api/films — Create a new film
# =============================================================================


@router.post("/films", response_model=dict, status_code=201)
async def create_film(film_data: FilmCreate, db: AsyncSession = Depends(get_db), admin: None = Depends(require_admin)):
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
                poster_url, backdrop_url, imdb_id, tmdb_id, budget, revenue,
                tmdb_score, tmdb_vote_count, tmdb_collection_id
            ) VALUES (
                :original_title, :duration, :color, :first_release_date, :summary,
                :poster_url, :backdrop_url, :imdb_id, :tmdb_id, :budget, :revenue,
                :tmdb_score, :tmdb_vote_count, :tmdb_collection_id
            ) RETURNING film_id
        """),
        {
            "original_title": film.get("original_title"),
            "duration": film.get("duration"),
            "color": film.get("color", True),
            "first_release_date": (
                date.fromisoformat(film["first_release_date"])
                if isinstance(film.get("first_release_date"), str)
                else film.get("first_release_date")
            ),
            "summary": film.get("summary"),
            "poster_url": film.get("poster_url"),
            "backdrop_url": film.get("backdrop_url"),
            "imdb_id": film.get("imdb_id"),
            "tmdb_id": tmdb_id,
            "budget": film.get("budget"),
            "revenue": film.get("revenue"),
            "tmdb_score": film.get("tmdb_score"),
            "tmdb_vote_count": film.get("tmdb_vote_count"),
            "tmdb_collection_id": film.get("tmdb_collection_id"),
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

    # Insert categories (special handling for Historic subcategories)
    for cat in enrichment.get("categories", []):
        if not cat or (isinstance(cat, str) and cat.startswith("[NEW]")):
            continue
        r = await db.execute(
            text("SELECT category_id FROM category WHERE category_name = :name AND historic_subcategory_name IS NULL"),
            {"name": cat},
        )
        lid = r.scalar_one_or_none()
        if lid:
            await db.execute(
                text("INSERT INTO film_genre (film_id, category_id) VALUES (:fid, :lid) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "lid": lid},
            )

    # Insert taxonomy junctions from enrichment
    taxonomy_junctions = [
        ("cinema_type", "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        ("themes", "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
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

    # Auto-link franchise sequels via TMDB collection
    tmdb_collection_id = film.get("tmdb_collection_id")
    if tmdb_collection_id:
        coll_result = await db.execute(
            text("""
                SELECT film_id FROM film
                WHERE tmdb_collection_id = :cid AND film_id != :fid
            """),
            {"cid": tmdb_collection_id, "fid": film_id},
        )
        sibling_ids = [row[0] for row in coll_result.fetchall()]
        for sibling_id in sibling_ids:
            await db.execute(
                text("""
                    INSERT INTO film_sequel (film_id, related_film_id, relation_type)
                    VALUES (:fid, :rid, 'sequel')
                    ON CONFLICT DO NOTHING
                """),
                {"fid": min(sibling_id, film_id), "rid": max(sibling_id, film_id)},
            )
        if sibling_ids:
            logger.info("Auto-linked %d sequel(s) via collection %d", len(sibling_ids), tmdb_collection_id)

    await db.commit()
    return {"film_id": film_id, "message": "Film created successfully"}


# =============================================================================
# PUT /api/films/{film_id} — Update a film
# =============================================================================
# DELETE /api/films/{film_id} — Delete a film
# =============================================================================


@router.delete("/films/{film_id}", status_code=200)
async def delete_film(film_id: int, db: AsyncSession = Depends(get_db), admin: None = Depends(require_admin)):
    result = await db.execute(
        text("SELECT film_id, original_title FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    film = result.mappings().first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")

    await db.execute(text("DELETE FROM film WHERE film_id = :fid"), {"fid": film_id})
    await db.commit()
    recommender.invalidate_film(film_id)
    logger.info("Deleted film #%d: %s", film_id, film["original_title"])
    return {"message": f"Film '{film['original_title']}' deleted"}


# =============================================================================
# PUT /api/films/{film_id} — Update a film
# =============================================================================


@router.put("/films/{film_id}", response_model=dict)
async def update_film(film_id: int, update: FilmUpdate, db: AsyncSession = Depends(get_db), admin: None = Depends(require_admin)):
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

    # Update categories (special handling for Historical subcategories)
    if update.categories is not None:
        await db.execute(text("DELETE FROM film_genre WHERE film_id = :fid"), {"fid": film_id})
        for val in update.categories:
            if not val:
                continue
            if ": " in val:
                # Composite "Historical: biopic" → lookup with subcategory
                parent, sub = val.split(": ", 1)
                r = await db.execute(
                    text("SELECT category_id FROM category WHERE category_name = :parent AND historic_subcategory_name = :sub"),
                    {"parent": parent, "sub": sub},
                )
            else:
                # Base category → lookup without subcategory
                r = await db.execute(
                    text("SELECT category_id FROM category WHERE category_name = :name AND historic_subcategory_name IS NULL"),
                    {"name": val},
                )
            lid = r.scalar_one_or_none()
            if lid:
                await db.execute(
                    text("INSERT INTO film_genre (film_id, category_id) VALUES (:fid, :lid) ON CONFLICT DO NOTHING"),
                    {"fid": film_id, "lid": lid},
                )

    # Update taxonomy junctions (clear and re-insert pattern)
    junction_updates = [
        (update.cinema_types, "film_technique", "cinema_type_id", "cinema_type", "cinema_type_id", "technique_name"),
        (update.themes, "film_theme", "theme_context_id", "theme_context", "theme_context_id", "theme_name"),
        (update.characters, "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
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

    # Studios (clear junction + re-insert, auto-create missing studios)
    if update.studios is not None:
        await db.execute(text("DELETE FROM production WHERE film_id = :fid"), {"fid": film_id})
        for studio_name in update.studios:
            if not studio_name:
                continue
            r = await db.execute(
                text("SELECT studio_id FROM studio WHERE studio_name = :name"),
                {"name": studio_name},
            )
            sid = r.scalar_one_or_none()
            if not sid:
                r = await db.execute(
                    text("INSERT INTO studio (studio_name) VALUES (:name) RETURNING studio_id"),
                    {"name": studio_name},
                )
                sid = r.scalar_one()
            await db.execute(
                text("INSERT INTO production (film_id, studio_id) VALUES (:fid, :sid) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "sid": sid},
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

    # Sources (find-or-create source rows, clear-and-reinsert junction)
    if update.sources is not None:
        await db.execute(text("DELETE FROM film_origin WHERE film_id = :fid"), {"fid": film_id})
        for src in update.sources:
            if not isinstance(src, dict):
                continue
            source_type = (src.get("source_type") or "").strip()
            if not source_type:
                continue
            source_title = src.get("source_title") or None
            author = src.get("author") or None
            # Find existing source
            r = await db.execute(
                text("""
                    SELECT source_id FROM source
                    WHERE source_type = :st
                      AND source_title IS NOT DISTINCT FROM :title
                      AND author IS NOT DISTINCT FROM :author
                """),
                {"st": source_type, "title": source_title, "author": author},
            )
            sid = r.scalar_one_or_none()
            if not sid:
                r = await db.execute(
                    text("""
                        INSERT INTO source (source_type, source_title, author)
                        VALUES (:st, :title, :author)
                        RETURNING source_id
                    """),
                    {"st": source_type, "title": source_title, "author": author},
                )
                sid = r.scalar_one()
            await db.execute(
                text("INSERT INTO film_origin (film_id, source_id) VALUES (:fid, :sid) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "sid": sid},
            )

    # Set places (geography)
    if update.set_places is not None:
        await db.execute(text("DELETE FROM film_set_place WHERE film_id = :fid"), {"fid": film_id})
        for sp in update.set_places:
            if not isinstance(sp, dict):
                continue
            continent = sp.get("continent") or None
            country = sp.get("country") or None
            state_city = sp.get("state_city") or None
            place_type = sp.get("place_type", "diegetic")
            if place_type not in ("diegetic", "shooting", "fictional"):
                continue
            if not continent and not country and not state_city:
                continue
            # Find or create geography
            r = await db.execute(
                text("""
                    SELECT geography_id FROM geography
                    WHERE continent IS NOT DISTINCT FROM :continent
                      AND country IS NOT DISTINCT FROM :country
                      AND state_city IS NOT DISTINCT FROM :state_city
                """),
                {"continent": continent, "country": country, "state_city": state_city},
            )
            gid = r.scalar_one_or_none()
            if not gid:
                r = await db.execute(
                    text("""
                        INSERT INTO geography (continent, country, state_city)
                        VALUES (:continent, :country, :state_city)
                        RETURNING geography_id
                    """),
                    {"continent": continent, "country": country, "state_city": state_city},
                )
                gid = r.scalar_one()
            await db.execute(
                text("INSERT INTO film_set_place (film_id, geography_id, place_type) VALUES (:fid, :gid, :pt) ON CONFLICT DO NOTHING"),
                {"fid": film_id, "gid": gid, "pt": place_type},
            )

    # Awards
    if update.awards is not None:
        await db.execute(text("DELETE FROM award WHERE film_id = :fid"), {"fid": film_id})
        for award in update.awards:
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

    await db.commit()
    recommender.invalidate_film(film_id)
    return {"film_id": film_id, "message": "Film updated successfully"}


# =============================================================================
# POST /api/films/{film_id}/relations — Add a film_sequel relation
# =============================================================================


@router.post("/films/{film_id}/relations", status_code=201)
async def add_film_relation(
    film_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    related_film_id = body.get("related_film_id")
    relation_type = body.get("relation_type")

    if not related_film_id or not relation_type:
        raise HTTPException(status_code=400, detail="related_film_id and relation_type required")
    if relation_type not in ("sequel", "prequel", "remake", "spinoff", "reboot", "cycle"):
        raise HTTPException(status_code=400, detail="Invalid relation_type")
    if related_film_id == film_id:
        raise HTTPException(status_code=400, detail="Cannot relate a film to itself")

    # Canonical ordering: smaller id first
    fid = min(film_id, related_film_id)
    rid = max(film_id, related_film_id)

    await db.execute(
        text("""
            INSERT INTO film_sequel (film_id, related_film_id, relation_type)
            VALUES (:fid, :rid, :rtype)
            ON CONFLICT (film_id, related_film_id) DO UPDATE SET relation_type = :rtype
        """),
        {"fid": fid, "rid": rid, "rtype": relation_type},
    )
    await db.commit()
    recommender.invalidate_film(film_id)
    recommender.invalidate_film(related_film_id)
    return {"message": "Relation added"}


# =============================================================================
# DELETE /api/films/{film_id}/relations/{related_film_id} — Remove a relation
# =============================================================================


@router.delete("/films/{film_id}/relations/{related_film_id}", status_code=200)
async def delete_film_relation(
    film_id: int,
    related_film_id: int,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    # Delete both orderings (the canonical one will match)
    await db.execute(
        text("""
            DELETE FROM film_sequel
            WHERE (film_id = :a AND related_film_id = :b)
               OR (film_id = :b AND related_film_id = :a)
        """),
        {"a": film_id, "b": related_film_id},
    )
    await db.commit()
    recommender.invalidate_film(film_id)
    recommender.invalidate_film(related_film_id)
    return {"message": "Relation removed"}


# =============================================================================
# GET /api/stats — Database statistics
# =============================================================================


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    stats: dict = {}

    # Total films
    r = await db.execute(text("SELECT COUNT(*) FROM film"))
    stats["total_films"] = r.scalar_one()

    # Seen vs unseen (per-user)
    if user:
        r = await db.execute(
            text("SELECT COUNT(*) FROM user_film_status WHERE user_id = :uid AND seen = TRUE"),
            {"uid": user.id},
        )
        stats["seen"] = r.scalar_one()
    else:
        stats["seen"] = 0
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
            INSERT INTO person (firstname, lastname, tmdb_id, photo_url, gender)
            VALUES (:firstname, :lastname, :tmdb_id, :photo_url, :gender)
            ON CONFLICT (tmdb_id) DO UPDATE SET
                firstname = EXCLUDED.firstname,
                lastname = EXCLUDED.lastname,
                photo_url = COALESCE(EXCLUDED.photo_url, person.photo_url),
                gender = COALESCE(EXCLUDED.gender, person.gender)
            RETURNING person_id
        """),
        {
            "firstname": person.get("firstname", ""),
            "lastname": person.get("lastname", ""),
            "tmdb_id": tmdb_id,
            "photo_url": person.get("photo_url"),
            "gender": person.get("gender"),
        },
    )
    return r.scalar_one()
