"""
Geography API endpoints — search locations, list countries.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.geography import CountryItem, GeographySearchResult

router = APIRouter(tags=["geography"])


@router.get("/geography/search", response_model=list[GeographySearchResult])
async def search_geography(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search across all geography levels (continent, country, state_city).
    Returns matching locations with film counts, ordered by film_count DESC.
    """
    result = await db.execute(
        text("""
            SELECT g.geography_id, g.continent, g.country, g.state_city,
                   COUNT(DISTINCT fsp.film_id) AS film_count
            FROM geography g
            LEFT JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
            WHERE g.continent ILIKE :q
               OR g.country ILIKE :q
               OR g.state_city ILIKE :q
            GROUP BY g.geography_id, g.continent, g.country, g.state_city
            ORDER BY film_count DESC, g.country, g.state_city
            LIMIT :limit
        """),
        {"q": f"%{q}%", "limit": limit},
    )

    items = []
    for r in result.fetchall():
        # Build a readable label: "state_city, country, continent"
        parts = [p for p in (r[3], r[2], r[1]) if p]
        label = ", ".join(parts) if parts else "Unknown"
        items.append(
            GeographySearchResult(
                geography_id=r[0],
                label=label,
                film_count=r[4],
                continent=r[1],
                country=r[2],
                state_city=r[3],
            )
        )

    return items


@router.get("/geography/countries", response_model=list[CountryItem])
async def list_countries(db: AsyncSession = Depends(get_db)):
    """
    List all distinct countries with film counts, sorted by count DESC.
    Useful for a quick filter dropdown.
    """
    result = await db.execute(
        text("""
            SELECT g.country, COUNT(DISTINCT fsp.film_id) AS film_count
            FROM geography g
            JOIN film_set_place fsp ON g.geography_id = fsp.geography_id
            WHERE g.country IS NOT NULL
            GROUP BY g.country
            ORDER BY film_count DESC, g.country
        """)
    )
    return [
        CountryItem(country=r[0], film_count=r[1])
        for r in result.fetchall()
    ]
