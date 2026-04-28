"""
Similar-films recommender using IDF-weighted Jaccard similarity
across 9 taxonomy dimensions plus structural bonuses.
"""

import logging
import math
import time

from cachetools import TTLCache
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Tunable constants ──────────────────────────────────────────────────────

DIMENSION_WEIGHTS: dict[str, float] = {
    "atmospheres": 1.4,
    "themes": 1.3,
    "motivations": 1.1,
    "messages": 1.0,
    "cinema_types": 1.0,
    "characters": 0.9,
    "categories": 0.7,
    "place_contexts": 0.6,
    "time_periods": 0.5,
}

BONUS_DIRECTOR = 0.10
BONUS_STUDIO_DECADE = 0.03
BONUS_QUALITY_MAX = 0.05

IDF_CACHE_TTL_HOURS = 24

# junction table / lookup table mapping per dimension
_DIM_SQL: dict[str, tuple[str, str, str, str]] = {
    "categories":    ("film_genre",             "category_id",         "category",           "category_name"),
    "cinema_types":  ("film_technique",         "cinema_type_id",      "cinema_type",        "technique_name"),
    "themes":        ("film_theme",             "theme_context_id",    "theme_context",      "theme_name"),
    "characters":    ("film_character_context",  "character_context_id","character_context",  "context_name"),
    "atmospheres":   ("film_atmosphere",         "atmosphere_id",       "atmosphere",         "atmosphere_name"),
    "messages":      ("film_message",            "message_id",          "message_conveyed",   "message_name"),
    "motivations":   ("film_motivation",         "motivation_id",       "motivation_relation","motivation_name"),
    "time_periods":  ("film_period",             "time_context_id",     "time_context",       "time_period"),
    "place_contexts":("film_place",              "place_context_id",    "place_context",      "environment"),
}

# ── IDF cache ──────────────────────────────────────────────────────────────

_idf_map: dict[str, dict[str, float]] | None = None
_idf_ts: float = 0.0
_total_films: int = 0


def invalidate_idf():
    global _idf_map, _idf_ts
    _idf_map = None
    _idf_ts = 0.0


async def _ensure_idf(db: AsyncSession) -> dict[str, dict[str, float]]:
    global _idf_map, _idf_ts, _total_films

    now = time.time()
    if _idf_map is not None and (now - _idf_ts) < IDF_CACHE_TTL_HOURS * 3600:
        return _idf_map

    r = await db.execute(text("SELECT COUNT(*) FROM film"))
    _total_films = r.scalar_one()
    if _total_films == 0:
        _idf_map = {}
        _idf_ts = now
        return _idf_map

    idf: dict[str, dict[str, float]] = {}
    for dim, (junc, junc_fk, lookup, name_col) in _DIM_SQL.items():
        r = await db.execute(text(
            f"SELECT lt.{name_col}, COUNT(DISTINCT jt.film_id) "
            f"FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"GROUP BY lt.{name_col}"
        ))
        dim_idf: dict[str, float] = {}
        for tag_name, cnt in r.fetchall():
            dim_idf[tag_name] = math.log(_total_films / cnt) if cnt > 0 else 0.0
        idf[dim] = dim_idf

    _idf_map = idf
    _idf_ts = now
    logger.info("IDF map rebuilt: %d dimensions, %d total films",
                len(idf), _total_films)
    return _idf_map


# ── Per-film similarity cache ─────────────────────────────────────────────

_sim_cache: TTLCache = TTLCache(maxsize=2000, ttl=3600)


def invalidate_film(film_id: int):
    keys_to_remove = [k for k in _sim_cache if k[0] == film_id]
    for k in keys_to_remove:
        _sim_cache.pop(k, None)


# ── Core algorithm ─────────────────────────────────────────────────────────


def _idf_jaccard(
    source_tags: set[str],
    candidate_tags: set[str],
    idf_dim: dict[str, float],
) -> float:
    shared = source_tags & candidate_tags
    union = source_tags | candidate_tags
    if not union:
        return 0.0
    num = sum(idf_dim.get(t, 1.0) for t in shared)
    den = sum(idf_dim.get(t, 1.0) for t in union)
    return num / den if den > 0 else 0.0


async def get_similar_films(
    db: AsyncSession,
    film_id: int,
    limit: int,
    tier: str,
) -> list[dict]:
    cache_key = (film_id, limit, tier)
    cached = _sim_cache.get(cache_key)
    if cached is not None:
        return cached

    idf_map = await _ensure_idf(db)

    # 1. Load source film tags per dimension
    source_tags: dict[str, set[str]] = {}
    for dim, (junc, junc_fk, lookup, name_col) in _DIM_SQL.items():
        r = await db.execute(text(
            f"SELECT lt.{name_col} "
            f"FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE jt.film_id = :fid"
        ), {"fid": film_id})
        source_tags[dim] = {row[0] for row in r.fetchall()}

    # 2. Get excluded film_ids (self + film_sequel relations in both directions)
    r = await db.execute(text(
        "SELECT related_film_id FROM film_sequel WHERE film_id = :fid "
        "UNION "
        "SELECT film_id FROM film_sequel WHERE related_film_id = :fid"
    ), {"fid": film_id})
    excluded = {film_id} | {row[0] for row in r.fetchall()}

    # 3. Get source film's directors and studios+decade for bonuses
    r = await db.execute(text(
        "SELECT p.person_id FROM crew cr "
        "JOIN person_job pj ON cr.job_id = pj.job_id "
        "JOIN person p ON cr.person_id = p.person_id "
        "WHERE cr.film_id = :fid AND pj.role_name = 'Director'"
    ), {"fid": film_id})
    source_director_ids = {row[0] for row in r.fetchall()}

    r = await db.execute(text(
        "SELECT s.studio_id FROM production pr "
        "JOIN studio s ON pr.studio_id = s.studio_id "
        "WHERE pr.film_id = :fid"
    ), {"fid": film_id})
    source_studio_ids = {row[0] for row in r.fetchall()}

    r = await db.execute(text(
        "SELECT EXTRACT(YEAR FROM first_release_date)::int / 10 AS decade, "
        "weighted_score FROM film WHERE film_id = :fid"
    ), {"fid": film_id})
    src_row = r.fetchone()
    source_decade = src_row[0] if src_row and src_row[0] is not None else None
    source_ws = float(src_row[1]) if src_row and src_row[1] is not None else None

    # 4. Find candidate films: any film sharing at least one tag in any dimension
    candidate_ids_sql_parts = []
    for dim, (junc, junc_fk, lookup, name_col) in _DIM_SQL.items():
        tags = source_tags.get(dim, set())
        if not tags:
            continue
        candidate_ids_sql_parts.append(
            f"SELECT DISTINCT jt.film_id FROM {junc} jt "
            f"JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE lt.{name_col} = ANY(:tags_{dim})"
        )

    if not candidate_ids_sql_parts:
        _sim_cache[cache_key] = []
        return []

    union_sql = " UNION ".join(candidate_ids_sql_parts)
    tag_params = {f"tags_{dim}": list(source_tags[dim]) for dim in _DIM_SQL if source_tags.get(dim)}
    r = await db.execute(text(f"SELECT DISTINCT film_id FROM ({union_sql}) sub"), tag_params)
    candidate_ids = [row[0] for row in r.fetchall() if row[0] not in excluded]

    if not candidate_ids:
        _sim_cache[cache_key] = []
        return []

    # 5. Load tags for all candidates in bulk (one query per dimension)
    candidate_tags: dict[int, dict[str, set[str]]] = {cid: {} for cid in candidate_ids}
    for dim, (junc, junc_fk, lookup, name_col) in _DIM_SQL.items():
        r = await db.execute(text(
            f"SELECT jt.film_id, lt.{name_col} "
            f"FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE jt.film_id = ANY(:cids)"
        ), {"cids": candidate_ids})
        for fid, tag_name in r.fetchall():
            if fid in candidate_tags:
                candidate_tags[fid].setdefault(dim, set()).add(tag_name)

    # 6. Load bonus data in bulk
    # Directors
    r = await db.execute(text(
        "SELECT cr.film_id, p.person_id FROM crew cr "
        "JOIN person_job pj ON cr.job_id = pj.job_id "
        "JOIN person p ON cr.person_id = p.person_id "
        "WHERE cr.film_id = ANY(:cids) AND pj.role_name = 'Director'"
    ), {"cids": candidate_ids})
    cand_directors: dict[int, set[int]] = {}
    for fid, pid in r.fetchall():
        cand_directors.setdefault(fid, set()).add(pid)

    # Studios + decade + weighted_score
    r = await db.execute(text(
        "SELECT pr.film_id, s.studio_id FROM production pr "
        "JOIN studio s ON pr.studio_id = s.studio_id "
        "WHERE pr.film_id = ANY(:cids)"
    ), {"cids": candidate_ids})
    cand_studios: dict[int, set[int]] = {}
    for fid, sid in r.fetchall():
        cand_studios.setdefault(fid, set()).add(sid)

    r = await db.execute(text(
        "SELECT film_id, EXTRACT(YEAR FROM first_release_date)::int / 10 AS decade, "
        "weighted_score, tmdb_collection_id FROM film WHERE film_id = ANY(:cids)"
    ), {"cids": candidate_ids})
    cand_meta: dict[int, tuple] = {}
    for fid, decade, ws, coll_id in r.fetchall():
        cand_meta[fid] = (decade, float(ws) if ws is not None else None, coll_id)

    # Compute max weighted_score for normalization
    all_ws = [source_ws] if source_ws else []
    all_ws.extend(m[1] for m in cand_meta.values() if m[1] is not None)
    max_ws = max(all_ws) if all_ws else 1.0

    # 7. Score each candidate
    scores: list[tuple[int, float, dict[str, list[str]]]] = []
    for cid in candidate_ids:
        c_tags = candidate_tags.get(cid, {})
        total_score = 0.0
        shared: dict[str, list[str]] = {}

        for dim, weight in DIMENSION_WEIGHTS.items():
            s_tags = source_tags.get(dim, set())
            ct = c_tags.get(dim, set())
            if not s_tags and not ct:
                continue
            dim_idf = idf_map.get(dim, {})
            dim_score = _idf_jaccard(s_tags, ct, dim_idf)
            total_score += weight * dim_score
            overlap = s_tags & ct
            if overlap:
                shared[dim] = sorted(overlap)[:3]

        # Bonuses
        if source_director_ids & cand_directors.get(cid, set()):
            total_score += BONUS_DIRECTOR

        meta = cand_meta.get(cid)
        if meta and source_decade is not None and meta[0] == source_decade:
            if source_studio_ids & cand_studios.get(cid, set()):
                total_score += BONUS_STUDIO_DECADE

        if meta and meta[1] is not None and max_ws > 0:
            total_score += BONUS_QUALITY_MAX * (meta[1] / max_ws)

        scores.append((cid, total_score, shared))

    # 8. Sort, deduplicate franchises (max 1 per collection), take top N
    scores.sort(key=lambda x: x[1], reverse=True)
    seen_collections: set[int] = set()
    deduped: list[tuple[int, float, dict[str, list[str]]]] = []
    for entry in scores:
        coll_id = (cand_meta.get(entry[0]) or (None, None, None))[2]
        if coll_id is not None:
            if coll_id in seen_collections:
                continue
            seen_collections.add(coll_id)
        deduped.append(entry)
    top = deduped[:limit]

    if not top:
        _sim_cache[cache_key] = []
        return []

    max_score = top[0][1] if top[0][1] > 0 else 1.0

    # 9. Fetch display data for top results
    top_ids = [t[0] for t in top]
    r = await db.execute(text(
        "SELECT film_id, original_title, first_release_date, duration, poster_url "
        "FROM film WHERE film_id = ANY(:ids)"
    ), {"ids": top_ids})
    film_info = {row[0]: row for row in r.fetchall()}

    # Directors for display
    r = await db.execute(text(
        "SELECT cr.film_id, COALESCE(p.firstname, '') || ' ' || p.lastname "
        "FROM crew cr JOIN person p ON cr.person_id = p.person_id "
        "JOIN person_job pj ON cr.job_id = pj.job_id "
        "WHERE cr.film_id = ANY(:ids) AND pj.role_name = 'Director'"
    ), {"ids": top_ids})
    dir_map: dict[int, str] = {}
    for fid, dname in r.fetchall():
        dir_map[fid] = f"{dir_map[fid]}, {dname}" if fid in dir_map else dname

    # Categories for display
    r = await db.execute(text(
        "SELECT fg.film_id, c.category_name FROM film_genre fg "
        "JOIN category c ON fg.category_id = c.category_id "
        "WHERE fg.film_id = ANY(:ids) AND c.historic_subcategory_name IS NULL"
    ), {"ids": top_ids})
    cat_map: dict[int, list[str]] = {}
    for fid, cname in r.fetchall():
        cat_map.setdefault(fid, []).append(cname)

    results = []
    for cid, score, shared in top:
        info = film_info.get(cid)
        if not info:
            continue
        results.append({
            "film_id": cid,
            "original_title": info[1],
            "first_release_date": info[2],
            "duration": info[3],
            "poster_url": info[4],
            "director": dir_map.get(cid),
            "categories": cat_map.get(cid, []),
            "score": round(score, 4),
            "score_pct": round((score / max_score) * 100) if max_score > 0 else 0,
            "shared_tags": shared,
        })

    _sim_cache[cache_key] = results
    return results
