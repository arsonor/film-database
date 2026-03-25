"""
Pydantic schemas for taxonomy API responses.
"""

from pydantic import BaseModel


class TaxonomyItem(BaseModel):
    id: int
    name: str
    film_count: int | None = None
    sort_order: int | None = None


class TaxonomyList(BaseModel):
    dimension: str
    items: list[TaxonomyItem]
