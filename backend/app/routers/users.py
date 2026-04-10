"""
User film status endpoints — seen, favorite, watchlist per user per film.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import UserInfo, require_authenticated
from backend.app.database import get_db
from backend.app.schemas.film import FilmListItem, PaginatedFilms, UserFilmStatus

router = APIRouter(tags=["users"])


@router.get("/users/me/films", response_model=PaginatedFilms)
async def list_user_films(
    filter: str = Query(..., pattern="^(seen|favorite|watchlist)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    user: UserInfo = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db),
):
    uid = user.id

    # Count
    count_sql = f"SELECT COUNT(*) FROM user_film_status ufs JOIN film f ON ufs.film_id = f.film_id WHERE ufs.user_id = :uid AND ufs.{filter} = TRUE"
    r = await db.execute(text(count_sql), {"uid": uid})
    total = r.scalar_one()

    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    # Main query
    list_sql = f"""
        SELECT f.film_id, f.original_title, f.first_release_date, f.duration,
               f.poster_url, ufs.seen, ufs.favorite, ufs.watchlist, ufs.rating
        FROM user_film_status ufs
        JOIN film f ON ufs.film_id = f.film_id
        WHERE ufs.user_id = :uid AND ufs.{filter} = TRUE
        ORDER BY ufs.updated_at DESC NULLS LAST, f.film_id ASC
        LIMIT :limit OFFSET :offset
    """
    result = await db.execute(text(list_sql), {"uid": uid, "limit": per_page, "offset": offset})
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
