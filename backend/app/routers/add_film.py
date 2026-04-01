"""
Add Film workflow endpoints — Search TMDB, Enrich with Claude, Save to DB.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.auth import require_admin
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.add_film import (
    EnrichmentPreview,
    EnrichRequest,
    TMDBSearchResponse,
    TMDBSearchResult,
)
from backend.app.services.claude_enricher import ClaudeEnricher
from backend.app.services.tmdb_mapper import TMDBMapper
from backend.app.services.tmdb_service import TMDBService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["add-film"])

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# =============================================================================
# GET /api/add-film/search — Search TMDB for candidates
# =============================================================================


@router.get("/add-film/search", response_model=TMDBSearchResponse)
async def search_tmdb(
    title: str = Query(..., min_length=1),
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")

    async with TMDBService(TMDB_API_KEY) as tmdb:
        # Search in both locales and deduplicate
        results_fr = await tmdb.search_film(title, year=year, language="fr-FR")
        results_en = await tmdb.search_film(title, year=year, language="en-US")

        seen_ids: set[int] = set()
        candidates: list[dict] = []
        for r in results_fr + results_en:
            if r["tmdb_id"] not in seen_ids:
                seen_ids.add(r["tmdb_id"])
                candidates.append(r)

    # Check which tmdb_ids already exist in DB
    if candidates:
        tmdb_ids = [c["tmdb_id"] for c in candidates]
        result = await db.execute(
            text("SELECT tmdb_id FROM film WHERE tmdb_id = ANY(:ids)"),
            {"ids": tmdb_ids},
        )
        existing_ids = {row[0] for row in result.fetchall()}
    else:
        existing_ids = set()

    # Build response
    results = []
    for c in candidates[:20]:  # Limit to 20 results
        poster_url = None
        if c.get("poster_path"):
            poster_url = f"https://image.tmdb.org/t/p/w342{c['poster_path']}"

        results.append(
            TMDBSearchResult(
                tmdb_id=c["tmdb_id"],
                title=c.get("title", ""),
                original_title=c.get("original_title", ""),
                release_date=c.get("release_date") or None,
                overview=c.get("overview") or None,
                poster_url=poster_url,
                already_in_db=c["tmdb_id"] in existing_ids,
            )
        )

    return TMDBSearchResponse(results=results)


# =============================================================================
# POST /api/add-film/enrich — Fetch TMDB details + Claude enrichment
# =============================================================================


@router.post("/add-film/enrich", response_model=EnrichmentPreview)
async def enrich_film(
    request: EnrichRequest,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    tmdb_id = request.tmdb_id

    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")

    # Check if film already exists
    result = await db.execute(
        text("SELECT film_id FROM film WHERE tmdb_id = :tmdb_id"),
        {"tmdb_id": tmdb_id},
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Film with tmdb_id={tmdb_id} already exists")

    # Step 1: Fetch full TMDB data
    async with TMDBService(TMDB_API_KEY) as tmdb:
        tmdb_data = await tmdb.get_film_details(tmdb_id)
        fr_data = await tmdb.get_film_details_fr(tmdb_id)
        watch_providers = await tmdb.get_watch_providers(tmdb_id)

        # Step 2: Map to DB structure
        mapper = TMDBMapper(tmdb)
        mapped = await mapper.map_film_to_db(tmdb_data, fr_data)
        streaming_platforms = mapper.map_watch_providers(watch_providers)

    mapped["streaming_platforms"] = streaming_platforms

    # Step 3: Claude enrichment
    enrichment_failed = False
    enrichment = {}

    if ANTHROPIC_API_KEY:
        try:
            enricher = ClaudeEnricher(ANTHROPIC_API_KEY)
            enrichment = await enricher.enrich_film(mapped)
            logger.info("Claude enrichment succeeded for tmdb_id=%d", tmdb_id)
        except Exception as e:
            logger.error("Claude enrichment failed for tmdb_id=%d: %s", tmdb_id, e)
            enrichment_failed = True
    else:
        logger.warning("ANTHROPIC_API_KEY not set, skipping enrichment")
        enrichment_failed = True

    # Merge Claude categories/subcategories with TMDB ones (Claude has priority when available)
    if enrichment.get("categories"):
        merged_categories = enrichment["categories"]
    else:
        merged_categories = mapped.get("categories", [])

    if enrichment.get("historic_subcategories"):
        merged_subcategories = enrichment["historic_subcategories"]
    else:
        merged_subcategories = mapped.get("historic_subcategories", [])

    # Convert date objects to strings for JSON serialization
    film_data = mapped["film"]
    if film_data.get("first_release_date"):
        film_data["first_release_date"] = str(film_data["first_release_date"])

    return EnrichmentPreview(
        film=film_data,
        titles=mapped.get("titles", []),
        categories=merged_categories,
        historic_subcategories=merged_subcategories,
        crew=mapped.get("crew", []),
        cast=mapped.get("cast", []),
        studios=mapped.get("studios", []),
        streaming_platforms=streaming_platforms,
        enrichment=enrichment,
        keywords=mapped.get("keywords", []),
        production_countries=mapped.get("production_countries", []),
        languages=mapped.get("languages", []),
        enrichment_failed=enrichment_failed,
    )
