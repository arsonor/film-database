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

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from backend.app.auth import UserInfo, get_current_user
from backend.app.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()


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
    category_by_decade_heatmap: list[dict[str, Any]]


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
    geography: dict[str, Any] | None
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
        heatmap_rows,
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
        _q(
            "SELECT c.category_name AS category, "
            "       (EXTRACT(YEAR FROM f.first_release_date)::int / 10) * 10 AS decade, "
            "       COUNT(*) AS count "
            "FROM film_genre fg "
            "JOIN category c ON fg.category_id = c.category_id "
            "JOIN film f ON fg.film_id = f.film_id "
            "WHERE c.historic_subcategory_name IS NULL "
            "  AND f.first_release_date IS NOT NULL "
            "GROUP BY c.category_name, decade "
            "ORDER BY c.category_name, decade"
        ),
    )

    return TaxonomyStats(
        top_themes=[{"name": r[0], "count": int(r[1])} for r in themes_rows],
        category_distribution=[
            {"name": r[0], "count": int(r[1])} for r in cat_dist_rows
        ],
        top_atmospheres=[{"name": r[0], "count": int(r[1])} for r in atmos_rows],
        category_by_decade_heatmap=[
            {"category": r[0], "decade": int(r[1]), "count": int(r[2])}
            for r in heatmap_rows
        ],
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
    show_personal = user is not None and tier in ("pro", "admin")

    tasks = [_build_quick()]
    if show_financials:
        tasks.append(_build_financials())
    if show_people:
        tasks.append(_build_people())
    if show_taxonomy:
        tasks.append(_build_taxonomy())

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

    personal = None
    if show_personal:
        personal = await _build_personal(user.id, quick.total_films)

    return DashboardResponse(
        tier=tier,
        quick=quick,
        geography=None,
        financials=financials,
        people=people,
        taxonomy=taxonomy,
        personal_stats=personal,
    )
