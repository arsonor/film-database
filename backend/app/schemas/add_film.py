"""
Pydantic schemas for the Add Film workflow (TMDB search + Claude enrichment).
"""

from pydantic import BaseModel


class TMDBSearchResult(BaseModel):
    tmdb_id: int
    title: str
    original_title: str
    release_date: str | None = None
    overview: str | None = None
    poster_url: str | None = None
    already_in_db: bool = False


class TMDBSearchResponse(BaseModel):
    results: list[TMDBSearchResult]


class EnrichRequest(BaseModel):
    tmdb_id: int


class EnrichmentPreview(BaseModel):
    """Full preview of what will be saved — matches FilmCreate structure."""
    film: dict
    titles: list[dict] = []
    categories: list[str] = []
    historic_subcategories: list[str] = []
    crew: list[dict] = []
    cast: list[dict] = []
    studios: list[dict] = []
    streaming_platforms: list[str] = []
    enrichment: dict = {}
    keywords: list[str] = []
    production_countries: list[str] = []
    languages: list[dict] = []
    enrichment_failed: bool = False
