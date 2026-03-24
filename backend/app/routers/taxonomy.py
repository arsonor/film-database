"""
Taxonomy API endpoints — list all values for any taxonomy dimension.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.taxonomy import TaxonomyItem, TaxonomyList

router = APIRouter(tags=["taxonomy"])

# Mapping: dimension name → (lookup_table, id_column, name_column, junction_table, junction_fk)
DIMENSION_MAP = {
    "categories": ("category", "category_id", "category_name", "film_genre", "category_id"),
    "cinema_types": ("cinema_type", "cinema_type_id", "technique_name", "film_technique", "cinema_type_id"),
    "cultural_movements": ("cultural_movement", "movement_id", "movement_name", "film_movement", "movement_id"),
    "themes": ("theme_context", "theme_context_id", "theme_name", "film_theme", "theme_context_id"),
    "characters": ("characters_type", "character_type_id", "type_name", "film_characters", "character_type_id"),
    "character_contexts": ("character_context", "character_context_id", "context_name", "film_character_context", "character_context_id"),
    "atmospheres": ("atmosphere", "atmosphere_id", "atmosphere_name", "film_atmosphere", "atmosphere_id"),
    "messages": ("message_conveyed", "message_id", "message_name", "film_message", "message_id"),
    "motivations": ("motivation_relation", "motivation_id", "motivation_name", "film_motivation", "motivation_id"),
    "time_periods": ("time_context", "time_context_id", "time_period", "film_period", "time_context_id"),
    "place_contexts": ("place_context", "place_context_id", "environment", "film_place", "place_context_id"),
    "streaming_platforms": ("stream_platform", "platform_id", "platform_name", "film_exploitation", "platform_id"),
    "person_jobs": ("person_job", "job_id", "role_name", None, None),
}

# Dimensions that use hierarchical naming with "parent: sub" convention
HIERARCHICAL_DIMENSIONS = {"themes"}


@router.get("/taxonomy/{dimension}", response_model=TaxonomyList)
async def get_taxonomy(dimension: str, db: AsyncSession = Depends(get_db)):
    if dimension not in DIMENSION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dimension: '{dimension}'. Valid: {', '.join(sorted(DIMENSION_MAP.keys()))}",
        )

    lookup_table, id_col, name_col, junc_table, junc_fk = DIMENSION_MAP[dimension]

    # Special handling for categories: filter out subcategory rows for cleaner output
    extra_where = ""
    if dimension == "categories":
        extra_where = "WHERE lt.historic_subcategory_name IS NULL"

    if junc_table:
        sql = f"""
            SELECT lt.{id_col}, lt.{name_col},
                   COUNT(jt.film_id) AS film_count
            FROM {lookup_table} lt
            LEFT JOIN {junc_table} jt ON lt.{id_col} = jt.{junc_fk}
            {extra_where}
            GROUP BY lt.{id_col}, lt.{name_col}
            ORDER BY lt.{name_col}
        """
    else:
        sql = f"""
            SELECT lt.{id_col}, lt.{name_col}, 0 AS film_count
            FROM {lookup_table} lt
            ORDER BY lt.{name_col}
        """

    result = await db.execute(text(sql))
    items = [
        TaxonomyItem(id=row[0], name=row[1], film_count=row[2])
        for row in result.fetchall()
    ]

    # For hierarchical dimensions, aggregate sub-item counts into parent items.
    # Convention: sub-items use "parent: sub" naming (e.g. "art: cinema", "sport: motor").
    # Parent items (e.g. "art") get the sum of all their sub-item counts added
    # to their own direct count, so they reflect total usage across the group.
    if dimension in HIERARCHICAL_DIMENSIONS:
        # Collect sub-item counts per parent prefix
        parent_extra: dict[str, int] = {}
        for item in items:
            if ": " in item.name:
                parent = item.name.split(": ", 1)[0]
                parent_extra[parent] = parent_extra.get(parent, 0) + (item.film_count or 0)

        # Add aggregated sub-counts to matching parent items
        for item in items:
            if ": " not in item.name and item.name in parent_extra:
                item.film_count = (item.film_count or 0) + parent_extra[item.name]

    return TaxonomyList(dimension=dimension, items=items)
