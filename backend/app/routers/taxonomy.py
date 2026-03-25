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
    "studios": ("studio", "studio_id", "studio_name", "production", "studio_id"),
    "person_jobs": ("person_job", "job_id", "role_name", None, None),
}

# Dimensions that use hierarchical naming with "parent: sub" convention
HIERARCHICAL_DIMENSIONS = {"themes", "categories"}

# Dimensions with sort_order columns for custom display ordering
SORTED_DIMENSIONS = {"themes", "time_periods"}

# Special dimensions not in DIMENSION_MAP
SPECIAL_DIMENSIONS = {"languages"}
ALL_DIMENSIONS = set(DIMENSION_MAP.keys()) | SPECIAL_DIMENSIONS


@router.get("/taxonomy/{dimension}", response_model=TaxonomyList)
async def get_taxonomy(dimension: str, db: AsyncSession = Depends(get_db)):
    if dimension not in ALL_DIMENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dimension: '{dimension}'. Valid: {', '.join(sorted(ALL_DIMENSIONS))}",
        )

    # Special handling for languages: count films where this is the original language
    if dimension == "languages":
        result = await db.execute(text("""
            SELECT l.language_id, l.language_name,
                   COUNT(DISTINCT fl.film_id) AS film_count
            FROM language l
            LEFT JOIN film_language fl ON l.language_id = fl.language_id AND fl.is_original = TRUE
            GROUP BY l.language_id, l.language_name
            ORDER BY film_count DESC, l.language_name
        """))
        items = [
            TaxonomyItem(id=row[0], name=row[1], film_count=row[2])
            for row in result.fetchall()
        ]
        return TaxonomyList(dimension=dimension, items=items)

    # Special handling for categories: show subcategories with "parent: sub" display
    if dimension == "categories":
        result = await db.execute(text("""
            SELECT lt.category_id,
                   CASE
                       WHEN lt.historic_subcategory_name IS NOT NULL
                       THEN lt.category_name || ': ' || lt.historic_subcategory_name
                       ELSE lt.category_name
                   END AS display_name,
                   COUNT(jt.film_id) AS film_count
            FROM category lt
            LEFT JOIN film_genre jt ON lt.category_id = jt.category_id
            GROUP BY lt.category_id, lt.category_name, lt.historic_subcategory_name
            ORDER BY lt.category_name, lt.historic_subcategory_name NULLS FIRST
        """))
        items = [
            TaxonomyItem(id=row[0], name=row[1], film_count=row[2])
            for row in result.fetchall()
        ]
        # Hierarchical aggregation for categories
        _aggregate_hierarchical(items)
        return TaxonomyList(dimension=dimension, items=items)

    lookup_table, id_col, name_col, junc_table, junc_fk = DIMENSION_MAP[dimension]

    # Build ORDER BY based on whether dimension has sort_order
    has_sort_order = dimension in SORTED_DIMENSIONS
    if has_sort_order:
        order_by = f"lt.sort_order, lt.{name_col}"
    else:
        order_by = f"lt.{name_col}"

    # Build select columns
    sort_order_col = ", lt.sort_order" if has_sort_order else ", NULL AS sort_order"

    if junc_table:
        sql = f"""
            SELECT lt.{id_col}, lt.{name_col},
                   COUNT(jt.film_id) AS film_count
                   {sort_order_col}
            FROM {lookup_table} lt
            LEFT JOIN {junc_table} jt ON lt.{id_col} = jt.{junc_fk}
            GROUP BY lt.{id_col}, lt.{name_col}{', lt.sort_order' if has_sort_order else ''}
            ORDER BY {order_by}
        """
    else:
        sql = f"""
            SELECT lt.{id_col}, lt.{name_col}, 0 AS film_count
                   {sort_order_col}
            FROM {lookup_table} lt
            ORDER BY {order_by}
        """

    result = await db.execute(text(sql))
    items = [
        TaxonomyItem(id=row[0], name=row[1], film_count=row[2], sort_order=row[3])
        for row in result.fetchall()
    ]

    # For hierarchical dimensions, aggregate sub-item counts into parent items.
    if dimension in HIERARCHICAL_DIMENSIONS:
        _aggregate_hierarchical(items)

    return TaxonomyList(dimension=dimension, items=items)


def _aggregate_hierarchical(items: list[TaxonomyItem]) -> None:
    """Aggregate sub-item counts into parent items for hierarchical naming."""
    parent_extra: dict[str, int] = {}
    for item in items:
        if ": " in item.name:
            parent = item.name.split(": ", 1)[0]
            parent_extra[parent] = parent_extra.get(parent, 0) + (item.film_count or 0)

    for item in items:
        if ": " not in item.name and item.name in parent_extra:
            item.film_count = (item.film_count or 0) + parent_extra[item.name]
