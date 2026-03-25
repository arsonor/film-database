"""
Pydantic schemas for geography API responses.
"""

from pydantic import BaseModel


class GeographySearchResult(BaseModel):
    geography_id: int
    label: str
    film_count: int
    continent: str | None = None
    country: str | None = None
    state_city: str | None = None


class CountryItem(BaseModel):
    country: str
    film_count: int
