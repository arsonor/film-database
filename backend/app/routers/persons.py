"""
Person API endpoints — detail with filmography, search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.person import (
    FilmographyEntry,
    PersonDetail,
    PersonSummary,
)

router = APIRouter(tags=["persons"])


@router.get("/persons/search", response_model=list[PersonSummary])
async def search_persons(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT person_id, firstname, lastname, photo_url
            FROM person
            WHERE (COALESCE(firstname, '') || ' ' || lastname) ILIKE :q
            ORDER BY lastname, firstname
            LIMIT :limit
        """),
        {"q": f"%{q}%", "limit": limit},
    )
    return [
        PersonSummary(person_id=r[0], firstname=r[1], lastname=r[2], photo_url=r[3])
        for r in result.fetchall()
    ]


@router.get("/persons/{person_id}", response_model=PersonDetail)
async def get_person(person_id: int, db: AsyncSession = Depends(get_db)):
    # Person info
    result = await db.execute(
        text("SELECT * FROM person WHERE person_id = :pid"),
        {"pid": person_id},
    )
    person = result.mappings().first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Filmography: crew roles
    crew_result = await db.execute(
        text("""
            SELECT f.film_id, f.original_title, f.first_release_date, f.poster_url,
                   pj.role_name
            FROM crew cr
            JOIN film f ON cr.film_id = f.film_id
            JOIN person_job pj ON cr.job_id = pj.job_id
            WHERE cr.person_id = :pid
            ORDER BY f.first_release_date DESC NULLS LAST
        """),
        {"pid": person_id},
    )
    crew_rows = crew_result.fetchall()

    # Filmography: cast roles
    cast_result = await db.execute(
        text("""
            SELECT f.film_id, f.original_title, f.first_release_date, f.poster_url,
                   ca.character_name
            FROM casting ca
            JOIN film f ON ca.film_id = f.film_id
            WHERE ca.person_id = :pid
            ORDER BY f.first_release_date DESC NULLS LAST
        """),
        {"pid": person_id},
    )
    cast_rows = cast_result.fetchall()

    # Merge into filmography entries
    film_map: dict[int, FilmographyEntry] = {}
    for r in crew_rows:
        fid = r[0]
        if fid not in film_map:
            film_map[fid] = FilmographyEntry(
                film_id=fid,
                original_title=r[1],
                first_release_date=r[2],
                poster_url=r[3],
            )
        film_map[fid].roles.append(r[4])

    for r in cast_rows:
        fid = r[0]
        if fid not in film_map:
            film_map[fid] = FilmographyEntry(
                film_id=fid,
                original_title=r[1],
                first_release_date=r[2],
                poster_url=r[3],
            )
        if r[4]:
            film_map[fid].characters.append(r[4])

    # Sort by date descending
    filmography = sorted(
        film_map.values(),
        key=lambda e: e.first_release_date or "0000-00-00",
        reverse=True,
    )

    return PersonDetail(
        person_id=person["person_id"],
        firstname=person["firstname"],
        lastname=person["lastname"],
        gender=person["gender"],
        date_of_birth=person["date_of_birth"],
        date_of_death=person["date_of_death"],
        nationality=person["nationality"],
        tmdb_id=person["tmdb_id"],
        photo_url=person["photo_url"],
        filmography=filmography,
    )
