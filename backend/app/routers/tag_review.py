"""
Tag review API — SSE-streamed batch review + apply endpoint.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth import require_admin
from backend.app.database import get_db
from backend.app.services.tag_reviewer import (
    DIMENSION_MAP,
    apply_changes_db,
    compute_changes,
    fetch_all_films,
    fetch_tag_id,
    fetch_tagged_film_ids,
    load_progress,
    results_file_path,
    run_review,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tag-review"])


@router.get("/tag-review/run")
async def run_tag_review(
    dimension: str = Query(...),
    tag: str = Query(...),
    description: str = Query(""),
    model: str = Query("haiku"),
    batch_size: int = Query(10, ge=1, le=50),
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if dimension not in DIMENSION_MAP:
        raise HTTPException(400, f"Unknown dimension: {dimension}")

    desc = description or f"films that should be classified as '{tag}'"

    async def event_stream():
        try:
            async for event in run_review(db, dimension, tag, desc, model, batch_size):
                event_type = event.pop("type")
                yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.exception("Tag review stream error")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class ApplyRequest(BaseModel):
    dimension: str
    tag: str


@router.post("/tag-review/apply")
async def apply_tag_review(
    body: ApplyRequest,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.dimension not in DIMENSION_MAP:
        raise HTTPException(400, f"Unknown dimension: {body.dimension}")

    path = results_file_path(body.dimension, body.tag)
    if not path.exists():
        raise HTTPException(404, f"No review results found for '{body.tag}' in '{body.dimension}'")

    tag_id = await fetch_tag_id(db, body.dimension, body.tag)
    if tag_id is None:
        raise HTTPException(404, f"Tag '{body.tag}' not found in dimension '{body.dimension}'")

    all_results = load_progress(path)
    all_films = await fetch_all_films(db)
    currently_tagged = await fetch_tagged_film_ids(db, body.dimension, body.tag)
    to_add, to_remove = compute_changes(all_films, all_results, currently_tagged)

    if to_add or to_remove:
        await apply_changes_db(db, body.dimension, tag_id, to_add, to_remove)

    path.unlink(missing_ok=True)

    return {"added": len(to_add), "removed": len(to_remove)}
