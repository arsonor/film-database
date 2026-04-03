"""
Taxonomy API endpoints — list, add, rename, merge, delete taxonomy values.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.auth import require_admin
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.schemas.taxonomy import (
    TaxonomyCreate,
    TaxonomyItem,
    TaxonomyList,
    TaxonomyMerge,
    TaxonomyRename,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["taxonomy"])

# Mapping: dimension name → (lookup_table, id_column, name_column, junction_table, junction_fk)
DIMENSION_MAP = {
    "categories": ("category", "category_id", "category_name", "film_genre", "category_id"),
    "cinema_types": ("cinema_type", "cinema_type_id", "technique_name", "film_technique", "cinema_type_id"),
    "themes": ("theme_context", "theme_context_id", "theme_name", "film_theme", "theme_context_id"),
    "characters": ("character_context", "character_context_id", "context_name", "film_character_context", "character_context_id"),
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
SORTED_DIMENSIONS = {
    "themes", "time_periods", "characters", "cinema_types",
    "atmospheres", "motivations", "place_contexts", "messages", "categories",
}

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
            ORDER BY lt.sort_order, lt.category_name, lt.historic_subcategory_name NULLS FIRST
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


# Dimensions that can be managed (excludes studios, streaming, person_jobs, languages)
MANAGEABLE_DIMENSIONS = {
    "categories", "cinema_types", "themes", "characters",
    "atmospheres", "messages", "motivations", "time_periods", "place_contexts",
}


def _validate_manageable(dimension: str):
    if dimension not in MANAGEABLE_DIMENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Dimension '{dimension}' is not manageable. Valid: {', '.join(sorted(MANAGEABLE_DIMENSIONS))}",
        )


# =============================================================================
# POST /api/taxonomy/{dimension} — Add a new value
# =============================================================================


@router.post("/taxonomy/{dimension}", response_model=TaxonomyItem, status_code=201)
async def add_taxonomy_value(
    dimension: str,
    body: TaxonomyCreate,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    _validate_manageable(dimension)
    lookup_table, id_col, name_col, _, _ = DIMENSION_MAP[dimension]

    # Categories: special handling for "Historical: biopic" format
    if dimension == "categories":
        if ": " in body.name:
            cat_name, sub_name = body.name.split(": ", 1)
        else:
            cat_name, sub_name = body.name, None

        try:
            result = await db.execute(
                text("""
                    INSERT INTO category (category_name, historic_subcategory_name)
                    VALUES (:cat, :sub)
                    RETURNING category_id
                """),
                {"cat": cat_name, "sub": sub_name},
            )
            new_id = result.scalar_one()
            await db.commit()
            return TaxonomyItem(id=new_id, name=body.name, film_count=0)
        except Exception as e:
            await db.rollback()
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                raise HTTPException(status_code=409, detail=f"Value '{body.name}' already exists")
            raise

    # Generic dimensions
    has_sort = dimension in SORTED_DIMENSIONS
    if has_sort:
        sort_val = body.sort_order
        if sort_val is None:
            # Auto-assign: max + 1
            r = await db.execute(text(f"SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {lookup_table}"))
            sort_val = r.scalar_one()
        sql = f"INSERT INTO {lookup_table} ({name_col}, sort_order) VALUES (:name, :sort) RETURNING {id_col}"
        params = {"name": body.name, "sort": sort_val}
    else:
        sql = f"INSERT INTO {lookup_table} ({name_col}) VALUES (:name) RETURNING {id_col}"
        params = {"name": body.name}

    try:
        result = await db.execute(text(sql), params)
        new_id = result.scalar_one()
        await db.commit()
        return TaxonomyItem(id=new_id, name=body.name, film_count=0, sort_order=sort_val if has_sort else None)
    except Exception as e:
        await db.rollback()
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail=f"Value '{body.name}' already exists")
        raise


# =============================================================================
# PUT /api/taxonomy/{dimension}/{item_id} — Rename a value
# =============================================================================


@router.put("/taxonomy/{dimension}/{item_id}", response_model=TaxonomyItem)
async def rename_taxonomy_value(
    dimension: str,
    item_id: int,
    body: TaxonomyRename,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    _validate_manageable(dimension)
    lookup_table, id_col, name_col, _, _ = DIMENSION_MAP[dimension]

    if dimension == "categories":
        if ": " in body.name:
            cat_name, sub_name = body.name.split(": ", 1)
        else:
            cat_name, sub_name = body.name, None

        result = await db.execute(
            text("""
                UPDATE category SET category_name = :cat, historic_subcategory_name = :sub
                WHERE category_id = :id RETURNING category_id
            """),
            {"cat": cat_name, "sub": sub_name, "id": item_id},
        )
    else:
        set_parts = [f"{name_col} = :name"]
        params: dict = {"name": body.name, "id": item_id}
        if dimension in SORTED_DIMENSIONS and body.sort_order is not None:
            set_parts.append("sort_order = :sort")
            params["sort"] = body.sort_order
        result = await db.execute(
            text(f"UPDATE {lookup_table} SET {', '.join(set_parts)} WHERE {id_col} = :id RETURNING {id_col}"),
            params,
        )

    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Value not found")
    await db.commit()
    return TaxonomyItem(id=item_id, name=body.name)


# =============================================================================
# POST /api/taxonomy/{dimension}/merge — Merge source into target
# =============================================================================


@router.post("/taxonomy/{dimension}/merge")
async def merge_taxonomy_values(
    dimension: str,
    body: TaxonomyMerge,
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    _validate_manageable(dimension)
    if body.source_id == body.target_id:
        raise HTTPException(status_code=400, detail="Source and target must be different")

    lookup_table, id_col, name_col, junc_table, junc_fk = DIMENSION_MAP[dimension]

    if not junc_table:
        raise HTTPException(status_code=400, detail="This dimension has no junction table")

    # Verify both exist
    for check_id, label in [(body.source_id, "Source"), (body.target_id, "Target")]:
        r = await db.execute(text(f"SELECT {id_col} FROM {lookup_table} WHERE {id_col} = :id"), {"id": check_id})
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"{label} value not found")

    # Count films that will be affected
    r = await db.execute(
        text(f"SELECT COUNT(*) FROM {junc_table} WHERE {junc_fk} = :sid"),
        {"sid": body.source_id},
    )
    films_affected = r.scalar_one()

    # Step 1: Move source rows to target (skip duplicates)
    await db.execute(
        text(f"""
            INSERT INTO {junc_table} (film_id, {junc_fk})
            SELECT film_id, :tid FROM {junc_table} WHERE {junc_fk} = :sid
            ON CONFLICT DO NOTHING
        """),
        {"tid": body.target_id, "sid": body.source_id},
    )

    # Step 2: Delete all source junction rows
    await db.execute(
        text(f"DELETE FROM {junc_table} WHERE {junc_fk} = :sid"),
        {"sid": body.source_id},
    )

    # Step 3: Delete source lookup row
    await db.execute(
        text(f"DELETE FROM {lookup_table} WHERE {id_col} = :sid"),
        {"sid": body.source_id},
    )

    await db.commit()
    logger.info("Merged %s #%d into #%d (%d films affected)", dimension, body.source_id, body.target_id, films_affected)
    return {"merged": True, "films_affected": films_affected}


# =============================================================================
# DELETE /api/taxonomy/{dimension}/{item_id} — Delete a value
# =============================================================================


@router.delete("/taxonomy/{dimension}/{item_id}", status_code=200)
async def delete_taxonomy_value(
    dimension: str,
    item_id: int,
    force: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin: None = Depends(require_admin),
):
    _validate_manageable(dimension)
    lookup_table, id_col, name_col, junc_table, junc_fk = DIMENSION_MAP[dimension]

    # Check existence
    r = await db.execute(text(f"SELECT {id_col} FROM {lookup_table} WHERE {id_col} = :id"), {"id": item_id})
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Value not found")

    # Check film count
    film_count = 0
    if junc_table:
        r = await db.execute(
            text(f"SELECT COUNT(*) FROM {junc_table} WHERE {junc_fk} = :id"),
            {"id": item_id},
        )
        film_count = r.scalar_one()

    if film_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Value is used by {film_count} films. Use ?force=true to delete anyway.",
        )

    # Delete junction rows first if force
    if junc_table and film_count > 0:
        await db.execute(
            text(f"DELETE FROM {junc_table} WHERE {junc_fk} = :id"),
            {"id": item_id},
        )

    await db.execute(
        text(f"DELETE FROM {lookup_table} WHERE {id_col} = :id"),
        {"id": item_id},
    )
    await db.commit()
    return {"deleted": True, "films_affected": film_count}
