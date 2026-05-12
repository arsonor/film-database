"""
Stats Dashboard API — single bulk endpoint with tier-aware payload.

Returns all data for the /stats page in one request. Sections the user's tier
cannot access come back as `null` so the frontend can render lock screens
without an extra round-trip.

Tier visibility (Step 17a):
- quick:         always populated
- geography:     always null in 17a (placeholder, "Coming soon")
- financials:    null for anonymous; populated for free / pro / admin
- people:        null for anonymous + free; populated for pro / admin
- taxonomy:      null for anonymous + free; populated for pro / admin
- personal_stats: populated only for logged-in pro / admin
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from backend.app.auth import UserInfo, get_current_user
from backend.app.data.country_name_to_iso import (
    LEGACY_ISO_ALIASES,
    country_name_to_iso,
    iso_to_country_names,
    normalize_iso,
    preferred_country_name,
)
from backend.app.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()


# Curated subset of cinema_type values with strong temporal patterns.
# Ordered here for reference only — actual ordering in the heatmap comes
# from each row's sort_order column in the cinema_type table.
CINEMA_MOVEMENT_NAMES = [
    # Aesthetics / visual
    "CGI",
    "3D",
    "black and white",
    # Movements / eras
    "silent",
    "expressionism",
    "realism",
    "neo-realism",
    "noir",
    "hollywood golden age",
    "new hollywood",
    "new wave",
    "neo-noir",
    # Industry / culture
    "blockbuster",
    "art house",
    "franchise",
    # Narrative / pacing
    "slow cinema",
    # Sub-genres / archetypes
    "biopic",
    "western",
    "peplum",
    "costume drama",
    "black comedy",
    "slasher",
    "docufiction",
]

# Pro/Admin only — share with both new endpoints.
_PRO_ADMIN_TIERS = {"pro", "admin"}


def _require_pro(user: UserInfo | None) -> UserInfo:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.tier not in _PRO_ADMIN_TIERS:
        raise HTTPException(status_code=403, detail="Pro tier required")
    return user


# =============================================================================
# Pydantic response models
# =============================================================================


class QuickStats(BaseModel):
    total_films: int
    total_directors: int
    total_actors: int
    total_composers: int
    by_decade: list[dict[str, Any]]
    duration_distribution: list[dict[str, Any]]
    color_by_decade: list[dict[str, Any]]
    top_studios: list[dict[str, Any]]
    top_franchises: list[dict[str, Any]]
    most_awarded_films: list[dict[str, Any]]
    by_source_type: list[dict[str, Any]]


class FinancialsStats(BaseModel):
    top_grossing: list[dict[str, Any]]
    top_budgets: list[dict[str, Any]]
    most_profitable: list[dict[str, Any]]
    avg_budget_by_decade: list[dict[str, Any]]
    budget_revenue_scatter: list[dict[str, Any]]


class PeopleStats(BaseModel):
    # Keyed as {role: {filter: [...]}}
    # roles: 'directors' | 'actors' | 'composers'
    # filters: 'all' | 'male' | 'female'
    top_people: dict[str, dict[str, list[dict[str, Any]]]]
    top_director_nationalities: list[dict[str, Any]]
    top_actor_nationalities: list[dict[str, Any]]
    gender_split: dict[str, dict[str, int]]
    directors_gender_by_decade: list[dict[str, Any]]
    living_status: dict[str, dict[str, int]]
    directors_by_birth_decade: list[dict[str, Any]]


class TaxonomyStats(BaseModel):
    top_themes: list[dict[str, Any]]
    category_distribution: list[dict[str, Any]]
    top_atmospheres: list[dict[str, Any]]
    # Shape changed in Step 17c: now {category, decade, film_count, decade_total, pct}
    category_by_decade_heatmap: list[dict[str, Any]]
    cinema_movements_by_decade: list[dict[str, Any]]
    message_by_decade_heatmap: list[dict[str, Any]]
    atmosphere_by_category: list[dict[str, Any]]
    message_by_movement: list[dict[str, Any]]


class PersonRef(BaseModel):
    person_id: int
    name: str
    film_count: int


class TagCount(BaseModel):
    name: str
    count: int


class PersonTagsResponse(BaseModel):
    person: PersonRef
    top_themes: list[TagCount]
    top_atmospheres: list[TagCount]
    top_characters: list[TagCount]
    top_messages: list[TagCount]


class PersonSearchResult(BaseModel):
    person_id: int
    name: str
    film_count: int


class ProductionCountryCell(BaseModel):
    iso: str
    country: str
    film_count: int


class SetPlaceCountryCell(BaseModel):
    iso: str
    country: str
    film_count: int


class SetPlaceTreemapCell(BaseModel):
    continent: str
    country: str | None
    state_city: str | None
    geography_id: int
    film_count: int


class MostInternationalFilm(BaseModel):
    film_id: int
    title: str
    poster_url: str | None
    year: int | None
    country_count: int
    countries: list[str]


class GeographyPayload(BaseModel):
    production_countries: list[ProductionCountryCell]
    set_place_countries: list[SetPlaceCountryCell]
    set_place_treemap: list[SetPlaceTreemapCell]
    production_country_total: int
    set_place_country_total: int
    most_international_film: MostInternationalFilm | None


class FilmByCountry(BaseModel):
    film_id: int
    title: str
    poster_url: str | None
    year: int | None
    weighted_score: float | None


class PersonalStats(BaseModel):
    seen_count: int
    unseen_count: int
    seen_pct: float
    favorite_count: int
    watchlist_count: int
    rated_count: int
    avg_rating: float | None
    seen_by_decade: list[dict[str, Any]]
    top_seen_categories: list[dict[str, Any]]


class DashboardResponse(BaseModel):
    tier: str
    quick: QuickStats | None
    geography: GeographyPayload | None
    financials: FinancialsStats | None
    people: PeopleStats | None
    taxonomy: TaxonomyStats | None
    personal_stats: PersonalStats | None


# =============================================================================
# Parallel query helper
# =============================================================================


_stats_semaphore = asyncio.Semaphore(8)


async def _q(sql: str, params: dict | None = None) -> list:
    """Run a single query on its own connection for true parallelism."""
    async with _stats_semaphore:
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params or {})
            return result.fetchall()


# =============================================================================
# Block builders
# =============================================================================


async def _build_quick() -> QuickStats:
    (
        total_films_rows,
        crew_role_rows,
        actors_rows,
        decade_rows,
        duration_rows,
        color_rows,
        studios_rows,
        franchises_rows,
        awarded_rows,
        source_rows,
    ) = await asyncio.gather(
        _q("SELECT COUNT(*) FROM film"),
        _q(
            "SELECT pj.role_name, COUNT(DISTINCT c.person_id) AS cnt "
            "FROM crew c JOIN person_job pj ON c.job_id = pj.job_id "
            "WHERE pj.role_name IN ('Director', 'Composer') "
            "GROUP BY pj.role_name"
        ),
        _q("SELECT COUNT(DISTINCT person_id) FROM casting"),
        _q(
            "SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade, "
            "       COUNT(*) AS count "
            "FROM film WHERE first_release_date IS NOT NULL "
            "GROUP BY decade ORDER BY decade"
        ),
        _q(
            "SELECT bucket, COUNT(*) AS count FROM ("
            "  SELECT CASE "
            "    WHEN duration < 60 THEN '<60' "
            "    WHEN duration < 90 THEN '60-89' "
            "    WHEN duration < 120 THEN '90-119' "
            "    WHEN duration < 150 THEN '120-149' "
            "    WHEN duration < 180 THEN '150-179' "
            "    ELSE '180+' "
            "  END AS bucket "
            "  FROM film WHERE duration IS NOT NULL"
            ") sub GROUP BY bucket"
        ),
        _q(
            "SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade, "
            "       COUNT(*) FILTER (WHERE color = TRUE) AS color, "
            "       COUNT(*) FILTER (WHERE color = FALSE) AS bw "
            "FROM film WHERE first_release_date IS NOT NULL "
            "GROUP BY decade ORDER BY decade"
        ),
        _q(
            "SELECT COALESCE(s.studio_group, s.studio_name) AS name, "
            "       COUNT(DISTINCT p.film_id) AS count "
            "FROM production p JOIN studio s ON p.studio_id = s.studio_id "
            "GROUP BY COALESCE(s.studio_group, s.studio_name) "
            "ORDER BY count DESC LIMIT 20"
        ),
        _q(
            "SELECT tc.collection_id, tc.collection_name AS name, "
            "       COUNT(*) AS count, tc.poster_path, tc.backdrop_path "
            "FROM film f "
            "JOIN tmdb_collection tc ON f.tmdb_collection_id = tc.collection_id "
            "GROUP BY tc.collection_id, tc.collection_name, tc.poster_path, tc.backdrop_path "
            "HAVING COUNT(*) >= 2 "
            "ORDER BY count DESC, tc.collection_name LIMIT 20"
        ),
        _q(
            "SELECT f.film_id, f.original_title AS title, f.poster_url, "
            "       EXTRACT(YEAR FROM f.first_release_date)::int AS year, "
            "       COUNT(*) FILTER (WHERE a.result='won') AS wins, "
            "       COUNT(*) FILTER (WHERE a.result='nominated') AS nominations "
            "FROM award a JOIN film f ON a.film_id = f.film_id "
            "GROUP BY f.film_id, f.original_title, f.poster_url, f.first_release_date "
            "ORDER BY wins DESC, nominations DESC LIMIT 20"
        ),
        _q(
            "SELECT s.source_type, COUNT(DISTINCT fo.film_id) AS count "
            "FROM film_origin fo JOIN source s ON fo.source_id = s.source_id "
            "GROUP BY s.source_type ORDER BY count DESC"
        ),
    )

    crew_counts = {r[0]: int(r[1]) for r in crew_role_rows}

    return QuickStats(
        total_films=int(total_films_rows[0][0]) if total_films_rows else 0,
        total_directors=crew_counts.get("Director", 0),
        total_actors=int(actors_rows[0][0]) if actors_rows else 0,
        total_composers=crew_counts.get("Composer", 0),
        by_decade=[{"decade": int(r[0]), "count": int(r[1])} for r in decade_rows],
        duration_distribution=[
            {"bucket": r[0], "count": int(r[1])} for r in duration_rows
        ],
        color_by_decade=[
            {"decade": int(r[0]), "color": int(r[1]), "bw": int(r[2])}
            for r in color_rows
        ],
        top_studios=[{"name": r[0], "count": int(r[1])} for r in studios_rows],
        top_franchises=[
            {
                "collection_id": r[0],
                "name": r[1],
                "count": int(r[2]),
                "poster_path": r[3],
                "backdrop_path": r[4],
            }
            for r in franchises_rows
        ],
        most_awarded_films=[
            {
                "film_id": r[0],
                "title": r[1],
                "poster_url": r[2],
                "year": r[3],
                "wins": int(r[4]),
                "nominations": int(r[5]),
            }
            for r in awarded_rows
        ],
        by_source_type=[
            {"source_type": r[0], "count": int(r[1])} for r in source_rows
        ],
    )


async def _build_financials() -> FinancialsStats:
    (
        top_grossing_rows,
        top_budget_rows,
        profitable_rows,
        avg_budget_rows,
        scatter_rows,
    ) = await asyncio.gather(
        _q(
            "SELECT film_id, original_title AS title, poster_url, "
            "       EXTRACT(YEAR FROM first_release_date)::int AS year, revenue "
            "FROM film WHERE revenue IS NOT NULL AND revenue > 0 "
            "ORDER BY revenue DESC LIMIT 20"
        ),
        _q(
            "SELECT film_id, original_title AS title, poster_url, "
            "       EXTRACT(YEAR FROM first_release_date)::int AS year, budget "
            "FROM film WHERE budget IS NOT NULL AND budget > 0 "
            "ORDER BY budget DESC LIMIT 20"
        ),
        _q(
            "SELECT film_id, original_title AS title, poster_url, "
            "       EXTRACT(YEAR FROM first_release_date)::int AS year, "
            "       budget, revenue, "
            "       (revenue::float / budget) AS ratio "
            "FROM film "
            "WHERE budget IS NOT NULL AND budget > 1000000 "
            "  AND revenue IS NOT NULL AND revenue > 0 "
            "ORDER BY ratio DESC LIMIT 20"
        ),
        _q(
            "SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade, "
            "       AVG(budget)::bigint AS avg_budget, "
            "       COUNT(*) AS film_count "
            "FROM film "
            "WHERE budget IS NOT NULL AND budget > 0 AND first_release_date IS NOT NULL "
            "GROUP BY decade HAVING COUNT(*) >= 3 "
            "ORDER BY decade"
        ),
        _q(
            "SELECT f.film_id, f.original_title AS title, f.budget, f.revenue, "
            "       (SELECT MIN(c.category_name) FROM film_genre fg "
            "        JOIN category c ON fg.category_id = c.category_id "
            "        WHERE fg.film_id = f.film_id "
            "          AND c.historic_subcategory_name IS NULL) AS category "
            "FROM film f "
            "WHERE f.budget IS NOT NULL AND f.budget > 0 "
            "  AND f.revenue IS NOT NULL AND f.revenue > 0 "
            "ORDER BY f.revenue DESC LIMIT 500"
        ),
    )

    return FinancialsStats(
        top_grossing=[
            {
                "film_id": r[0],
                "title": r[1],
                "poster_url": r[2],
                "year": r[3],
                "revenue": int(r[4]),
            }
            for r in top_grossing_rows
        ],
        top_budgets=[
            {
                "film_id": r[0],
                "title": r[1],
                "poster_url": r[2],
                "year": r[3],
                "budget": int(r[4]),
            }
            for r in top_budget_rows
        ],
        most_profitable=[
            {
                "film_id": r[0],
                "title": r[1],
                "poster_url": r[2],
                "year": r[3],
                "budget": int(r[4]),
                "revenue": int(r[5]),
                "ratio": float(r[6]),
            }
            for r in profitable_rows
        ],
        avg_budget_by_decade=[
            {
                "decade": int(r[0]),
                "avg_budget": int(r[1]),
                "film_count": int(r[2]),
            }
            for r in avg_budget_rows
        ],
        budget_revenue_scatter=[
            {
                "film_id": r[0],
                "title": r[1],
                "budget": int(r[2]),
                "revenue": int(r[3]),
                "category": r[4],
            }
            for r in scatter_rows
        ],
    )


def _gender_reshape(rows) -> dict[str, int]:
    out = {"M": 0, "F": 0, "unknown": 0}
    for r in rows:
        g = r[0]
        c = int(r[1])
        if g == "M":
            out["M"] = c
        elif g == "F":
            out["F"] = c
        else:
            out["unknown"] = out["unknown"] + c
    return out


# Normalize nationality variants (e.g. "U.S." vs "USA", "England" vs "UK")
_NAT_NORMALIZE_SQL = """
CASE
  WHEN p.nationality IN ('U.S.', 'U.S', 'U.S.A.', 'United States', 'United States of America', 'America') THEN 'USA'
  WHEN p.nationality IN ('England', 'Britain', 'Great Britain', 'United Kingdom', 'British') THEN 'UK'
  ELSE p.nationality
END
"""


def _top_role_sql(role: str | None, gender: str | None, via_casting: bool) -> str:
    """Build a top-N query for directors/composers (crew) or actors (casting)."""
    gender_filter = ""
    if gender == "M":
        gender_filter = " AND p.gender = 'M'"
    elif gender == "F":
        gender_filter = " AND p.gender = 'F'"

    if via_casting:
        return f"""
            SELECT p.person_id,
                   TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
                   p.photo_url, p.nationality, p.gender,
                   COUNT(*) AS film_count,
                   MIN(EXTRACT(YEAR FROM f.first_release_date)::int) AS first_year,
                   MAX(EXTRACT(YEAR FROM f.first_release_date)::int) AS last_year
            FROM casting ca
            JOIN person p ON ca.person_id = p.person_id
            JOIN film f ON ca.film_id = f.film_id
            WHERE f.first_release_date IS NOT NULL{gender_filter}
            GROUP BY p.person_id, p.firstname, p.lastname, p.photo_url, p.nationality, p.gender
            ORDER BY film_count DESC LIMIT 15
        """
    return f"""
        SELECT p.person_id,
               TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
               p.photo_url, p.nationality, p.gender,
               COUNT(*) AS film_count,
               MIN(EXTRACT(YEAR FROM f.first_release_date)::int) AS first_year,
               MAX(EXTRACT(YEAR FROM f.first_release_date)::int) AS last_year
        FROM crew c
        JOIN person p ON c.person_id = p.person_id
        JOIN person_job pj ON c.job_id = pj.job_id
        JOIN film f ON c.film_id = f.film_id
        WHERE pj.role_name = '{role}' AND f.first_release_date IS NOT NULL{gender_filter}
        GROUP BY p.person_id, p.firstname, p.lastname, p.photo_url, p.nationality, p.gender
        ORDER BY film_count DESC, last_year DESC LIMIT 15
    """


async def _build_people() -> PeopleStats:
    role_specs: list[tuple[str, str, bool, str | None]] = [
        ("directors", "Director", False, None),
        ("directors", "Director", False, "M"),
        ("directors", "Director", False, "F"),
        ("actors", "", True, None),
        ("actors", "", True, "M"),
        ("actors", "", True, "F"),
        ("composers", "Composer", False, None),
        ("composers", "Composer", False, "M"),
        ("composers", "Composer", False, "F"),
    ]
    role_queries = [
        _q(_top_role_sql(role_name or None, gender, via_cast))
        for (_, role_name, via_cast, gender) in role_specs
    ]

    (
        *role_results,
        dir_nat_rows,
        actor_nat_rows,
        gender_all_rows,
        gender_dir_rows,
        gender_actor_rows,
        dir_gender_decade_rows,
        living_dir_rows,
        living_actor_rows,
        dir_birth_decade_rows,
    ) = await asyncio.gather(
        *role_queries,
        _q(
            f"SELECT {_NAT_NORMALIZE_SQL} AS nat, COUNT(DISTINCT p.person_id) AS count "
            "FROM crew c "
            "JOIN person p ON c.person_id = p.person_id "
            "JOIN person_job pj ON c.job_id = pj.job_id "
            "WHERE pj.role_name = 'Director' AND p.nationality IS NOT NULL "
            f"GROUP BY {_NAT_NORMALIZE_SQL} ORDER BY count DESC LIMIT 15"
        ),
        _q(
            f"SELECT {_NAT_NORMALIZE_SQL} AS nat, COUNT(DISTINCT p.person_id) AS count "
            "FROM casting ca "
            "JOIN person p ON ca.person_id = p.person_id "
            "WHERE p.nationality IS NOT NULL "
            f"GROUP BY {_NAT_NORMALIZE_SQL} ORDER BY count DESC LIMIT 15"
        ),
        _q(
            "SELECT COALESCE(gender, 'unknown') AS g, COUNT(*) AS c "
            "FROM person GROUP BY COALESCE(gender, 'unknown')"
        ),
        _q(
            "SELECT COALESCE(p.gender, 'unknown') AS g, "
            "       COUNT(DISTINCT p.person_id) AS c "
            "FROM crew c "
            "JOIN person p ON c.person_id = p.person_id "
            "JOIN person_job pj ON c.job_id = pj.job_id "
            "WHERE pj.role_name = 'Director' "
            "GROUP BY COALESCE(p.gender, 'unknown')"
        ),
        _q(
            "SELECT COALESCE(p.gender, 'unknown') AS g, "
            "       COUNT(DISTINCT p.person_id) AS c "
            "FROM casting ca "
            "JOIN person p ON ca.person_id = p.person_id "
            "GROUP BY COALESCE(p.gender, 'unknown')"
        ),
        _q(
            "SELECT (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade, "
            "       COUNT(*) FILTER (WHERE p.gender = 'M') AS male, "
            "       COUNT(*) FILTER (WHERE p.gender = 'F') AS female "
            "FROM crew c "
            "JOIN person p ON c.person_id = p.person_id "
            "JOIN person_job pj ON c.job_id = pj.job_id "
            "JOIN film f ON c.film_id = f.film_id "
            "WHERE pj.role_name = 'Director' AND f.first_release_date IS NOT NULL "
            "GROUP BY decade ORDER BY decade"
        ),
        _q(
            "SELECT "
            "  COUNT(*) FILTER (WHERE p.date_of_death IS NULL AND p.date_of_birth IS NOT NULL) AS living, "
            "  COUNT(*) FILTER (WHERE p.date_of_death IS NOT NULL) AS deceased, "
            "  COUNT(*) FILTER (WHERE p.date_of_birth IS NULL) AS unknown "
            "FROM ( "
            "  SELECT DISTINCT p.person_id, p.date_of_birth, p.date_of_death "
            "  FROM crew c "
            "  JOIN person p ON c.person_id = p.person_id "
            "  JOIN person_job pj ON c.job_id = pj.job_id "
            "  WHERE pj.role_name = 'Director' "
            ") p"
        ),
        _q(
            "SELECT "
            "  COUNT(*) FILTER (WHERE p.date_of_death IS NULL AND p.date_of_birth IS NOT NULL) AS living, "
            "  COUNT(*) FILTER (WHERE p.date_of_death IS NOT NULL) AS deceased, "
            "  COUNT(*) FILTER (WHERE p.date_of_birth IS NULL) AS unknown "
            "FROM ( "
            "  SELECT DISTINCT p.person_id, p.date_of_birth, p.date_of_death "
            "  FROM casting ca "
            "  JOIN person p ON ca.person_id = p.person_id "
            ") p"
        ),
        _q(
            "SELECT (EXTRACT(YEAR FROM p.date_of_birth)::int / 10) * 10 AS birth_decade, "
            "       COUNT(DISTINCT p.person_id) AS count "
            "FROM crew c "
            "JOIN person p ON c.person_id = p.person_id "
            "JOIN person_job pj ON c.job_id = pj.job_id "
            "WHERE pj.role_name = 'Director' AND p.date_of_birth IS NOT NULL "
            "GROUP BY birth_decade ORDER BY birth_decade"
        ),
    )

    def _person_card(rows):
        return [
            {
                "person_id": r[0],
                "name": r[1],
                "photo_url": r[2],
                "nationality": r[3],
                "gender": r[4],
                "film_count": int(r[5]),
                "first_year": r[6],
                "last_year": r[7],
            }
            for r in rows
        ]

    def _living_dict(rows):
        if not rows:
            return {"living": 0, "deceased": 0, "unknown": 0}
        r = rows[0]
        return {
            "living": int(r[0] or 0),
            "deceased": int(r[1] or 0),
            "unknown": int(r[2] or 0),
        }

    # Build top_people from role_results in declared order
    filter_keys = ["all", "male", "female"]
    top_people: dict[str, dict[str, list[dict[str, Any]]]] = {
        "directors": {},
        "actors": {},
        "composers": {},
    }
    for idx, (role_key, _, _, _) in enumerate(role_specs):
        flt = filter_keys[idx % 3]
        top_people[role_key][flt] = _person_card(role_results[idx])

    return PeopleStats(
        top_people=top_people,
        top_director_nationalities=[
            {"nationality": r[0], "count": int(r[1])} for r in dir_nat_rows
        ],
        top_actor_nationalities=[
            {"nationality": r[0], "count": int(r[1])} for r in actor_nat_rows
        ],
        gender_split={
            "all": _gender_reshape(gender_all_rows),
            "directors": _gender_reshape(gender_dir_rows),
            "actors": _gender_reshape(gender_actor_rows),
        },
        directors_gender_by_decade=[
            {"decade": int(r[0]), "M": int(r[1]), "F": int(r[2])}
            for r in dir_gender_decade_rows
        ],
        living_status={
            "directors": _living_dict(living_dir_rows),
            "actors": _living_dict(living_actor_rows),
        },
        directors_by_birth_decade=[
            {"birth_decade": int(r[0]), "count": int(r[1])}
            for r in dir_birth_decade_rows
        ],
    )


async def _build_taxonomy() -> TaxonomyStats:
    (
        themes_rows,
        cat_dist_rows,
        atmos_rows,
        cat_heatmap_rows,
        cinema_rows,
        msg_heatmap_rows,
        atmos_cat_rows,
        msg_movement_rows,
    ) = await asyncio.gather(
        _q(
            "SELECT tc.theme_name AS name, COUNT(*) AS count "
            "FROM film_theme ft "
            "JOIN theme_context tc ON ft.theme_context_id = tc.theme_context_id "
            "WHERE tc.theme_name NOT LIKE '%: %' "
            "GROUP BY tc.theme_name ORDER BY count DESC LIMIT 20"
        ),
        _q(
            "SELECT c.category_name AS name, COUNT(*) AS count "
            "FROM film_genre fg JOIN category c ON fg.category_id = c.category_id "
            "WHERE c.historic_subcategory_name IS NULL "
            "GROUP BY c.category_name ORDER BY count DESC"
        ),
        _q(
            "SELECT a.atmosphere_name AS name, COUNT(*) AS count "
            "FROM film_atmosphere fa "
            "JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id "
            "GROUP BY a.atmosphere_name ORDER BY count DESC LIMIT 30"
        ),
        # 1a. Category × decade — % of decade's films (distinct film_id),
        # so a film tagged with 3 genres no longer triple-counts.
        _q(
            """
            WITH decade_totals AS (
              SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
                     COUNT(*) AS total
              FROM film
              WHERE first_release_date IS NOT NULL
              GROUP BY decade
            ),
            category_decade AS (
              SELECT c.category_name AS category,
                     (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
                     COUNT(DISTINCT f.film_id) AS film_count
              FROM film_genre fg
              JOIN category c ON fg.category_id = c.category_id
              JOIN film f ON fg.film_id = f.film_id
              WHERE c.historic_subcategory_name IS NULL
                AND f.first_release_date IS NOT NULL
              GROUP BY c.category_name, decade
            )
            SELECT cd.category, cd.decade, cd.film_count,
                   dt.total AS decade_total,
                   ROUND((cd.film_count::numeric / dt.total) * 100, 2) AS pct
            FROM category_decade cd
            JOIN decade_totals dt ON cd.decade = dt.decade
            WHERE dt.total >= 5
            ORDER BY cd.category, cd.decade
            """
        ),
        # 1b. Cinema movements × decade — count-based, curated subset.
        _q(
            """
            SELECT ct.technique_name AS movement,
                   (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
                   COUNT(DISTINCT f.film_id) AS count,
                   ct.sort_order
            FROM film_technique fte
            JOIN cinema_type ct ON fte.cinema_type_id = ct.cinema_type_id
            JOIN film f ON fte.film_id = f.film_id
            WHERE ct.technique_name = ANY(:movement_names)
              AND f.first_release_date IS NOT NULL
            GROUP BY ct.technique_name, decade, ct.sort_order
            ORDER BY ct.sort_order, decade
            """,
            {"movement_names": CINEMA_MOVEMENT_NAMES},
        ),
        # 1c. Messages × decade — % within decade.
        _q(
            """
            WITH decade_totals AS (
              SELECT (EXTRACT(YEAR FROM first_release_date)::int / 10) * 10 AS decade,
                     COUNT(*) AS total
              FROM film
              WHERE first_release_date IS NOT NULL
              GROUP BY decade
              HAVING COUNT(*) >= 20
            ),
            message_totals AS (
              SELECT mc.message_id, mc.message_name, mc.sort_order,
                     COUNT(DISTINCT fm.film_id) AS total_count
              FROM message_conveyed mc
              LEFT JOIN film_message fm ON mc.message_id = fm.message_id
              GROUP BY mc.message_id, mc.message_name, mc.sort_order
              HAVING COUNT(DISTINCT fm.film_id) >= 5
            ),
            message_decade AS (
              SELECT mc.message_name AS message,
                     mc.sort_order,
                     (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade,
                     COUNT(DISTINCT f.film_id) AS film_count
              FROM film_message fm
              JOIN message_conveyed mc ON fm.message_id = mc.message_id
              JOIN film f ON fm.film_id = f.film_id
              WHERE f.first_release_date IS NOT NULL
                AND mc.message_id IN (SELECT message_id FROM message_totals)
              GROUP BY mc.message_name, mc.sort_order, decade
            )
            SELECT md.message, md.decade, md.film_count,
                   dt.total AS decade_total,
                   ROUND((md.film_count::numeric / dt.total) * 100, 2) AS pct,
                   md.sort_order
            FROM message_decade md
            JOIN decade_totals dt ON md.decade = dt.decade
            ORDER BY md.sort_order, md.decade
            """
        ),
        # 1d. Atmosphere × category — % within category.
        _q(
            """
            WITH category_totals AS (
              SELECT c.category_name AS category, COUNT(DISTINCT fg.film_id) AS total
              FROM film_genre fg
              JOIN category c ON fg.category_id = c.category_id
              WHERE c.historic_subcategory_name IS NULL
              GROUP BY c.category_name
            ),
            ca AS (
              SELECT c.category_name AS category,
                     a.atmosphere_name AS atmosphere,
                     a.sort_order AS atmosphere_sort_order,
                     COUNT(DISTINCT fg.film_id) AS film_count
              FROM film_genre fg
              JOIN category c ON fg.category_id = c.category_id
              JOIN film_atmosphere fa ON fg.film_id = fa.film_id
              JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id
              WHERE c.historic_subcategory_name IS NULL
              GROUP BY c.category_name, a.atmosphere_name, a.sort_order
            )
            SELECT ca.category, ca.atmosphere, ca.atmosphere_sort_order,
                   ca.film_count, ct.total AS category_total,
                   ROUND((ca.film_count::numeric / ct.total) * 100, 2) AS pct
            FROM ca
            JOIN category_totals ct ON ca.category = ct.category
            ORDER BY ca.category, ca.atmosphere_sort_order
            """
        ),
        # 1e. Message × cinema movement — % within movement.
        # Rows = curated movement list, cols = all messages with ≥ 1 film
        # in any of those movements. Movements without any tagged films are
        # filtered out by the JOIN.
        _q(
            """
            WITH movement_totals AS (
              SELECT ct.technique_name AS movement,
                     ct.sort_order AS movement_sort_order,
                     COUNT(DISTINCT fte.film_id) AS total
              FROM film_technique fte
              JOIN cinema_type ct ON fte.cinema_type_id = ct.cinema_type_id
              WHERE ct.technique_name = ANY(:movement_names)
              GROUP BY ct.technique_name, ct.sort_order
              HAVING COUNT(DISTINCT fte.film_id) > 0
            ),
            mm AS (
              SELECT ct.technique_name AS movement,
                     ct.sort_order AS movement_sort_order,
                     mc.message_name AS message,
                     mc.sort_order AS message_sort_order,
                     COUNT(DISTINCT fte.film_id) AS film_count
              FROM film_technique fte
              JOIN cinema_type ct ON fte.cinema_type_id = ct.cinema_type_id
              JOIN film_message fm ON fte.film_id = fm.film_id
              JOIN message_conveyed mc ON fm.message_id = mc.message_id
              WHERE ct.technique_name = ANY(:movement_names)
              GROUP BY ct.technique_name, ct.sort_order, mc.message_name, mc.sort_order
            )
            SELECT mm.movement, mm.movement_sort_order,
                   mm.message, mm.message_sort_order,
                   mm.film_count, mt.total AS movement_total,
                   ROUND((mm.film_count::numeric / mt.total) * 100, 2) AS pct
            FROM mm
            JOIN movement_totals mt ON mm.movement = mt.movement
            ORDER BY mm.movement_sort_order, mm.message_sort_order
            """,
            {"movement_names": CINEMA_MOVEMENT_NAMES},
        ),
    )

    return TaxonomyStats(
        top_themes=[{"name": r[0], "count": int(r[1])} for r in themes_rows],
        category_distribution=[
            {"name": r[0], "count": int(r[1])} for r in cat_dist_rows
        ],
        top_atmospheres=[{"name": r[0], "count": int(r[1])} for r in atmos_rows],
        category_by_decade_heatmap=[
            {
                "category": r[0],
                "decade": int(r[1]),
                "film_count": int(r[2]),
                "decade_total": int(r[3]),
                "pct": float(r[4]),
            }
            for r in cat_heatmap_rows
        ],
        cinema_movements_by_decade=[
            {
                "movement": r[0],
                "decade": int(r[1]),
                "count": int(r[2]),
                "sort_order": int(r[3]) if r[3] is not None else 0,
            }
            for r in cinema_rows
        ],
        message_by_decade_heatmap=[
            {
                "message": r[0],
                "decade": int(r[1]),
                "film_count": int(r[2]),
                "decade_total": int(r[3]),
                "pct": float(r[4]),
                "sort_order": int(r[5]) if r[5] is not None else 0,
            }
            for r in msg_heatmap_rows
        ],
        atmosphere_by_category=[
            {
                "category": r[0],
                "atmosphere": r[1],
                "atmosphere_sort_order": int(r[2]) if r[2] is not None else 0,
                "film_count": int(r[3]),
                "category_total": int(r[4]),
                "pct": float(r[5]),
            }
            for r in atmos_cat_rows
        ],
        message_by_movement=[
            {
                "movement": r[0],
                "movement_sort_order": int(r[1]) if r[1] is not None else 0,
                "message": r[2],
                "message_sort_order": int(r[3]) if r[3] is not None else 0,
                "film_count": int(r[4]),
                "movement_total": int(r[5]),
                "pct": float(r[6]),
            }
            for r in msg_movement_rows
        ],
    )


async def _build_geography() -> GeographyPayload:
    """Geography tab payload — production countries + set-place breakdowns."""
    (
        production_rows,
        set_place_country_rows,
        treemap_rows,
        production_total_rows,
        set_place_total_rows,
        most_intl_rows,
    ) = await asyncio.gather(
        # 2a. Production countries — ISO codes already present.
        _q(
            """
            SELECT pc.country_code AS iso,
                   pc.country_name AS country,
                   COUNT(DISTINCT fpc.film_id) AS film_count
            FROM production_country pc
            JOIN film_production_country fpc ON pc.country_id = fpc.country_id
            GROUP BY pc.country_code, pc.country_name
            ORDER BY film_count DESC, country
            """
        ),
        # 2b. Set-place — free-text country names from `geography`. ISO is
        # resolved in Python below.
        _q(
            """
            SELECT g.country, COUNT(DISTINCT fsp.film_id) AS film_count
            FROM geography g
            JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
            WHERE g.country IS NOT NULL
            GROUP BY g.country
            ORDER BY film_count DESC, g.country
            """
        ),
        # 2c. Set-place hierarchical treemap data.
        _q(
            """
            SELECT g.continent, g.country, g.state_city, g.geography_id,
                   COUNT(DISTINCT fsp.film_id) AS film_count
            FROM geography g
            JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
            WHERE g.continent IS NOT NULL
            GROUP BY g.continent, g.country, g.state_city, g.geography_id
            ORDER BY g.continent, g.country, g.state_city
            """
        ),
        # 2d. Distinct country totals.
        _q("SELECT COUNT(DISTINCT country_id) FROM film_production_country"),
        _q(
            """
            SELECT COUNT(DISTINCT country) FROM geography
            WHERE country IS NOT NULL
              AND geography_id IN (SELECT geography_id FROM film_set_place)
            """
        ),
        # 2e. Most international film.
        _q(
            """
            SELECT fpc.film_id, f.original_title AS title,
                   f.poster_url,
                   EXTRACT(YEAR FROM f.first_release_date)::int AS year,
                   COUNT(*) AS country_count,
                   array_agg(pc.country_code ORDER BY pc.country_code) AS countries
            FROM film_production_country fpc
            JOIN film f ON fpc.film_id = f.film_id
            JOIN production_country pc ON fpc.country_id = pc.country_id
            GROUP BY fpc.film_id, f.original_title, f.poster_url, f.first_release_date
            ORDER BY country_count DESC, f.original_title
            LIMIT 1
            """
        ),
    )

    # production_countries — fold legacy ISO codes (SU→RU, YU→RS, CS→CZ,
    # DD→DE) into their modern successors so the world map can show them.
    production_by_iso: dict[str, int] = {}
    production_canonical_name: dict[str, str] = {}
    for raw_iso, raw_name, count in production_rows:
        if not raw_iso:
            continue
        iso = normalize_iso(raw_iso) or raw_iso
        production_by_iso[iso] = production_by_iso.get(iso, 0) + int(count)
        # Prefer the modern successor's name; only keep the legacy name as a
        # fallback if no modern row has been seen yet.
        if iso not in production_canonical_name or raw_iso == iso:
            production_canonical_name[iso] = raw_name

    production_countries = [
        ProductionCountryCell(
            iso=iso,
            country=production_canonical_name.get(iso) or preferred_country_name(iso),
            film_count=count,
        )
        for iso, count in sorted(
            production_by_iso.items(), key=lambda kv: (-kv[1], kv[0])
        )
    ]
    iso_to_canonical = {r.iso: r.country for r in production_countries}

    # set_place_countries — resolve free-text → ISO, then aggregate by ISO.
    set_place_by_iso: dict[str, int] = {}
    for country_name, count in set_place_country_rows:
        iso = country_name_to_iso(country_name)
        if iso is None:
            continue
        set_place_by_iso[iso] = set_place_by_iso.get(iso, 0) + int(count)

    set_place_countries = [
        SetPlaceCountryCell(
            iso=iso,
            country=iso_to_canonical.get(iso) or preferred_country_name(iso),
            film_count=count,
        )
        for iso, count in sorted(
            set_place_by_iso.items(), key=lambda kv: (-kv[1], kv[0])
        )
    ]

    set_place_treemap = [
        SetPlaceTreemapCell(
            continent=r[0],
            country=r[1],
            state_city=r[2],
            geography_id=int(r[3]),
            film_count=int(r[4]),
        )
        for r in treemap_rows
    ]

    # Use the deduplicated post-merge counts. The raw SQL totals would
    # double-count legacy/modern pairs (e.g. SU + RU as two entries) and the
    # set-place SQL total counts free-text variants (e.g. "USSR" and "Soviet
    # Union" as two distinct countries), which is misleading.
    production_country_total = len(production_countries)
    set_place_country_total = len(set_place_countries)
    # set_place_total_rows is kept fetched for backwards compatibility but
    # intentionally ignored.
    _ = set_place_total_rows
    _ = production_total_rows

    most_intl: MostInternationalFilm | None = None
    if most_intl_rows:
        r = most_intl_rows[0]
        most_intl = MostInternationalFilm(
            film_id=int(r[0]),
            title=r[1],
            poster_url=r[2],
            year=r[3],
            country_count=int(r[4]),
            countries=list(r[5]) if r[5] is not None else [],
        )

    return GeographyPayload(
        production_countries=production_countries,
        set_place_countries=set_place_countries,
        set_place_treemap=set_place_treemap,
        production_country_total=production_country_total,
        set_place_country_total=set_place_country_total,
        most_international_film=most_intl,
    )


async def _build_personal(user_id: str, total_films: int) -> PersonalStats:
    params = {"uid": user_id}
    (
        seen_rows,
        fav_rows,
        watch_rows,
        rated_rows,
        avg_rows,
        seen_decade_rows,
        seen_cat_rows,
    ) = await asyncio.gather(
        _q(
            "SELECT COUNT(*) FROM user_film_status "
            "WHERE user_id = :uid AND seen = TRUE",
            params,
        ),
        _q(
            "SELECT COUNT(*) FROM user_film_status "
            "WHERE user_id = :uid AND favorite = TRUE",
            params,
        ),
        _q(
            "SELECT COUNT(*) FROM user_film_status "
            "WHERE user_id = :uid AND watchlist = TRUE",
            params,
        ),
        _q(
            "SELECT COUNT(*) FROM user_film_status "
            "WHERE user_id = :uid AND rating IS NOT NULL",
            params,
        ),
        _q(
            "SELECT AVG(rating)::float FROM user_film_status "
            "WHERE user_id = :uid AND rating IS NOT NULL",
            params,
        ),
        _q(
            "SELECT (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade, "
            "       COUNT(*) AS count "
            "FROM user_film_status u JOIN film f ON u.film_id = f.film_id "
            "WHERE u.user_id = :uid AND u.seen = TRUE AND f.first_release_date IS NOT NULL "
            "GROUP BY decade ORDER BY decade",
            params,
        ),
        _q(
            "SELECT c.category_name AS name, COUNT(*) AS count "
            "FROM user_film_status u "
            "JOIN film_genre fg ON u.film_id = fg.film_id "
            "JOIN category c ON fg.category_id = c.category_id "
            "WHERE u.user_id = :uid AND u.seen = TRUE "
            "  AND c.historic_subcategory_name IS NULL "
            "GROUP BY c.category_name ORDER BY count DESC LIMIT 10",
            params,
        ),
    )

    seen_count = int(seen_rows[0][0]) if seen_rows else 0
    unseen = max(total_films - seen_count, 0)
    seen_pct = round((seen_count / total_films * 100), 1) if total_films else 0.0
    avg_rating = avg_rows[0][0] if avg_rows and avg_rows[0][0] is not None else None

    return PersonalStats(
        seen_count=seen_count,
        unseen_count=unseen,
        seen_pct=seen_pct,
        favorite_count=int(fav_rows[0][0]) if fav_rows else 0,
        watchlist_count=int(watch_rows[0][0]) if watch_rows else 0,
        rated_count=int(rated_rows[0][0]) if rated_rows else 0,
        avg_rating=round(float(avg_rating), 2) if avg_rating is not None else None,
        seen_by_decade=[
            {"decade": int(r[0]), "count": int(r[1])} for r in seen_decade_rows
        ],
        top_seen_categories=[
            {"name": r[0], "count": int(r[1])} for r in seen_cat_rows
        ],
    )


# =============================================================================
# Endpoint
# =============================================================================


@router.get("/stats/dashboard", response_model=DashboardResponse)
async def get_dashboard(user: UserInfo | None = Depends(get_current_user)):
    tier = user.tier if user else "anonymous"

    show_financials = tier in ("free", "pro", "admin")
    show_people = tier in ("pro", "admin")
    show_taxonomy = tier in ("pro", "admin")
    show_geography = tier in ("pro", "admin")
    show_personal = user is not None and tier in ("pro", "admin")

    tasks = [_build_quick()]
    if show_financials:
        tasks.append(_build_financials())
    if show_people:
        tasks.append(_build_people())
    if show_taxonomy:
        tasks.append(_build_taxonomy())
    if show_geography:
        tasks.append(_build_geography())

    results = await asyncio.gather(*tasks)

    idx = 0
    quick = results[idx]
    idx += 1
    financials = results[idx] if show_financials else None
    if show_financials:
        idx += 1
    people = results[idx] if show_people else None
    if show_people:
        idx += 1
    taxonomy = results[idx] if show_taxonomy else None
    if show_taxonomy:
        idx += 1
    geography = results[idx] if show_geography else None
    if show_geography:
        idx += 1

    personal = None
    if show_personal:
        personal = await _build_personal(user.id, quick.total_films)

    return DashboardResponse(
        tier=tier,
        quick=quick,
        geography=geography,
        financials=financials,
        people=people,
        taxonomy=taxonomy,
        personal_stats=personal,
    )


# =============================================================================
# Person filmography tag breakdown (Step 17c)
# =============================================================================


_PERSON_ROLES = ("director", "composer", "actor")


def _validate_role(role: str) -> str:
    if role not in _PERSON_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Must be one of: {', '.join(_PERSON_ROLES)}",
        )
    return role


@router.get("/stats/people-with-films", response_model=list[PersonSearchResult])
async def people_with_films(
    role: str = Query("director"),
    q: str | None = Query(None),
    user: UserInfo | None = Depends(get_current_user),
):
    """Autocomplete-friendly list of people in a given role with ≥ 3 films."""
    _require_pro(user)
    _validate_role(role)

    # Pre-format the LIKE pattern in Python — avoids an asyncpg type-inference
    # quirk where `'%' || :q || '%'` raises ambiguous-type errors and the
    # endpoint silently 500s.
    pattern = f"%{q.strip()}%" if q and q.strip() else "%"

    if role == "actor":
        # casting is implicitly the actor table — no role_name filter needed.
        sql = """
            SELECT p.person_id,
                   TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
                   COUNT(DISTINCT ca.film_id) AS film_count
            FROM casting ca
            JOIN person p ON ca.person_id = p.person_id
            WHERE (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE :pattern
            GROUP BY p.person_id, p.firstname, p.lastname
            HAVING COUNT(DISTINCT ca.film_id) >= 3
            ORDER BY film_count DESC, name
            LIMIT 30
        """
        params: dict = {"pattern": pattern}
    else:
        role_name = "Director" if role == "director" else "Composer"
        sql = """
            SELECT p.person_id,
                   TRIM(COALESCE(p.firstname, '') || ' ' || p.lastname) AS name,
                   COUNT(DISTINCT c.film_id) AS film_count
            FROM crew c
            JOIN person p ON c.person_id = p.person_id
            JOIN person_job pj ON c.job_id = pj.job_id
            WHERE pj.role_name = :role_name
              AND (COALESCE(p.firstname, '') || ' ' || p.lastname) ILIKE :pattern
            GROUP BY p.person_id, p.firstname, p.lastname
            HAVING COUNT(DISTINCT c.film_id) >= 3
            ORDER BY film_count DESC, name
            LIMIT 30
        """
        params = {"role_name": role_name, "pattern": pattern}

    rows = await _q(sql, params)
    return [
        PersonSearchResult(person_id=r[0], name=r[1], film_count=int(r[2]))
        for r in rows
    ]


# WITH-CTE clause shared by all 4 per-person tag queries.
# Resolves the set of film_ids this person is credited on for the given role.
_PERSON_FILMS_CTE_CREW = """
WITH person_films AS (
  SELECT DISTINCT c.film_id
  FROM crew c
  JOIN person_job pj ON c.job_id = pj.job_id
  WHERE c.person_id = :pid AND pj.role_name = :role_name
)
"""

_PERSON_FILMS_CTE_CASTING = """
WITH person_films AS (
  SELECT DISTINCT film_id
  FROM casting
  WHERE person_id = :pid
)
"""


@router.get("/stats/person-tags", response_model=PersonTagsResponse)
async def person_tags(
    person_id: int = Query(..., alias="person_id"),
    role: str = Query("director"),
    user: UserInfo | None = Depends(get_current_user),
):
    """Top tags across one person's filmography in a given role."""
    _require_pro(user)
    _validate_role(role)

    # 1. Validate person exists and get name.
    person_rows = await _q(
        "SELECT person_id, "
        "       TRIM(COALESCE(firstname, '') || ' ' || lastname) AS name "
        "FROM person WHERE person_id = :pid",
        {"pid": person_id},
    )
    if not person_rows:
        raise HTTPException(status_code=404, detail="Person not found")
    pname = person_rows[0][1]

    # 2. Resolve film count (also tells us whether to skip the tag queries).
    if role == "actor":
        cte = _PERSON_FILMS_CTE_CASTING
        cte_params: dict = {"pid": person_id}
    else:
        cte = _PERSON_FILMS_CTE_CREW
        cte_params = {
            "pid": person_id,
            "role_name": "Director" if role == "director" else "Composer",
        }

    count_rows = await _q(
        f"{cte} SELECT COUNT(*) FROM person_films",
        cte_params,
    )
    film_count = int(count_rows[0][0]) if count_rows else 0

    if film_count == 0:
        return PersonTagsResponse(
            person=PersonRef(person_id=person_id, name=pname, film_count=0),
            top_themes=[],
            top_atmospheres=[],
            top_characters=[],
            top_messages=[],
        )

    # 3. Four parallel tag queries scoped to person_films.
    themes_q = f"""
        {cte}
        SELECT tc.theme_name AS name, COUNT(DISTINCT ft.film_id) AS count
        FROM film_theme ft
        JOIN theme_context tc ON ft.theme_context_id = tc.theme_context_id
        WHERE ft.film_id IN (SELECT film_id FROM person_films)
          AND tc.theme_name NOT LIKE '%: %'
        GROUP BY tc.theme_name
        ORDER BY count DESC, tc.theme_name
        LIMIT 8
    """
    atmos_q = f"""
        {cte}
        SELECT a.atmosphere_name AS name, COUNT(DISTINCT fa.film_id) AS count
        FROM film_atmosphere fa
        JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id
        WHERE fa.film_id IN (SELECT film_id FROM person_films)
        GROUP BY a.atmosphere_name
        ORDER BY count DESC, a.atmosphere_name
        LIMIT 5
    """
    chars_q = f"""
        {cte}
        SELECT cc.context_name AS name, COUNT(DISTINCT fcc.film_id) AS count
        FROM film_character_context fcc
        JOIN character_context cc ON fcc.character_context_id = cc.character_context_id
        WHERE fcc.film_id IN (SELECT film_id FROM person_films)
        GROUP BY cc.context_name
        ORDER BY count DESC, cc.context_name
        LIMIT 5
    """
    msgs_q = f"""
        {cte}
        SELECT mc.message_name AS name, COUNT(DISTINCT fm.film_id) AS count
        FROM film_message fm
        JOIN message_conveyed mc ON fm.message_id = mc.message_id
        WHERE fm.film_id IN (SELECT film_id FROM person_films)
        GROUP BY mc.message_name
        ORDER BY count DESC, mc.message_name
        LIMIT 3
    """

    themes_rows, atmos_rows, chars_rows, msgs_rows = await asyncio.gather(
        _q(themes_q, cte_params),
        _q(atmos_q, cte_params),
        _q(chars_q, cte_params),
        _q(msgs_q, cte_params),
    )

    return PersonTagsResponse(
        person=PersonRef(person_id=person_id, name=pname, film_count=film_count),
        top_themes=[TagCount(name=r[0], count=int(r[1])) for r in themes_rows],
        top_atmospheres=[TagCount(name=r[0], count=int(r[1])) for r in atmos_rows],
        top_characters=[TagCount(name=r[0], count=int(r[1])) for r in chars_rows],
        top_messages=[TagCount(name=r[0], count=int(r[1])) for r in msgs_rows],
    )


# =============================================================================
# Films by country (Step 17d) — drives the country click-panel on the maps.
# =============================================================================


_FILM_BY_COUNTRY_TYPES = ("production", "set_place")


@router.get("/stats/films-by-country", response_model=list[FilmByCountry])
async def films_by_country(
    type: str = Query(..., description="'production' or 'set_place'"),
    iso: str = Query(..., min_length=2, max_length=2),
    limit: int = Query(10, ge=1, le=30),
    user: UserInfo | None = Depends(get_current_user),
):
    """Top films associated with a country, sorted by weighted_score.

    `type=production` matches against production_country.country_code directly.
    `type=set_place` reverse-resolves the ISO to its free-text variants and
    matches LOWER(geography.country) against them.
    """
    _require_pro(user)
    if type not in _FILM_BY_COUNTRY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Must be one of: {', '.join(_FILM_BY_COUNTRY_TYPES)}",
        )

    iso_upper = normalize_iso(iso.upper()) or iso.upper()

    if type == "production":
        # Include legacy aliases (e.g. clicking RU also pulls SU = Soviet
        # Union films, since TMDB sometimes tags them with the defunct code).
        iso_aliases = [
            legacy for legacy, modern in LEGACY_ISO_ALIASES.items() if modern == iso_upper
        ]
        iso_set = [iso_upper, *iso_aliases]
        sql = """
            SELECT f.film_id, f.original_title AS title, f.poster_url,
                   EXTRACT(YEAR FROM f.first_release_date)::int AS year,
                   f.weighted_score
            FROM film f
            JOIN film_production_country fpc ON f.film_id = fpc.film_id
            JOIN production_country pc ON fpc.country_id = pc.country_id
            WHERE pc.country_code = ANY(:iso_set)
            ORDER BY f.weighted_score DESC NULLS LAST, f.first_release_date DESC
            LIMIT :limit
        """
        rows = await _q(sql, {"iso_set": iso_set, "limit": limit})
    else:
        # set_place — reverse-lookup ISO to free-text variants.
        names = iso_to_country_names(iso_upper)
        if not names:
            return []
        sql = """
            SELECT DISTINCT f.film_id, f.original_title AS title, f.poster_url,
                   EXTRACT(YEAR FROM f.first_release_date)::int AS year,
                   f.weighted_score
            FROM film f
            JOIN film_set_place fsp ON f.film_id = fsp.film_id
            JOIN geography g ON fsp.geography_id = g.geography_id
            WHERE LOWER(g.country) = ANY(:names)
            ORDER BY f.weighted_score DESC NULLS LAST, year DESC NULLS LAST
            LIMIT :limit
        """
        rows = await _q(sql, {"names": names, "limit": limit})

    return [
        FilmByCountry(
            film_id=int(r[0]),
            title=r[1],
            poster_url=r[2],
            year=r[3],
            weighted_score=float(r[4]) if r[4] is not None else None,
        )
        for r in rows
    ]
