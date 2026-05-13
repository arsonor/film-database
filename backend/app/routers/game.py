"""
Game mode "Tag It" — step 18.

Endpoints under /game:
  GET  /game/daily              — today's daily challenge (3 films)
  GET  /game/random             — 3 random films from a filtered pool (free play)
  POST /game/check              — apply tags, return remaining_count + target_included
  POST /game/joker/remaining    — list of films still matching current tags
  POST /game/joker/hint         — best next tag (reduces count most while keeping target)
  POST /game/joker/synopsis     — target film synopsis
  POST /game/result             — save game result (requires auth)
  GET  /game/stats              — user game statistics (requires auth)
"""

import json
import logging
import random

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import UserInfo, get_current_user, require_authenticated
from backend.app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["game"])


# (junction_table, junction_fk_col, tag_table, tag_pk_col, tag_name_col)
DIMENSION_TABLE_MAP: dict[str, tuple[str, str, str, str, str]] = {
    "categories":     ("film_genre",             "category_id",          "category",            "category_id",          "category_name"),
    "themes":         ("film_theme",             "theme_context_id",     "theme_context",       "theme_context_id",     "theme_name"),
    "atmospheres":    ("film_atmosphere",        "atmosphere_id",        "atmosphere",          "atmosphere_id",        "atmosphere_name"),
    "characters":     ("film_character_context", "character_context_id", "character_context",   "character_context_id", "context_name"),
    "motivations":    ("film_motivation",        "motivation_id",        "motivation_relation", "motivation_id",        "motivation_name"),
    "messages":       ("film_message",           "message_id",           "message_conveyed",    "message_id",           "message_name"),
    "cinema_types":   ("film_technique",         "cinema_type_id",       "cinema_type",         "cinema_type_id",       "technique_name"),
    "time_periods":   ("film_period",            "time_context_id",      "time_context",        "time_context_id",      "time_period"),
    "place_contexts": ("film_place",             "place_context_id",     "place_context",       "place_context_id",     "environment"),
}


def _year_from_date(d) -> int | None:
    if d is None:
        return None
    try:
        return d.year
    except AttributeError:
        try:
            return int(str(d)[:4])
        except Exception:
            return None


def _film_row_to_dict(row) -> dict:
    return {
        "film_id": row[0],
        "title": row[1],
        "year": _year_from_date(row[2]),
        "poster_url": row[3],
    }


def _build_tag_clauses(tags: list[dict], params: dict, start_idx: int = 0) -> list[str]:
    """Return list of 'film_id IN (...)' clauses for each selected tag."""
    clauses: list[str] = []
    for i, t in enumerate(tags):
        dim = t.get("dimension")
        val = t.get("value")
        if not dim or not val or dim not in DIMENSION_TABLE_MAP:
            continue
        jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
        pname = f"tagv_{start_idx + i}"
        params[pname] = val
        clauses.append(
            f"film_id IN (SELECT j.film_id FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} WHERE t.{tn} = :{pname})"
        )
    return clauses


def _apply_pool_filters(pool_filters: dict | None, params: dict, alias: str = "") -> list[str]:
    """Build pool filter WHERE clauses. `alias` is e.g. 'f.' to disambiguate film_id."""
    clauses: list[str] = []
    if not pool_filters:
        return clauses
    a = f"{alias}." if alias and not alias.endswith(".") else alias
    ymin = pool_filters.get("year_min")
    ymax = pool_filters.get("year_max")
    lang = pool_filters.get("language")
    if ymin is not None:
        clauses.append(f"EXTRACT(YEAR FROM {a}first_release_date) >= :pool_ymin")
        params["pool_ymin"] = ymin
    if ymax is not None:
        clauses.append(f"EXTRACT(YEAR FROM {a}first_release_date) <= :pool_ymax")
        params["pool_ymax"] = ymax
    if lang:
        clauses.append(
            f"{a}film_id IN (SELECT fl.film_id FROM film_language fl JOIN language l "
            "ON fl.language_id = l.language_id WHERE fl.is_original = TRUE "
            "AND (l.language_code = :pool_lang OR l.language_name ILIKE :pool_lang_like))"
        )
        params["pool_lang"] = lang
        params["pool_lang_like"] = f"%{lang}%"
    return clauses


# =============================================================================
# Helper: pick an eligible random film
# =============================================================================


async def _pick_eligible_film(db: AsyncSession, exclude_ids: list[int] | None = None) -> int | None:
    """Pick a random film with poster, summary and tags in >= 5 dimensions."""
    dim_unions = " UNION ALL ".join([
        f"SELECT DISTINCT film_id FROM {jt}" for (jt, _, _, _, _) in DIMENSION_TABLE_MAP.values()
    ])
    excl_clause = ""
    params: dict = {}
    if exclude_ids:
        excl_clause = "AND f.film_id <> ALL(:excl)"
        params["excl"] = exclude_ids

    sql = f"""
        WITH dim_films AS (
            SELECT film_id, COUNT(*) AS n_dims FROM (
                {dim_unions}
            ) u GROUP BY film_id
        )
        SELECT f.film_id
        FROM film f
        JOIN dim_films d ON d.film_id = f.film_id
        WHERE f.poster_url IS NOT NULL
          AND f.summary IS NOT NULL
          AND d.n_dims >= 5
          {excl_clause}
        ORDER BY RANDOM()
        LIMIT 1
    """
    r = await db.execute(text(sql), params)
    row = r.fetchone()
    return row[0] if row else None


async def _fetch_films(db: AsyncSession, film_ids: list[int]) -> list[dict]:
    if not film_ids:
        return []
    r = await db.execute(
        text("SELECT film_id, original_title, first_release_date, poster_url FROM film WHERE film_id = ANY(:ids)"),
        {"ids": film_ids},
    )
    by_id = {row[0]: _film_row_to_dict(row) for row in r.fetchall()}
    return [by_id[i] for i in film_ids if i in by_id]


# =============================================================================
# GET /game/daily
# =============================================================================


@router.get("/game/daily")
async def get_daily_challenge(
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    # Fetch existing row for today
    r = await db.execute(
        text("SELECT challenge_date, film_id, decoy1_film_id, decoy2_film_id FROM daily_challenge WHERE challenge_date = CURRENT_DATE")
    )
    row = r.fetchone()

    if row is None:
        target_id = await _pick_eligible_film(db)
        if target_id is None:
            raise HTTPException(status_code=500, detail="No eligible film found")
        decoy1 = await _pick_eligible_film(db, exclude_ids=[target_id])
        decoy2 = await _pick_eligible_film(db, exclude_ids=[target_id, decoy1] if decoy1 else [target_id])
        await db.execute(
            text("""INSERT INTO daily_challenge (challenge_date, film_id, decoy1_film_id, decoy2_film_id)
                    VALUES (CURRENT_DATE, :f, :d1, :d2)
                    ON CONFLICT (challenge_date) DO NOTHING"""),
            {"f": target_id, "d1": decoy1, "d2": decoy2},
        )
        await db.commit()
    else:
        target_id, decoy1, decoy2 = row[1], row[2], row[3]

    ids = [i for i in [target_id, decoy1, decoy2] if i is not None]
    # Shuffle so the target is not always first
    rnd = random.Random(str(target_id) + "-display")
    ids_shuffled = ids.copy()
    rnd.shuffle(ids_shuffled)

    films = await _fetch_films(db, ids_shuffled)

    # Pool size = full film count
    c = await db.execute(text("SELECT COUNT(*) FROM film"))
    pool_size = c.scalar_one()

    already_played = None
    if user:
        ar = await db.execute(
            text("""SELECT film_id, tags_used, lives_remaining, jokers_used, stars,
                          tag_sequence, completed, played_at
                    FROM game_result
                    WHERE user_id = :uid AND mode = 'daily' AND challenge_date = CURRENT_DATE
                    LIMIT 1"""),
            {"uid": user.id},
        )
        ar_row = ar.fetchone()
        if ar_row:
            already_played = {
                "film_id": ar_row[0],
                "tags_used": ar_row[1],
                "lives_remaining": ar_row[2],
                "jokers_used": ar_row[3],
                "stars": ar_row[4],
                "tag_sequence": ar_row[5],
                "completed": ar_row[6],
                "played_at": ar_row[7].isoformat() if ar_row[7] else None,
            }

    return {
        "films": films, "pool_size": pool_size, "mode": "daily",
        "already_played": already_played,
    }


# =============================================================================
# GET /game/random
# =============================================================================


@router.get("/game/random")
async def get_random_films(
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {}
    where = ["f.poster_url IS NOT NULL", "f.summary IS NOT NULL"]
    pool_filters = {}
    if year_min is not None:
        pool_filters["year_min"] = year_min
    if year_max is not None:
        pool_filters["year_max"] = year_max
    if language:
        pool_filters["language"] = language
    where.extend(_apply_pool_filters(pool_filters, params, alias="f"))

    # require >= 5 dims
    dim_unions = " UNION ALL ".join([
        f"SELECT DISTINCT film_id FROM {jt}" for (jt, _, _, _, _) in DIMENSION_TABLE_MAP.values()
    ])
    where_sql = " AND ".join(where)

    sql = f"""
        WITH dim_films AS (
            SELECT film_id, COUNT(*) AS n_dims FROM (
                {dim_unions}
            ) u GROUP BY film_id
        ),
        pool AS (
            SELECT f.film_id FROM film f
            JOIN dim_films d ON d.film_id = f.film_id
            WHERE d.n_dims >= 5 AND {where_sql}
        )
        SELECT (SELECT COUNT(*) FROM pool) AS pool_size
    """
    r = await db.execute(text(sql), params)
    pool_size = r.scalar_one() or 0

    if pool_size < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough films in this pool ({pool_size}) — broaden your filters (minimum 50)",
        )

    pick_sql = f"""
        WITH dim_films AS (
            SELECT film_id, COUNT(*) AS n_dims FROM (
                {dim_unions}
            ) u GROUP BY film_id
        )
        SELECT f.film_id, f.original_title, f.first_release_date, f.poster_url
        FROM film f
        JOIN dim_films d ON d.film_id = f.film_id
        WHERE d.n_dims >= 5 AND {where_sql}
        ORDER BY RANDOM() LIMIT 3
    """
    r = await db.execute(text(pick_sql), params)
    films = [_film_row_to_dict(row) for row in r.fetchall()]

    return {"films": films, "pool_size": pool_size, "mode": "free"}


# =============================================================================
# POST /game/check
# =============================================================================


@router.post("/game/check")
async def check_tags(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    film_id = body.get("film_id")
    tags = body.get("tags") or []
    pool_filters = body.get("pool_filters")

    if not film_id:
        raise HTTPException(status_code=400, detail="film_id is required")

    params: dict = {}
    where_clauses = _build_tag_clauses(tags, params)
    where_clauses.extend(_apply_pool_filters(pool_filters, params))

    if not where_clauses:
        # No tags yet — return pool size and target included = True
        r = await db.execute(text("SELECT COUNT(*) FROM film"))
        return {"remaining_count": r.scalar_one(), "target_included": True, "victory": False}

    where_sql = " AND ".join(where_clauses)
    r = await db.execute(text(f"SELECT COUNT(*) FROM film WHERE {where_sql}"), params)
    remaining = r.scalar_one()

    params["target_fid"] = film_id
    r2 = await db.execute(
        text(f"SELECT 1 FROM film WHERE film_id = :target_fid AND {where_sql}"),
        params,
    )
    target_included = r2.fetchone() is not None
    victory = (remaining == 1 and target_included)

    return {"remaining_count": remaining, "target_included": target_included, "victory": victory}


# =============================================================================
# POST /game/joker/remaining
# =============================================================================


@router.post("/game/joker/remaining")
async def joker_remaining(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    tags = body.get("tags") or []
    pool_filters = body.get("pool_filters")

    params: dict = {}
    where_clauses = _build_tag_clauses(tags, params)
    where_clauses.extend(_apply_pool_filters(pool_filters, params))

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
    sql = f"""
        SELECT film_id, original_title, first_release_date, poster_url
        FROM film
        WHERE {where_sql}
        ORDER BY weighted_score DESC NULLS LAST
        LIMIT 20
    """
    r = await db.execute(text(sql), params)
    return {"films": [_film_row_to_dict(row) for row in r.fetchall()]}


# =============================================================================
# POST /game/joker/hint
# =============================================================================


@router.post("/game/joker/hint")
async def joker_hint(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    film_id = body.get("film_id")
    tags = body.get("tags") or []
    pool_filters = body.get("pool_filters")

    if not film_id:
        raise HTTPException(status_code=400, detail="film_id is required")

    selected_set = {(t["dimension"], t["value"]) for t in tags if t.get("dimension") and t.get("value")}

    # Gather all target film tags across dimensions
    candidates: list[tuple[str, str]] = []
    for dim, (jt, jfk, tt, tpk, tn) in DIMENSION_TABLE_MAP.items():
        r = await db.execute(
            text(f"SELECT t.{tn} FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} WHERE j.film_id = :fid"),
            {"fid": film_id},
        )
        for row in r.fetchall():
            tag = row[0]
            if (dim, tag) not in selected_set:
                candidates.append((dim, tag))

    if not candidates:
        return {"dimension": None, "tag": None, "would_reduce_to": None}

    # Compute count for each candidate
    base_params: dict = {}
    base_clauses = _build_tag_clauses(tags, base_params)
    base_clauses.extend(_apply_pool_filters(pool_filters, base_params))

    best: tuple[str, str, int] | None = None
    for dim, tag in candidates[:30]:  # cap
        jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
        params = dict(base_params)
        pname = "cand_val"
        params[pname] = tag
        extra = (
            f"film_id IN (SELECT j.film_id FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} WHERE t.{tn} = :{pname})"
        )
        clauses = base_clauses + [extra]
        where_sql = " AND ".join(clauses)
        r = await db.execute(text(f"SELECT COUNT(*) FROM film WHERE {where_sql}"), params)
        count = r.scalar_one()
        if count >= 1 and (best is None or count < best[2]):
            best = (dim, tag, count)

    if best is None:
        return {"dimension": None, "tag": None, "would_reduce_to": None}

    return {"dimension": best[0], "tag": best[1], "would_reduce_to": best[2]}


# =============================================================================
# POST /game/joker/synopsis
# =============================================================================


@router.post("/game/joker/synopsis")
async def joker_synopsis(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    film_id = body.get("film_id")
    if not film_id:
        raise HTTPException(status_code=400, detail="film_id is required")
    r = await db.execute(text("SELECT summary FROM film WHERE film_id = :fid"), {"fid": film_id})
    row = r.fetchone()
    return {"synopsis": row[0] if row else None}


# =============================================================================
# POST /game/result
# =============================================================================


@router.post("/game/result")
async def save_result(
    body: dict = Body(...),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    mode = body.get("mode")
    if mode not in ("daily", "free"):
        raise HTTPException(status_code=400, detail="mode must be 'daily' or 'free'")
    film_id = body.get("film_id")
    if not film_id:
        raise HTTPException(status_code=400, detail="film_id required")

    challenge_date = body.get("challenge_date")  # 'YYYY-MM-DD' or None
    tags_used = int(body.get("tags_used") or 0)
    lives_remaining = int(body.get("lives_remaining") or 0)
    jokers_used = int(body.get("jokers_used") or 0)
    stars = int(body.get("stars") or 0)
    tag_sequence = body.get("tag_sequence")
    completed = bool(body.get("completed", True))

    # For daily mode the server is the authority on what date "today" is — ignore
    # the client-provided challenge_date to avoid TZ mismatches between client/server.
    if mode == "daily":
        r = await db.execute(
            text("""SELECT id FROM game_result
                    WHERE user_id = :uid AND mode = 'daily' AND challenge_date = CURRENT_DATE"""),
            {"uid": user.id},
        )
        existing = r.fetchone()
        if existing:
            logger.info("save_result: daily already saved for user=%s row=%s", user.id, existing[0])
            return {"saved": False, "id": existing[0], "already_saved": True}

    try:
        if mode == "daily":
            insert_sql = """
                INSERT INTO game_result (user_id, film_id, mode, challenge_date, tags_used,
                                         lives_remaining, jokers_used, stars, tag_sequence, completed)
                VALUES (:uid, :fid, 'daily', CURRENT_DATE, :tu, :lr, :ju, :st, CAST(:seq AS JSONB), :comp)
                RETURNING id
            """
            params = {
                "uid": user.id, "fid": film_id,
                "tu": tags_used, "lr": lives_remaining, "ju": jokers_used, "st": stars,
                "seq": json.dumps(tag_sequence) if tag_sequence is not None else None,
                "comp": completed,
            }
        else:
            insert_sql = """
                INSERT INTO game_result (user_id, film_id, mode, challenge_date, tags_used,
                                         lives_remaining, jokers_used, stars, tag_sequence, completed)
                VALUES (:uid, :fid, 'free', NULL, :tu, :lr, :ju, :st, CAST(:seq AS JSONB), :comp)
                RETURNING id
            """
            params = {
                "uid": user.id, "fid": film_id,
                "tu": tags_used, "lr": lives_remaining, "ju": jokers_used, "st": stars,
                "seq": json.dumps(tag_sequence) if tag_sequence is not None else None,
                "comp": completed,
            }
        r = await db.execute(text(insert_sql), params)
        rid = r.scalar_one()
        await db.commit()
        logger.info("save_result: inserted mode=%s user=%s id=%s", mode, user.id, rid)
        return {"saved": True, "id": rid}
    except IntegrityError as e:
        await db.rollback()
        logger.warning("save_result: IntegrityError mode=%s user=%s: %s", mode, user.id, e)
        r = await db.execute(
            text("""SELECT id FROM game_result
                    WHERE user_id = :uid AND mode = 'daily' AND challenge_date = CURRENT_DATE"""),
            {"uid": user.id},
        )
        existing = r.fetchone()
        return {"saved": False, "id": existing[0] if existing else None, "already_saved": True}


# =============================================================================
# GET /game/stats
# =============================================================================


@router.get("/game/stats")
async def game_stats(
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    # Per-mode aggregates
    r = await db.execute(
        text("""
            SELECT
                mode,
                COUNT(*) AS games,
                SUM(CASE WHEN completed AND stars > 0 THEN 1 ELSE 0 END) AS wins,
                AVG(stars)::float AS avg_stars,
                MAX(stars) AS best_stars,
                MIN(CASE WHEN completed AND stars > 0 THEN tags_used END) AS best_tags
            FROM game_result
            WHERE user_id = :uid
            GROUP BY mode
        """),
        {"uid": user.id},
    )

    def empty_block():
        return {"games": 0, "wins": 0, "avg_stars": 0.0, "best_stars": 0, "best_tags": None}

    daily_block = empty_block()
    free_block = empty_block()
    for row in r.fetchall():
        block = {
            "games": row[1] or 0,
            "wins": row[2] or 0,
            "avg_stars": round(row[3], 2) if row[3] is not None else 0.0,
            "best_stars": row[4] or 0,
            "best_tags": row[5],
        }
        if row[0] == "daily":
            daily_block = block
        elif row[0] == "free":
            free_block = block

    # Daily streak: consecutive distinct challenge_dates ending today or yesterday
    streak_r = await db.execute(
        text("""
            SELECT DISTINCT challenge_date FROM game_result
            WHERE user_id = :uid AND mode = 'daily' AND challenge_date IS NOT NULL
            ORDER BY challenge_date DESC
            LIMIT 365
        """),
        {"uid": user.id},
    )
    dates = [r2[0] for r2 in streak_r.fetchall()]

    current_streak = 0
    max_streak = 0
    if dates:
        from datetime import date, timedelta
        today = date.today()
        # Current streak from today/yesterday
        expected = today
        for d in dates:
            if d == expected:
                current_streak += 1
                expected = expected - timedelta(days=1)
            elif d == today - timedelta(days=1) and current_streak == 0:
                # allow streak if last played yesterday but not today
                current_streak = 1
                expected = d - timedelta(days=1)
            else:
                break
        # Max streak
        prev = None
        run = 0
        for d in dates:
            if prev is None or prev - d == timedelta(days=1):
                run += 1
            else:
                run = 1
            max_streak = max(max_streak, run)
            prev = d

    daily_block["current_streak"] = current_streak
    daily_block["max_streak"] = max_streak

    return {"daily": daily_block, "free": free_block}
