"""
User film status endpoints — seen, favorite, watchlist per user per film.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import UserInfo, require_authenticated
from backend.app.database import get_db

router = APIRouter(tags=["users"])


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
