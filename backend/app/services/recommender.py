"""
Similar-films recommender using IDF-weighted Jaccard similarity
across 9 taxonomy dimensions plus structural bonuses.
"""

import asyncio
import logging
import math
import time

from cachetools import TTLCache
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import engine

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
# (junction_table, foreign_key, lookup_table, name_column)
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

_DIM_KEYS = list(_DIM_SQL.keys())

_semaphore = asyncio.Semaphore(8)


async def _q(sql: str, params: dict | None = None) -> list:
    async with _semaphore:
        async with engine.connect() as conn:
            r = await conn.execute(text(sql), params or {})
            return r.fetchall()


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

    # Parallel IDF computation across all 9 dimensions
    async def _idf_for_dim(dim: str) -> tuple[str, dict[str, float]]:
        junc, junc_fk, lookup, name_col = _DIM_SQL[dim]
        rows = await _q(
            f"SELECT lt.{name_col}, COUNT(DISTINCT jt.film_id) "
            f"FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"GROUP BY lt.{name_col}"
        )
        return dim, {
            tag: math.log(_total_films / cnt) if cnt > 0 else 0.0
            for tag, cnt in rows
        }

    results = await asyncio.gather(*[_idf_for_dim(d) for d in _DIM_KEYS])
    _idf_map = dict(results)
    _idf_ts = now
    logger.info("IDF map rebuilt: %d dimensions, %d total films",
                len(_idf_map), _total_films)
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

    # ── Phase 1: load source film data in parallel ─────────────────────
    # 9 tag queries + exclusions + directors + studios + film meta = 13 parallel queries

    async def _source_tags(dim: str) -> tuple[str, set[str]]:
        junc, junc_fk, lookup, name_col = _DIM_SQL[dim]
        rows = await _q(
            f"SELECT lt.{name_col} FROM {junc} jt "
            f"JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE jt.film_id = :fid",
            {"fid": film_id},
        )
        return dim, {row[0] for row in rows}

    phase1 = await asyncio.gather(
        *[_source_tags(d) for d in _DIM_KEYS],
        _q(
            "SELECT related_film_id FROM film_sequel WHERE film_id = :fid "
            "UNION "
            "SELECT film_id FROM film_sequel WHERE related_film_id = :fid",
            {"fid": film_id},
        ),
        _q(
            "SELECT p.person_id FROM crew cr "
            "JOIN person_job pj ON cr.job_id = pj.job_id "
            "JOIN person p ON cr.person_id = p.person_id "
            "WHERE cr.film_id = :fid AND pj.role_name = 'Director'",
            {"fid": film_id},
        ),
        _q(
            "SELECT s.studio_id FROM production pr "
            "JOIN studio s ON pr.studio_id = s.studio_id "
            "WHERE pr.film_id = :fid",
            {"fid": film_id},
        ),
        _q(
            "SELECT EXTRACT(YEAR FROM first_release_date)::int / 10 AS decade, "
            "weighted_score FROM film WHERE film_id = :fid",
            {"fid": film_id},
        ),
    )

    # Unpack phase 1
    source_tags: dict[str, set[str]] = dict(phase1[:9])  # type: ignore[arg-type]
    excluded_rows = phase1[9]
    excluded = {film_id} | {row[0] for row in excluded_rows}
    source_director_ids = {row[0] for row in phase1[10]}
    source_studio_ids = {row[0] for row in phase1[11]}
    src_row = phase1[12][0] if phase1[12] else None
    source_decade = src_row[0] if src_row and src_row[0] is not None else None
    source_ws = float(src_row[1]) if src_row and src_row[1] is not None else None

    # ── Phase 2: find candidates (single query) ───────────────────────

    candidate_ids_sql_parts = []
    tag_params: dict = {}
    for dim, (junc, junc_fk, lookup, name_col) in _DIM_SQL.items():
        tags = source_tags.get(dim, set())
        if not tags:
            continue
        candidate_ids_sql_parts.append(
            f"SELECT DISTINCT jt.film_id FROM {junc} jt "
            f"JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE lt.{name_col} = ANY(:tags_{dim})"
        )
        tag_params[f"tags_{dim}"] = list(tags)

    if not candidate_ids_sql_parts:
        _sim_cache[cache_key] = []
        return []

    union_sql = " UNION ".join(candidate_ids_sql_parts)
    rows = await _q(f"SELECT DISTINCT film_id FROM ({union_sql}) sub", tag_params)
    candidate_ids = [row[0] for row in rows if row[0] not in excluded]

    if not candidate_ids:
        _sim_cache[cache_key] = []
        return []

    # ── Phase 3: load candidate data in parallel ──────────────────────
    # 9 tag queries + directors + studios + film meta = 12 parallel queries

    async def _cand_tags(dim: str) -> tuple[str, list]:
        junc, junc_fk, lookup, name_col = _DIM_SQL[dim]
        rows = await _q(
            f"SELECT jt.film_id, lt.{name_col} "
            f"FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{junc_fk} "
            f"WHERE jt.film_id = ANY(:cids)",
            {"cids": candidate_ids},
        )
        return dim, rows

    phase3 = await asyncio.gather(
        *[_cand_tags(d) for d in _DIM_KEYS],
        _q(
            "SELECT cr.film_id, p.person_id FROM crew cr "
            "JOIN person_job pj ON cr.job_id = pj.job_id "
            "JOIN person p ON cr.person_id = p.person_id "
            "WHERE cr.film_id = ANY(:cids) AND pj.role_name = 'Director'",
            {"cids": candidate_ids},
        ),
        _q(
            "SELECT pr.film_id, s.studio_id FROM production pr "
            "JOIN studio s ON pr.studio_id = s.studio_id "
            "WHERE pr.film_id = ANY(:cids)",
            {"cids": candidate_ids},
        ),
        _q(
            "SELECT film_id, EXTRACT(YEAR FROM first_release_date)::int / 10 AS decade, "
            "weighted_score, tmdb_collection_id FROM film WHERE film_id = ANY(:cids)",
            {"cids": candidate_ids},
        ),
    )

    # Unpack candidate tags
    candidate_tags: dict[int, dict[str, set[str]]] = {cid: {} for cid in candidate_ids}
    for dim, rows in phase3[:9]:  # type: ignore[misc]
        for fid, tag_name in rows:
            if fid in candidate_tags:
                candidate_tags[fid].setdefault(dim, set()).add(tag_name)

    # Unpack candidate directors
    cand_directors: dict[int, set[int]] = {}
    for fid, pid in phase3[9]:
        cand_directors.setdefault(fid, set()).add(pid)

    # Unpack candidate studios
    cand_studios: dict[int, set[int]] = {}
    for fid, sid in phase3[10]:
        cand_studios.setdefault(fid, set()).add(sid)

    # Unpack candidate meta (decade, weighted_score, collection_id)
    cand_meta: dict[int, tuple] = {}
    for fid, decade, ws, coll_id in phase3[11]:
        cand_meta[fid] = (decade, float(ws) if ws is not None else None, coll_id)

    # Compute max weighted_score for normalization
    all_ws = [source_ws] if source_ws else []
    all_ws.extend(m[1] for m in cand_meta.values() if m[1] is not None)
    max_ws = max(all_ws) if all_ws else 1.0

    # ── Phase 4: score (pure Python, no I/O) ──────────────────────────

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

    # Sort, deduplicate franchises (max 1 per collection), take top N
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

    # ── Phase 5: fetch display data in parallel ───────────────────────

    top_ids = [t[0] for t in top]
    film_rows, dir_rows, cat_rows = await asyncio.gather(
        _q(
            "SELECT film_id, original_title, first_release_date, duration, poster_url "
            "FROM film WHERE film_id = ANY(:ids)",
            {"ids": top_ids},
        ),
        _q(
            "SELECT cr.film_id, COALESCE(p.firstname, '') || ' ' || p.lastname "
            "FROM crew cr JOIN person p ON cr.person_id = p.person_id "
            "JOIN person_job pj ON cr.job_id = pj.job_id "
            "WHERE cr.film_id = ANY(:ids) AND pj.role_name = 'Director'",
            {"ids": top_ids},
        ),
        _q(
            "SELECT fg.film_id, c.category_name FROM film_genre fg "
            "JOIN category c ON fg.category_id = c.category_id "
            "WHERE fg.film_id = ANY(:ids) AND c.historic_subcategory_name IS NULL",
            {"ids": top_ids},
        ),
    )

    film_info = {row[0]: row for row in film_rows}
    dir_map: dict[int, str] = {}
    for fid, dname in dir_rows:
        dir_map[fid] = f"{dir_map[fid]}, {dname}" if fid in dir_map else dname
    cat_map: dict[int, list[str]] = {}
    for fid, cname in cat_rows:
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
