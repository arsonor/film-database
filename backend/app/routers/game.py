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
        if not dim or not val:
            continue
        pname = f"tagv_{start_idx + i}"
        params[pname] = val
        if dim == "geography":
            clauses.append(
                f"film_id IN (SELECT fsp.film_id FROM film_set_place fsp "
                f"JOIN geography g ON fsp.geography_id = g.geography_id "
                f"WHERE g.country = :{pname} OR g.state_city = :{pname})"
            )
            continue
        if dim not in DIMENSION_TABLE_MAP:
            continue
        jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
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
        text("SELECT challenge_date, film_id, decoy1_film_id, decoy2_film_id FROM daily_challenge "
             "WHERE challenge_date = CURRENT_DATE AND game_type = 'tag_it'")
    )
    row = r.fetchone()

    if row is None:
        target_id = await _pick_eligible_film(db)
        if target_id is None:
            raise HTTPException(status_code=500, detail="No eligible film found")
        decoy1 = await _pick_eligible_film(db, exclude_ids=[target_id])
        decoy2 = await _pick_eligible_film(db, exclude_ids=[target_id, decoy1] if decoy1 else [target_id])
        await db.execute(
            text("""INSERT INTO daily_challenge (challenge_date, game_type, film_id, decoy1_film_id, decoy2_film_id)
                    VALUES (CURRENT_DATE, 'tag_it', :f, :d1, :d2)
                    ON CONFLICT (challenge_date, game_type) DO NOTHING"""),
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
                    WHERE user_id = :uid AND mode = 'daily'
                      AND challenge_date = CURRENT_DATE AND game_type = 'tag_it'
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

    game_type = body.get("game_type") or "tag_it"
    if game_type not in ("tag_it", "chain_it", "guess_it"):
        raise HTTPException(status_code=400, detail="invalid game_type")

    tags_used = int(body.get("tags_used") or 0)
    lives_remaining = int(body.get("lives_remaining") or 0)
    jokers_used = int(body.get("jokers_used") or 0)
    stars = int(body.get("stars") or 0)
    tag_sequence = body.get("tag_sequence")
    completed = bool(body.get("completed", True))
    chain_length = body.get("chain_length")
    origin_film_id = body.get("origin_film_id")
    target_film_id = body.get("target_film_id")
    difficulty = body.get("difficulty")
    pool_filters = body.get("pool_filters")

    if mode == "daily":
        r = await db.execute(
            text("""SELECT id FROM game_result
                    WHERE user_id = :uid AND mode = 'daily'
                      AND challenge_date = CURRENT_DATE AND game_type = :gt"""),
            {"uid": user.id, "gt": game_type},
        )
        existing = r.fetchone()
        if existing:
            logger.info("save_result: daily already saved for user=%s row=%s", user.id, existing[0])
            return {"saved": False, "id": existing[0], "already_saved": True}

    try:
        date_expr = "CURRENT_DATE" if mode == "daily" else "NULL"
        insert_sql = f"""
            INSERT INTO game_result (user_id, game_type, film_id, origin_film_id, target_film_id,
                                     chain_length, mode, challenge_date, tags_used,
                                     lives_remaining, jokers_used, stars, tag_sequence, completed,
                                     difficulty, pool_filters)
            VALUES (:uid, :gt, :fid, :ofid, :tfid, :cl, :mode, {date_expr},
                    :tu, :lr, :ju, :st, CAST(:seq AS JSONB), :comp,
                    :diff, CAST(:pf AS JSONB))
            RETURNING id
        """
        params = {
            "uid": user.id, "gt": game_type, "fid": film_id,
            "ofid": origin_film_id, "tfid": target_film_id, "cl": chain_length,
            "mode": mode,
            "tu": tags_used, "lr": lives_remaining, "ju": jokers_used, "st": stars,
            "seq": json.dumps(tag_sequence) if tag_sequence is not None else None,
            "comp": completed,
            "diff": difficulty,
            "pf": json.dumps(pool_filters) if pool_filters else None,
        }
        r = await db.execute(text(insert_sql), params)
        rid = r.scalar_one()
        await db.commit()
        logger.info("save_result: inserted gt=%s mode=%s user=%s id=%s", game_type, mode, user.id, rid)
        return {"saved": True, "id": rid}
    except IntegrityError as e:
        await db.rollback()
        logger.warning("save_result: IntegrityError gt=%s mode=%s user=%s: %s", game_type, mode, user.id, e)
        r = await db.execute(
            text("""SELECT id FROM game_result
                    WHERE user_id = :uid AND mode = 'daily'
                      AND challenge_date = CURRENT_DATE AND game_type = :gt"""),
            {"uid": user.id, "gt": game_type},
        )
        existing = r.fetchone()
        return {"saved": False, "id": existing[0] if existing else None, "already_saved": True}


# =============================================================================
# GET /game/stats
# =============================================================================


def _empty_mode_block():
    return {"games": 0, "wins": 0, "avg_stars": 0.0, "best_stars": 0, "best_tags": None}


async def _compute_streak(db: AsyncSession, user_id, game_type: str):
    streak_r = await db.execute(
        text("""
            SELECT DISTINCT challenge_date FROM game_result
            WHERE user_id = :uid AND mode = 'daily' AND game_type = :gt
              AND challenge_date IS NOT NULL
            ORDER BY challenge_date DESC
            LIMIT 365
        """),
        {"uid": user_id, "gt": game_type},
    )
    dates = [r2[0] for r2 in streak_r.fetchall()]

    current_streak = 0
    max_streak = 0
    if dates:
        from datetime import date, timedelta
        today = date.today()
        expected = today
        for d in dates:
            if d == expected:
                current_streak += 1
                expected = expected - timedelta(days=1)
            elif d == today - timedelta(days=1) and current_streak == 0:
                current_streak = 1
                expected = d - timedelta(days=1)
            else:
                break
        prev = None
        run = 0
        for d in dates:
            if prev is None or prev - d == timedelta(days=1):
                run += 1
            else:
                run = 1
            max_streak = max(max_streak, run)
            prev = d
    return current_streak, max_streak


@router.get("/game/stats")
async def game_stats(
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        text("""
            SELECT
                game_type, mode,
                COUNT(*) AS games,
                SUM(CASE WHEN completed AND stars > 0 THEN 1 ELSE 0 END) AS wins,
                AVG(stars)::float AS avg_stars,
                MAX(stars) AS best_stars,
                MIN(CASE WHEN completed AND stars > 0 THEN tags_used END) AS best_tags
            FROM game_result
            WHERE user_id = :uid
            GROUP BY game_type, mode
        """),
        {"uid": user.id},
    )

    result = {
        "tag_it": {"daily": _empty_mode_block(), "free": _empty_mode_block()},
        "chain_it": {"daily": _empty_mode_block(), "free": _empty_mode_block()},
        "guess_it": {"daily": _empty_mode_block(), "free": _empty_mode_block()},
    }
    for row in r.fetchall():
        gt, mode = row[0], row[1]
        if gt not in result or mode not in ("daily", "free"):
            continue
        result[gt][mode] = {
            "games": row[2] or 0,
            "wins": row[3] or 0,
            "avg_stars": round(row[4], 2) if row[4] is not None else 0.0,
            "best_stars": row[5] or 0,
            "best_tags": row[6],
        }

    for gt in ("tag_it", "chain_it", "guess_it"):
        cs, ms = await _compute_streak(db, user.id, gt)
        result[gt]["daily"]["current_streak"] = cs
        result[gt]["daily"]["max_streak"] = ms

    # Back-compat: legacy clients expect top-level daily/free for Tag It.
    result["daily"] = result["tag_it"]["daily"]
    result["free"] = result["tag_it"]["free"]
    return result


# =============================================================================
# GET /game/history
# =============================================================================


@router.get("/game/history")
async def game_history(
    game_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    if game_type and game_type not in ("tag_it", "chain_it", "guess_it"):
        raise HTTPException(status_code=400, detail="invalid game_type")

    where = ["user_id = :uid"]
    params: dict = {"uid": user.id}
    if game_type:
        where.append("game_type = :gt")
        params["gt"] = game_type
    where_sql = " AND ".join(where)

    cr = await db.execute(text(f"SELECT COUNT(*) FROM game_result WHERE {where_sql}"), params)
    total = cr.scalar_one() or 0

    offset = (page - 1) * per_page
    params["lim"] = per_page
    params["off"] = offset

    sql = f"""
        SELECT gr.id, gr.game_type, gr.mode, gr.played_at, gr.stars, gr.completed,
               gr.tags_used, gr.chain_length, gr.lives_remaining, gr.jokers_used,
               gr.film_id, fp.original_title, fp.poster_url,
               gr.origin_film_id, fo.original_title, fo.poster_url,
               gr.target_film_id, ft.original_title, ft.poster_url,
               gr.difficulty, gr.pool_filters, gr.challenge_date, gr.tag_sequence
        FROM game_result gr
        LEFT JOIN film fp ON fp.film_id = gr.film_id
        LEFT JOIN film fo ON fo.film_id = gr.origin_film_id
        LEFT JOIN film ft ON ft.film_id = gr.target_film_id
        WHERE {where_sql}
        ORDER BY gr.played_at DESC
        LIMIT :lim OFFSET :off
    """
    rr = await db.execute(text(sql), params)
    rows = rr.fetchall()

    def f(fid, title, poster):
        if fid is None:
            return None
        return {"film_id": fid, "title": title, "poster_url": poster}

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "game_type": row[1],
            "mode": row[2],
            "played_at": row[3].isoformat() if row[3] else None,
            "stars": row[4],
            "completed": row[5],
            "tags_used": row[6],
            "chain_length": row[7],
            "lives_remaining": row[8],
            "jokers_used": row[9],
            "film": f(row[10], row[11], row[12]),
            "origin_film": f(row[13], row[14], row[15]),
            "target_film": f(row[16], row[17], row[18]),
            "difficulty": row[19],
            "pool_filters": row[20],
            "challenge_date": row[21].isoformat() if row[21] else None,
            "tag_sequence": row[22],
        })

    total_pages = (total + per_page - 1) // per_page if total else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


# =============================================================================
# Chain It — helpers
# =============================================================================


async def _fetch_film_tags(db: AsyncSession, film_id: int) -> dict[str, list[str]]:
    """Return all tags for a film, grouped by dimension."""
    result: dict[str, list[str]] = {dim: [] for dim in DIMENSION_TABLE_MAP}
    for dim, (jt, jfk, tt, tpk, tn) in DIMENSION_TABLE_MAP.items():
        r = await db.execute(
            text(
                f"SELECT t.{tn} FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} "
                f"WHERE j.film_id = :fid ORDER BY t.{tn}"
            ),
            {"fid": film_id},
        )
        result[dim] = [row[0] for row in r.fetchall()]

    # Pseudo-dimension: geography (country + state/city pulled from film_set_place)
    g = await db.execute(
        text("""
            SELECT DISTINCT g.country, g.state_city
            FROM film_set_place fsp
            JOIN geography g ON fsp.geography_id = g.geography_id
            WHERE fsp.film_id = :fid
        """),
        {"fid": film_id},
    )
    geo: set[str] = set()
    for row in g.fetchall():
        if row[0]:
            geo.add(row[0])
        if row[1]:
            geo.add(row[1])
    result["geography"] = sorted(geo)
    return result


async def _fetch_chain_film(db: AsyncSession, film_id: int) -> dict | None:
    r = await db.execute(
        text("SELECT film_id, original_title, first_release_date, poster_url FROM film WHERE film_id = :fid"),
        {"fid": film_id},
    )
    row = r.fetchone()
    return _film_row_to_dict(row) if row else None


DIFFICULTY_BOUNDS: dict[str, tuple[int, int]] = {
    # name: (min_shared_tags, max_shared_tags). Higher shared count = more similar = easier chain.
    "easy":   (12, 100),  # very similar — many overlapping tags, short chain expected
    "medium": (4, 8),     # moderate overlap
    "hard":   (1, 2),     # extremely distant — only 1–2 shared tags total
}


async def _pick_chain_pair(
    db: AsyncSession,
    pool_filters: dict | None = None,
    difficulty: str = "medium",
) -> tuple[int, int] | None:
    """Pick a winnable origin+target pair: both eligible, share ≥1 tag, similarity per difficulty."""
    lo, hi = DIFFICULTY_BOUNDS.get(difficulty, DIFFICULTY_BOUNDS["medium"])
    # Apply pool filters by picking eligible candidates from a filtered pool
    params: dict = {}
    where = ["f.poster_url IS NOT NULL", "f.summary IS NOT NULL"]
    where.extend(_apply_pool_filters(pool_filters, params, alias="f"))
    dim_unions = " UNION ALL ".join([
        f"SELECT DISTINCT film_id FROM {jt}" for (jt, _, _, _, _) in DIMENSION_TABLE_MAP.values()
    ])
    where_sql = " AND ".join(where)
    sql = f"""
        WITH dim_films AS (
            SELECT film_id, COUNT(*) AS n_dims FROM (
                {dim_unions}
            ) u GROUP BY film_id
        )
        SELECT f.film_id FROM film f
        JOIN dim_films d ON d.film_id = f.film_id
        WHERE d.n_dims >= 5 AND {where_sql}
        ORDER BY RANDOM() LIMIT 150
    """
    r = await db.execute(text(sql), params)
    candidates = [row[0] for row in r.fetchall()]
    if len(candidates) < 2:
        return None

    # Try pairs: must share ≥1 tag across any dimension, within the difficulty band.
    for _ in range(200):
        a, b = random.sample(candidates, 2)
        ta = await _fetch_film_tags(db, a)
        tb = await _fetch_film_tags(db, b)
        shared = 0
        for dim in DIMENSION_TABLE_MAP:
            sa = set(ta.get(dim) or [])
            sb = set(tb.get(dim) or [])
            shared += len(sa & sb)
        if lo <= shared <= hi:
            return (a, b)
    return None


# =============================================================================
# Chain It — endpoints
# =============================================================================


@router.get("/game/chain/daily")
async def chain_daily(
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    r = await db.execute(
        text("SELECT film_id, target_film_id FROM daily_challenge "
             "WHERE challenge_date = CURRENT_DATE AND game_type = 'chain_it'")
    )
    row = r.fetchone()
    if row is None:
        pair = await _pick_chain_pair(db)
        if pair is None:
            raise HTTPException(status_code=500, detail="Could not find a winnable pair")
        origin_id, target_id = pair
        await db.execute(
            text("""INSERT INTO daily_challenge (challenge_date, game_type, film_id, target_film_id)
                    VALUES (CURRENT_DATE, 'chain_it', :o, :t)
                    ON CONFLICT (challenge_date, game_type) DO NOTHING"""),
            {"o": origin_id, "t": target_id},
        )
        await db.commit()
    else:
        origin_id, target_id = row[0], row[1]

    origin = await _fetch_chain_film(db, origin_id)
    target = await _fetch_chain_film(db, target_id)
    if not origin or not target:
        raise HTTPException(status_code=500, detail="Pair films missing")
    origin_tags = await _fetch_film_tags(db, origin_id)

    pool = await db.execute(text("SELECT COUNT(*) FROM film WHERE poster_url IS NOT NULL"))
    pool_size = pool.scalar_one() or 0

    already_played = None
    if user:
        ar = await db.execute(
            text("""SELECT id, chain_length, lives_remaining, jokers_used, stars, tag_sequence,
                           completed, played_at, origin_film_id, target_film_id
                    FROM game_result
                    WHERE user_id = :uid AND mode = 'daily'
                      AND challenge_date = CURRENT_DATE AND game_type = 'chain_it'
                    LIMIT 1"""),
            {"uid": user.id},
        )
        ar_row = ar.fetchone()
        if ar_row:
            already_played = {
                "id": ar_row[0],
                "chain_length": ar_row[1],
                "lives_remaining": ar_row[2],
                "jokers_used": ar_row[3],
                "stars": ar_row[4],
                "tag_sequence": ar_row[5],
                "completed": ar_row[6],
                "played_at": ar_row[7].isoformat() if ar_row[7] else None,
                "origin_film_id": ar_row[8],
                "target_film_id": ar_row[9],
            }

    return {
        "origin": {**origin, "tags": origin_tags},
        "target": target,
        "pool_size": pool_size,
        "mode": "daily",
        "already_played": already_played,
    }


@router.get("/game/chain/random")
async def chain_random(
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    difficulty: str = Query("medium"),
    db: AsyncSession = Depends(get_db),
):
    if difficulty not in DIFFICULTY_BOUNDS:
        raise HTTPException(status_code=400, detail="difficulty must be easy/medium/hard")
    pool_filters: dict = {}
    if year_min is not None:
        pool_filters["year_min"] = year_min
    if year_max is not None:
        pool_filters["year_max"] = year_max
    if language:
        pool_filters["language"] = language

    pair = await _pick_chain_pair(db, pool_filters, difficulty=difficulty)
    if pair is None:
        raise HTTPException(status_code=400, detail="Could not find a winnable pair — broaden filters")
    origin_id, target_id = pair
    origin = await _fetch_chain_film(db, origin_id)
    target = await _fetch_chain_film(db, target_id)
    origin_tags = await _fetch_film_tags(db, origin_id)
    pool = await db.execute(text("SELECT COUNT(*) FROM film WHERE poster_url IS NOT NULL"))
    pool_size = pool.scalar_one() or 0
    return {
        "origin": {**origin, "tags": origin_tags},
        "target": target,
        "pool_size": pool_size,
        "mode": "free",
    }


@router.post("/game/chain/check-tag")
async def chain_check_tag(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    dim = body.get("dimension")
    val = body.get("value")
    if not target_film_id or not dim or not val:
        raise HTTPException(status_code=400, detail="target_film_id, dimension, value required")

    if dim == "geography":
        r = await db.execute(
            text("""
                SELECT 1 FROM film_set_place fsp
                JOIN geography g ON fsp.geography_id = g.geography_id
                WHERE fsp.film_id = :fid AND (g.country = :v OR g.state_city = :v)
                LIMIT 1
            """),
            {"fid": target_film_id, "v": val},
        )
        return {"correct": r.fetchone() is not None}

    if dim not in DIMENSION_TABLE_MAP:
        raise HTTPException(status_code=400, detail="invalid dimension")
    jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
    r = await db.execute(
        text(
            f"SELECT 1 FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} "
            f"WHERE j.film_id = :fid AND t.{tn} = :v LIMIT 1"
        ),
        {"fid": target_film_id, "v": val},
    )
    return {"correct": r.fetchone() is not None}


@router.post("/game/chain/get-films")
async def chain_get_films(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    tags = body.get("tags") or []
    exclude_ids = body.get("exclude_film_ids") or []
    target_film_id = body.get("target_film_id")
    pool_filters = body.get("pool_filters")
    randomize = bool(body.get("random"))
    difficulty = body.get("difficulty") or "medium"
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    params: dict = {}
    where_clauses = _build_tag_clauses(tags, params)
    where_clauses.extend(_apply_pool_filters(pool_filters, params))
    where_clauses.append("poster_url IS NOT NULL")
    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Total pool excluding chain films already used
    excl_params: dict = dict(params)
    excl_clause = ""
    if exclude_ids:
        excl_clause = " AND film_id <> ALL(:excl)"
        excl_params["excl"] = exclude_ids
    pool_r = await db.execute(
        text(f"SELECT COUNT(*) FROM film WHERE {where_sql}{excl_clause}"),
        excl_params,
    )
    pool_size = pool_r.scalar_one() or 0

    # Target visibility: when pool drops to ≤ 10 distinct candidates (excluding chain films).
    target_visible = pool_size <= 10

    # If target not visible, also exclude target from results
    # Build result exclusion list: drop target when visible, keep it otherwise.
    result_excl = [i for i in exclude_ids if i != target_film_id]
    if not target_visible and target_film_id is not None:
        result_excl.append(target_film_id)

    pick_params: dict = dict(params)
    pick_excl = ""
    if result_excl:
        pick_excl = " AND film_id <> ALL(:excl)"
        pick_params["excl"] = result_excl
    if not randomize and difficulty == "easy" and target_film_id is not None:
        # Order candidates by how many tags they share with the target — surfaces
        # the films "closest" to the target so the player gets natural breadcrumbs.
        all_tags_union = " UNION ALL ".join([
            f"SELECT film_id, '{dim}:'||{jfk} AS tag_key FROM {jt}"
            for dim, (jt, jfk, _, _, _) in DIMENSION_TABLE_MAP.items()
        ])
        pick_params["tgt"] = target_film_id
        sql = f"""
            WITH all_tags AS ({all_tags_union}),
            target_keys AS (SELECT DISTINCT tag_key FROM all_tags WHERE film_id = :tgt),
            overlap AS (
                SELECT a.film_id AS fid, COUNT(*) AS shared
                FROM all_tags a
                JOIN target_keys t ON a.tag_key = t.tag_key
                GROUP BY a.film_id
            )
            SELECT film.film_id, original_title, first_release_date, poster_url
            FROM film
            LEFT JOIN overlap ON overlap.fid = film.film_id
            WHERE {where_sql}{pick_excl}
            ORDER BY COALESCE(overlap.shared, 0) DESC, film.weighted_score DESC NULLS LAST
            LIMIT 20
        """
    else:
        order_by = "RANDOM()" if (randomize or difficulty == "hard") else "weighted_score DESC NULLS LAST"
        sql = f"""
            SELECT film_id, original_title, first_release_date, poster_url
            FROM film
            WHERE {where_sql}{pick_excl}
            ORDER BY {order_by}
            LIMIT 20
        """
    rr = await db.execute(text(sql), pick_params)
    films = [_film_row_to_dict(row) for row in rr.fetchall()]
    return {"films": films, "pool_size": pool_size, "target_visible": target_visible}


@router.post("/game/chain/get-tags")
async def chain_get_tags(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    film_id = body.get("film_id")
    if not film_id:
        raise HTTPException(status_code=400, detail="film_id required")
    tags = await _fetch_film_tags(db, film_id)
    return {"tags": tags}


@router.post("/game/chain/joker/synopsis")
async def chain_joker_synopsis(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    if not target_film_id:
        raise HTTPException(status_code=400, detail="target_film_id required")
    r = await db.execute(text("SELECT summary FROM film WHERE film_id = :fid"), {"fid": target_film_id})
    row = r.fetchone()
    return {"synopsis": row[0] if row else None}


@router.post("/game/chain/joker/reveal-tag")
async def chain_joker_reveal_tag(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    current_film_id = body.get("current_film_id")
    used_dimensions = set(body.get("used_dimensions") or [])
    used_values = {(t.get("dimension"), t.get("value")) for t in (body.get("used_tags") or [])}
    if not target_film_id:
        raise HTTPException(status_code=400, detail="target_film_id required")

    target_tags = await _fetch_film_tags(db, target_film_id)
    current_tags = await _fetch_film_tags(db, current_film_id) if current_film_id else {}

    def filter_candidates(pairs):
        return [
            (d, t) for (d, t) in pairs
            if d not in used_dimensions and (d, t) not in used_values
        ]

    # Prefer tags that are in BOTH target and current film
    if current_tags:
        shared = [
            (dim, tag)
            for dim, vals in target_tags.items()
            for tag in vals
            if tag in (current_tags.get(dim) or [])
        ]
        candidates = filter_candidates(shared)
        if candidates:
            dim, tag = random.choice(candidates)
            return {"dimension": dim, "tag": tag, "in_current": True}

    # Fallback: any target tag not in used dimensions
    all_pairs = [(dim, tag) for dim, vals in target_tags.items() for tag in vals]
    candidates = filter_candidates(all_pairs)
    if not candidates:
        return {"dimension": None, "tag": None, "in_current": False}
    dim, tag = random.choice(candidates)
    return {"dimension": dim, "tag": tag, "in_current": False}


# =============================================================================
# Guess It — helpers & endpoints
# =============================================================================


_GUESS_DIM_LABELS = {
    "categories": "Genre",
    "themes": "Theme",
    "atmospheres": "Atmosphere",
    "characters": "Characters",
    "motivations": "Motivation",
    "messages": "Message",
    "cinema_types": "Cinema type",
    "time_periods": "Time period",
    "place_contexts": "Place",
}


async def _build_guess_grid(
    db: AsyncSession,
    target_film_id: int,
    pool_filters: dict | None = None,
    difficulty: str = "medium",
) -> list[int]:
    """Build an 11-decoy list (target excluded) at varying similarity.

    Difficulty controls the mix:
      easy   → mostly loosely-related films (rank 30-100 + random popular)
      medium → 3 close / 4 mid / 4 loose
      hard   → mostly highly-similar films (rank 1-15)
    Pool filters (year/language) restrict every candidate.
    """
    from backend.app.services.recommender import get_similar_films

    similar = await get_similar_films(db, target_film_id, limit=100, tier="admin")
    similar_ids = [s["film_id"] for s in similar if s["film_id"] != target_film_id]

    # Filter similar_ids by pool_filters if any.
    if pool_filters and similar_ids:
        params: dict = {"ids": similar_ids}
        where = ["film_id = ANY(:ids)"]
        pf_clauses = _apply_pool_filters(pool_filters, params)
        where.extend(pf_clauses)
        r = await db.execute(
            text(f"SELECT film_id FROM film WHERE {' AND '.join(where)}"),
            params,
        )
        allowed = {row[0] for row in r.fetchall()}
        similar_ids = [fid for fid in similar_ids if fid in allowed]

    decoys: list[int] = []

    if difficulty == "hard":
        # Previously "medium" — balanced 3/4/4 gradient.
        top_pool = similar_ids[:10]
        if top_pool:
            decoys.extend(random.sample(top_pool, min(3, len(top_pool))))
        mid_pool = [fid for fid in similar_ids[10:30] if fid not in decoys]
        if mid_pool:
            decoys.extend(random.sample(mid_pool, min(4, len(mid_pool))))
        low_pool = [fid for fid in similar_ids[30:60] if fid not in decoys]
        if low_pool:
            decoys.extend(random.sample(low_pool, min(4, len(low_pool))))
    elif difficulty == "easy":
        # Mostly loosely-related, no very-similar decoys → easier to eliminate.
        low_pool = [fid for fid in similar_ids[30:100]]
        if low_pool:
            decoys.extend(random.sample(low_pool, min(7, len(low_pool))))
        mid_pool = [fid for fid in similar_ids[15:30] if fid not in decoys]
        if mid_pool:
            decoys.extend(random.sample(mid_pool, min(11 - len(decoys), len(mid_pool))))
    else:  # medium — softer than before: 1 close / 3 mid / 7 loose
        top_pool = similar_ids[:10]
        if top_pool:
            decoys.extend(random.sample(top_pool, min(1, len(top_pool))))
        mid_pool = [fid for fid in similar_ids[10:30] if fid not in decoys]
        if mid_pool:
            decoys.extend(random.sample(mid_pool, min(3, len(mid_pool))))
        low_pool = [fid for fid in similar_ids[30:100] if fid not in decoys]
        if low_pool:
            decoys.extend(random.sample(low_pool, min(11 - len(decoys), len(low_pool))))

    if len(decoys) < 11:
        existing = set(decoys + [target_film_id])
        fill_params: dict = {"excl": list(existing), "n": 11 - len(decoys)}
        fill_where = ["poster_url IS NOT NULL", "film_id <> ALL(:excl)"]
        fill_where.extend(_apply_pool_filters(pool_filters, fill_params))
        order = "weighted_score DESC NULLS LAST, RANDOM()" if difficulty == "easy" else "RANDOM()"
        r = await db.execute(
            text(f"""SELECT film_id FROM film
                     WHERE {' AND '.join(fill_where)}
                     ORDER BY {order} LIMIT :n"""),
            fill_params,
        )
        decoys.extend([row[0] for row in r.fetchall()])

    return decoys[:11]


def _deterministic_shuffle(items: list[int], seed: str) -> list[int]:
    rnd = random.Random(seed)
    out = list(items)
    rnd.shuffle(out)
    return out


@router.get("/game/guess/daily")
async def guess_daily(
    db: AsyncSession = Depends(get_db),
    user: UserInfo | None = Depends(get_current_user),
):
    r = await db.execute(
        text("""SELECT film_id, decoy_film_ids FROM daily_challenge
                WHERE challenge_date = CURRENT_DATE AND game_type = 'guess_it'"""),
    )
    row = r.fetchone()
    if row is None:
        target_id = await _pick_eligible_film(db)
        if target_id is None:
            raise HTTPException(status_code=500, detail="No eligible film found")
        decoys = await _build_guess_grid(db, target_id)
        await db.execute(
            text("""INSERT INTO daily_challenge (challenge_date, game_type, film_id, decoy_film_ids)
                    VALUES (CURRENT_DATE, 'guess_it', :f, :d)
                    ON CONFLICT (challenge_date, game_type) DO NOTHING"""),
            {"f": target_id, "d": decoys},
        )
        await db.commit()
    else:
        target_id, decoys = row[0], list(row[1] or [])

    grid_ids = _deterministic_shuffle([target_id] + decoys, f"guess-{target_id}-daily")
    films = await _fetch_films(db, grid_ids)

    already_played = None
    if user:
        ar = await db.execute(
            text("""SELECT film_id, tags_used, lives_remaining, jokers_used, stars,
                           tag_sequence, completed, played_at
                    FROM game_result
                    WHERE user_id = :uid AND mode = 'daily'
                      AND challenge_date = CURRENT_DATE AND game_type = 'guess_it'
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
        "grid": films,
        "target_film_id": target_id,
        "mode": "daily",
        "already_played": already_played,
    }


@router.get("/game/guess/random")
async def guess_random(
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    difficulty: str = Query("medium"),
    db: AsyncSession = Depends(get_db),
):
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    params: dict = {}
    where = ["f.poster_url IS NOT NULL", "f.summary IS NOT NULL"]
    pool_filters: dict = {}
    if year_min is not None:
        pool_filters["year_min"] = year_min
    if year_max is not None:
        pool_filters["year_max"] = year_max
    if language:
        pool_filters["language"] = language
    where.extend(_apply_pool_filters(pool_filters, params, alias="f"))

    dim_unions = " UNION ALL ".join([
        f"SELECT DISTINCT film_id FROM {jt}" for (jt, _, _, _, _) in DIMENSION_TABLE_MAP.values()
    ])
    where_sql = " AND ".join(where)
    pick_sql = f"""
        WITH dim_films AS (
            SELECT film_id, COUNT(*) AS n_dims FROM (
                {dim_unions}
            ) u GROUP BY film_id
        )
        SELECT f.film_id
        FROM film f
        JOIN dim_films d ON d.film_id = f.film_id
        WHERE d.n_dims >= 5 AND {where_sql}
        ORDER BY RANDOM() LIMIT 1
    """
    r = await db.execute(text(pick_sql), params)
    row = r.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="No eligible film in this pool")
    target_id = row[0]

    decoys = await _build_guess_grid(db, target_id, pool_filters, difficulty=difficulty)
    grid_ids = [target_id] + decoys
    random.shuffle(grid_ids)
    films = await _fetch_films(db, grid_ids)
    return {"grid": films, "target_film_id": target_id, "mode": "free"}


async def _film_has_tag(db: AsyncSession, film_id: int, dim: str, value: str) -> bool:
    if dim not in DIMENSION_TABLE_MAP:
        return False
    jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
    r = await db.execute(
        text(
            f"SELECT 1 FROM {jt} j JOIN {tt} t ON j.{jfk} = t.{tpk} "
            f"WHERE j.film_id = :fid AND t.{tn} = :v LIMIT 1"
        ),
        {"fid": film_id, "v": value},
    )
    return r.fetchone() is not None


@router.post("/game/guess/reveal-tag")
async def guess_reveal_tag(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    revealed_tags = body.get("revealed_tags") or []
    remaining_film_ids = body.get("remaining_film_ids") or []
    difficulty = body.get("difficulty") or "medium"
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    if not target_film_id:
        raise HTTPException(status_code=400, detail="target_film_id required")

    target_tags = await _fetch_film_tags(db, target_film_id)
    revealed_set = {(t.get("dimension"), t.get("value")) for t in revealed_tags}
    revealed_dims = {t.get("dimension") for t in revealed_tags}

    # Build candidate tags from target (skip already revealed and pseudo-dims like geography)
    candidates: list[tuple[str, str]] = []
    for dim, vals in target_tags.items():
        if dim not in DIMENSION_TABLE_MAP:
            continue
        for tag in vals:
            if (dim, tag) in revealed_set:
                continue
            candidates.append((dim, tag))

    if not candidates:
        return {"dimension": None, "tag": None, "display": None}

    # For each candidate, count how many remaining decoys share that tag with the target.
    # Difficulty tunes which count we prefer:
    #   easy   → low count (highly discriminative: many decoys can be eliminated)
    #   medium → middling count (≈ N/2; balanced)
    #   hard   → high count (most decoys also have it; few eliminations, much ambiguity)
    decoy_ids = [fid for fid in remaining_film_ids if fid != target_film_id]
    n = max(1, len(decoy_ids))

    scored: list[tuple[str, str, int]] = []
    for dim, tag in candidates:
        if not decoy_ids:
            count = 0
        else:
            jt, jfk, tt, tpk, tn = DIMENSION_TABLE_MAP[dim]
            r = await db.execute(
                text(
                    f"SELECT COUNT(DISTINCT j.film_id) FROM {jt} j "
                    f"JOIN {tt} t ON j.{jfk} = t.{tpk} "
                    f"WHERE t.{tn} = :v AND j.film_id = ANY(:ids)"
                ),
                {"v": tag, "ids": decoy_ids},
            )
            count = r.scalar_one() or 0
        scored.append((dim, tag, count))

    if not scored:
        return {"dimension": None, "tag": None, "display": None}

    if difficulty == "easy":
        # Lowest count → highly discriminative.
        key_fn = lambda x: (x[2], 0 if x[0] not in revealed_dims else 1, random.random())
    elif difficulty == "hard":
        # Balanced — about half the decoys share the tag (was the previous "medium").
        target_count = max(1, n // 2)
        key_fn = lambda x: (abs(x[2] - target_count), 0 if x[0] not in revealed_dims else 1, random.random())
    else:
        # Medium — softer than before: target ≈ N/3, so most decoys still don't have the tag
        # and can be safely eliminated.
        target_count = max(1, n // 3)
        key_fn = lambda x: (abs(x[2] - target_count), 0 if x[0] not in revealed_dims else 1, random.random())

    scored.sort(key=key_fn)
    dim, tag, _ = scored[0]
    label = _GUESS_DIM_LABELS.get(dim, dim)
    return {"dimension": dim, "tag": tag, "display": f"{label}: {tag}"}


@router.post("/game/guess/remove")
async def guess_remove(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    film_id_to_remove = body.get("film_id_to_remove")
    revealed_tags = body.get("revealed_tags") or []
    if not target_film_id or not film_id_to_remove:
        raise HTTPException(status_code=400, detail="film ids required")

    if film_id_to_remove == target_film_id:
        return {"correct": False, "is_target": True}

    # Film "matches all revealed tags" → wrong removal.
    matches_all = True
    for t in revealed_tags:
        dim = t.get("dimension")
        val = t.get("value")
        if not dim or not val:
            continue
        if not await _film_has_tag(db, film_id_to_remove, dim, val):
            matches_all = False
            break

    if matches_all and revealed_tags:
        return {"correct": False, "is_target": False}
    return {"correct": True, "is_target": False}


@router.post("/game/guess/early-guess")
async def guess_early(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    guessed_film_id = body.get("guessed_film_id")
    if not target_film_id or not guessed_film_id:
        raise HTTPException(status_code=400, detail="film ids required")
    return {"correct": target_film_id == guessed_film_id}


@router.post("/game/guess/joker/synopsis")
async def guess_joker_synopsis(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Reveal the synopsis of a random remaining film (may or may not be target).

    Body: {remaining_film_ids: [int], used_film_ids: [int]}
    """
    remaining = body.get("remaining_film_ids") or []
    used = set(body.get("used_film_ids") or [])
    pool = [fid for fid in remaining if fid not in used]
    if not pool:
        return {"film_id": None, "synopsis": None}
    fid = random.choice(pool)
    r = await db.execute(text("SELECT summary FROM film WHERE film_id = :fid"), {"fid": fid})
    row = r.fetchone()
    return {"film_id": fid, "synopsis": row[0] if row else None}


@router.post("/game/guess/joker/decade")
async def guess_joker_decade(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    target_film_id = body.get("target_film_id")
    if not target_film_id:
        raise HTTPException(status_code=400, detail="target_film_id required")
    r = await db.execute(text("SELECT first_release_date FROM film WHERE film_id = :fid"), {"fid": target_film_id})
    row = r.fetchone()
    y = _year_from_date(row[0]) if row else None
    if y is None:
        return {"decade": None}
    return {"decade": f"{(y // 10) * 10}s"}
