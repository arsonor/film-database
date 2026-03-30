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


class TaxonomyCreate(BaseModel):
    name: str
    sort_order: int | None = None


class TaxonomyRename(BaseModel):
    name: str
    sort_order: int | None = None


class TaxonomyMerge(BaseModel):
    source_id: int
    target_id: int
