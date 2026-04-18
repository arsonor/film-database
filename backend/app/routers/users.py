"""
User film status endpoints — seen, favorite, watchlist per user per film.
User custom lists — create, delete, add/remove films.
"""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import UserInfo, require_authenticated
from backend.app.database import get_db
from backend.app.schemas.film import FilmListItem, PaginatedFilms, UserFilmStatus
from backend.app.tier_config import TIER_MAX_LISTS

router = APIRouter(tags=["users"])


@router.get("/users/me/films", response_model=PaginatedFilms)
async def list_user_films(
    filter: str = Query(..., pattern="^(seen|favorite|watchlist)$"),
    sort_by: str = Query("recent", pattern="^(recent|year|rating|popularity)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    language: str | None = Query(None),
    categories: list[str] | None = Query(None),
    rating_min: int | None = Query(None, ge=0, le=10),
    rating_max: int | None = Query(None, ge=0, le=10),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    uid = user.id

    where_clauses = [f"ufs.user_id = :uid AND ufs.{filter} = TRUE"]
    params: dict = {"uid": uid}

    if year_min is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) >= :year_min")
        params["year_min"] = year_min
    if year_max is not None:
        where_clauses.append("EXTRACT(YEAR FROM f.first_release_date) <= :year_max")
        params["year_max"] = year_max
    if language:
        where_clauses.append("""
            EXISTS (SELECT 1 FROM film_language fl JOIN language l ON fl.language_id = l.language_id
                    WHERE fl.film_id = f.film_id AND fl.is_original = TRUE
                    AND l.language_name ILIKE :language)
        """)
        params["language"] = f"%{language}%"
    if categories:
        where_clauses.append("""
            EXISTS (SELECT 1 FROM film_genre fg JOIN category c ON fg.category_id = c.category_id
                    WHERE fg.film_id = f.film_id AND c.category_name = ANY(:categories)
                    AND c.historic_subcategory_name IS NULL)
        """)
        params["categories"] = categories
    if rating_min is not None and rating_max is not None and rating_min == 0 and rating_max == 0:
        where_clauses.append("ufs.rating IS NULL")
    else:
        if rating_min is not None and rating_min > 0:
            where_clauses.append("ufs.rating >= :rating_min")
            params["rating_min"] = rating_min
        if rating_max is not None and rating_max < 10:
            where_clauses.append("ufs.rating <= :rating_max")
            params["rating_max"] = rating_max

    where_sql = " AND ".join(where_clauses)

    # Count
    count_sql = f"SELECT COUNT(*) FROM user_film_status ufs JOIN film f ON ufs.film_id = f.film_id WHERE {where_sql}"
    r = await db.execute(text(count_sql), params)
    total = r.scalar_one()

    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    sort_col_map = {
        "recent": "ufs.updated_at",
        "year": "f.first_release_date",
        "rating": "ufs.rating",
        "popularity": "f.weighted_score",
    }
    sort_col = sort_col_map[sort_by]
    order = sort_order.upper()
    nulls = "NULLS LAST" if order == "DESC" else "NULLS FIRST"

    # Main query
    list_sql = f"""
        SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
               f.poster_url, ufs.seen, ufs.favorite, ufs.watchlist, ufs.rating
        FROM user_film_status ufs
        JOIN film f ON ufs.film_id = f.film_id
        WHERE {where_sql}
        ORDER BY {sort_col} {order} {nulls}, f.film_id ASC
        LIMIT :limit OFFSET :offset
    """
    result = await db.execute(text(list_sql), {**params, "limit": per_page, "offset": offset})
    rows = result.fetchall()

    film_ids = [r[0] for r in rows]
    items: list[FilmListItem] = []

    if film_ids:
        # Batch load categories
        cat_result = await db.execute(
            text("""
                SELECT fg.film_id, c.category_name
                FROM film_genre fg
                JOIN category c ON fg.category_id = c.category_id
                WHERE fg.film_id = ANY(:film_ids) AND c.historic_subcategory_name IS NULL
                ORDER BY fg.film_id, c.category_name
            """),
            {"film_ids": film_ids},
        )
        cat_map: dict[int, list[str]] = {}
        for fid, cname in cat_result.fetchall():
            cat_map.setdefault(fid, []).append(cname)

        # Batch load directors
        dir_result = await db.execute(
            text("""
                SELECT cr.film_id, COALESCE(p.firstname, '') || ' ' || p.lastname AS director_name
                FROM crew cr
                JOIN person p ON cr.person_id = p.person_id
                JOIN person_job pj ON cr.job_id = pj.job_id
                WHERE cr.film_id = ANY(:film_ids) AND pj.role_name = 'Director'
                ORDER BY cr.film_id
            """),
            {"film_ids": film_ids},
        )
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
                    user_status=UserFilmStatus(
                        seen=r[5] or False,
                        favorite=r[6] or False,
                        watchlist=r[7] or False,
                        rating=r[8],
                    ),
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


@router.get("/users/me/films/{film_id}/status")
async def get_film_status(
    film_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT seen, favorite, watchlist, rating, notes
            FROM user_film_status
            WHERE user_id = :uid AND film_id = :fid
        """),
        {"uid": user.id, "fid": film_id},
    )
    row = result.fetchone()
    if not row:
        return {"seen": False, "favorite": False, "watchlist": False, "rating": None, "notes": None}
    return {"seen": row[0], "favorite": row[1], "watchlist": row[2], "rating": row[3], "notes": row[4]}


@router.put("/users/me/films/{film_id}/status")
async def update_film_status(
    film_id: int,
    body: dict,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    # Validate film exists
    r = await db.execute(text("SELECT film_id FROM film WHERE film_id = :fid"), {"fid": film_id})
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Film not found")

    # Upsert user_film_status
    await db.execute(
        text("""
            INSERT INTO user_film_status (user_id, film_id, seen, favorite, watchlist, rating, notes)
            VALUES (:uid, :fid, :seen, :fav, :wl, :rating, :notes)
            ON CONFLICT (user_id, film_id) DO UPDATE SET
                seen = COALESCE(:seen, user_film_status.seen),
                favorite = COALESCE(:fav, user_film_status.favorite),
                watchlist = COALESCE(:wl, user_film_status.watchlist),
                rating = COALESCE(:rating, user_film_status.rating),
                notes = COALESCE(:notes, user_film_status.notes)
        """),
        {
            "uid": user.id, "fid": film_id,
            "seen": body.get("seen"),
            "fav": body.get("favorite"),
            "wl": body.get("watchlist"),
            "rating": body.get("rating"),
            "notes": body.get("notes"),
        },
    )
    await db.commit()
    return {"film_id": film_id, "updated": True}


# =============================================================================
# Custom Lists
# =============================================================================


class ListCreate(BaseModel):
    name: str


class ListOut(BaseModel):
    list_id: int
    list_name: str
    film_count: int


@router.get("/users/me/lists", response_model=list[ListOut])
async def get_user_lists(
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT ul.list_id, ul.list_name, COUNT(ulf.film_id) AS film_count
            FROM user_list ul
            LEFT JOIN user_list_film ulf ON ul.list_id = ulf.list_id
            WHERE ul.user_id = :uid
            GROUP BY ul.list_id, ul.list_name
            ORDER BY ul.created_at
        """),
        {"uid": user.id},
    )
    return [ListOut(list_id=r[0], list_name=r[1], film_count=r[2]) for r in result.fetchall()]


@router.post("/users/me/lists", response_model=ListOut, status_code=201)
async def create_user_list(
    body: ListCreate,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="List name cannot be empty")

    max_lists = TIER_MAX_LISTS.get(user.tier, 0)
    if max_lists is not None:
        r = await db.execute(
            text("SELECT COUNT(*) FROM user_list WHERE user_id = :uid"),
            {"uid": user.id},
        )
        if r.scalar_one() >= max_lists:
            raise HTTPException(
                status_code=403,
                detail=f"List limit reached ({max_lists} max for your tier)",
            )

    try:
        result = await db.execute(
            text("INSERT INTO user_list (user_id, list_name) VALUES (:uid, :name) RETURNING list_id"),
            {"uid": user.id, "name": name},
        )
        list_id = result.scalar_one()
        await db.commit()
        return ListOut(list_id=list_id, list_name=name, film_count=0)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A list with this name already exists")


@router.delete("/users/me/lists/{list_id}", status_code=204)
async def delete_user_list(
    list_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("DELETE FROM user_list WHERE list_id = :lid AND user_id = :uid RETURNING list_id"),
        {"lid": list_id, "uid": user.id},
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="List not found")
    await db.commit()


@router.get("/users/me/lists/{list_id}/films", response_model=PaginatedFilms)
async def list_films_in_list(
    list_id: int,
    sort_by: str = Query("recent", pattern="^(recent|year|rating|popularity)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    owner = await db.execute(
        text("SELECT user_id FROM user_list WHERE list_id = :lid"),
        {"lid": list_id},
    )
    row = owner.fetchone()
    if not row or str(row[0]) != str(user.id):
        raise HTTPException(status_code=404, detail="List not found")

    uid = user.id

    count_sql = """
        SELECT COUNT(*) FROM user_list_film ulf
        JOIN film f ON ulf.film_id = f.film_id
        WHERE ulf.list_id = :lid
    """
    r = await db.execute(text(count_sql), {"lid": list_id})
    total = r.scalar_one()
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    sort_col_map = {
        "recent": "ulf.added_at",
        "year": "f.first_release_date",
        "rating": "ufs.rating",
        "popularity": "f.weighted_score",
    }
    sort_col = sort_col_map[sort_by]
    order = sort_order.upper()
    nulls = "NULLS LAST" if order == "DESC" else "NULLS FIRST"

    list_sql = f"""
        SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
               f.poster_url, ufs.seen, ufs.favorite, ufs.watchlist, ufs.rating
        FROM user_list_film ulf
        JOIN film f ON ulf.film_id = f.film_id
        LEFT JOIN user_film_status ufs ON ufs.film_id = f.film_id AND ufs.user_id = :uid
        WHERE ulf.list_id = :lid
        ORDER BY {sort_col} {order} {nulls}, f.film_id ASC
        LIMIT :limit OFFSET :offset
    """
    result = await db.execute(text(list_sql), {"lid": list_id, "uid": uid, "limit": per_page, "offset": offset})
    rows = result.fetchall()

    film_ids = [r[0] for r in rows]
    items: list[FilmListItem] = []

    if film_ids:
        cat_result = await db.execute(
            text("""
                SELECT fg.film_id, c.category_name
                FROM film_genre fg JOIN category c ON fg.category_id = c.category_id
                WHERE fg.film_id = ANY(:film_ids) AND c.historic_subcategory_name IS NULL
                ORDER BY fg.film_id, c.category_name
            """),
            {"film_ids": film_ids},
        )
        cat_map: dict[int, list[str]] = {}
        for fid, cname in cat_result.fetchall():
            cat_map.setdefault(fid, []).append(cname)

        dir_result = await db.execute(
            text("""
                SELECT cr.film_id, COALESCE(p.firstname, '') || ' ' || p.lastname
                FROM crew cr JOIN person p ON cr.person_id = p.person_id
                JOIN person_job pj ON cr.job_id = pj.job_id
                WHERE cr.film_id = ANY(:film_ids) AND pj.role_name = 'Director'
                ORDER BY cr.film_id
            """),
            {"film_ids": film_ids},
        )
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
                    user_status=UserFilmStatus(
                        seen=r[5] or False, favorite=r[6] or False,
                        watchlist=r[7] or False, rating=r[8],
                    ) if r[5] is not None else None,
                    categories=cat_map.get(fid, []),
                    director=dir_map.get(fid),
                )
            )

    return PaginatedFilms(total=total, page=page, per_page=per_page, total_pages=total_pages, items=items)


@router.post("/users/me/lists/{list_id}/films/{film_id}", status_code=201)
async def add_film_to_list(
    list_id: int,
    film_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    owner = await db.execute(
        text("SELECT user_id FROM user_list WHERE list_id = :lid"),
        {"lid": list_id},
    )
    row = owner.fetchone()
    if not row or str(row[0]) != str(user.id):
        raise HTTPException(status_code=404, detail="List not found")

    try:
        await db.execute(
            text("INSERT INTO user_list_film (list_id, film_id) VALUES (:lid, :fid)"),
            {"lid": list_id, "fid": film_id},
        )
        await db.commit()
        return {"list_id": list_id, "film_id": film_id, "added": True}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Film already in list")


@router.delete("/users/me/lists/{list_id}/films/{film_id}", status_code=204)
async def remove_film_from_list(
    list_id: int,
    film_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    owner = await db.execute(
        text("SELECT user_id FROM user_list WHERE list_id = :lid"),
        {"lid": list_id},
    )
    row = owner.fetchone()
    if not row or str(row[0]) != str(user.id):
        raise HTTPException(status_code=404, detail="List not found")

    await db.execute(
        text("DELETE FROM user_list_film WHERE list_id = :lid AND film_id = :fid"),
        {"lid": list_id, "fid": film_id},
    )
    await db.commit()


@router.get("/users/me/films/{film_id}/lists", response_model=list[int])
async def get_film_list_memberships(
    film_id: int,
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Return list_ids that this film belongs to for the current user."""
    result = await db.execute(
        text("""
            SELECT ulf.list_id FROM user_list_film ulf
            JOIN user_list ul ON ulf.list_id = ul.list_id
            WHERE ulf.film_id = :fid AND ul.user_id = :uid
        """),
        {"fid": film_id, "uid": user.id},
    )
    return [r[0] for r in result.fetchall()]
