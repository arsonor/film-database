"""
Tag review service — batch-review a taxonomy tag across all films using Claude.

Yields progress events as an async generator for SSE streaming.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import AsyncGenerator

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "data"

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
}

MODEL_ALIASES = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6-20250514",
}


def results_file_path(dimension: str, tag: str) -> Path:
    return RESULTS_DIR / f"review_{dimension}_{tag}.json"


def save_progress(path: Path, results: dict[int, bool]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({str(k): v for k, v in results.items()}, indent=2))


def load_progress(path: Path) -> dict[int, bool]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {int(k): v for k, v in data.items()}


def build_batch_prompt(films: list[dict], tag: str, description: str) -> str:
    film_lines = []
    for f in films:
        year_str = f"({f['year']})" if f.get("year") else ""
        summary = (f.get("summary") or "No summary available.")[:300]
        film_lines.append(f"[{f['film_id']}] {f['original_title']} {year_str} — {summary}")
    films_block = "\n".join(film_lines)
    return (
        f'Review each film below and decide whether it should be tagged as "{tag}".\n'
        f"Definition: {description}\n\n"
        "For each film, respond with ONLY its ID and YES or NO. One per line, format: ID:YES or ID:NO\n"
        "Do not add explanations. Do not skip any film.\n\n"
        f"Films:\n{films_block}"
    )


def parse_response(text: str) -> dict[int, bool]:
    results = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        line = line.replace("[", "").replace("]", "")
        for sep in [":", "-", " "]:
            if sep in line:
                parts = line.split(sep, 1)
                try:
                    film_id = int(parts[0].strip())
                    answer = parts[1].strip().upper()
                    if answer.startswith("YES"):
                        results[film_id] = True
                    elif answer.startswith("NO"):
                        results[film_id] = False
                    break
                except (ValueError, IndexError):
                    continue
    return results


def compute_changes(
    all_films: list[dict],
    all_results: dict[int, bool],
    currently_tagged: set[int],
) -> tuple[list[int], list[int]]:
    to_add, to_remove = [], []
    for film in all_films:
        fid = film["film_id"]
        should_have = all_results.get(fid)
        if should_have is None:
            continue
        has_tag = fid in currently_tagged
        if should_have and not has_tag:
            to_add.append(fid)
        elif not should_have and has_tag:
            to_remove.append(fid)
    return to_add, to_remove


async def fetch_all_films(db: AsyncSession) -> list[dict]:
    r = await db.execute(text(
        "SELECT film_id, original_title, "
        "EXTRACT(YEAR FROM first_release_date)::int AS year, "
        "summary FROM film ORDER BY film_id"
    ))
    return [{"film_id": row[0], "original_title": row[1], "year": row[2], "summary": row[3]} for row in r.fetchall()]


async def fetch_tagged_film_ids(db: AsyncSession, dimension: str, tag: str) -> set[int]:
    lookup, id_col, name_col, junc, junc_fk = DIMENSION_MAP[dimension]
    r = await db.execute(
        text(f"SELECT jt.film_id FROM {junc} jt JOIN {lookup} lt ON jt.{junc_fk} = lt.{id_col} WHERE lt.{name_col} = :tag"),
        {"tag": tag},
    )
    return {row[0] for row in r.fetchall()}


async def fetch_tag_id(db: AsyncSession, dimension: str, tag: str) -> int | None:
    lookup, id_col, name_col, _, _ = DIMENSION_MAP[dimension]
    r = await db.execute(text(f"SELECT {id_col} FROM {lookup} WHERE {name_col} = :tag"), {"tag": tag})
    row = r.fetchone()
    return row[0] if row else None


async def apply_changes_db(
    db: AsyncSession,
    dimension: str,
    tag_id: int,
    to_add: list[int],
    to_remove: list[int],
):
    _, _, _, junc, junc_fk = DIMENSION_MAP[dimension]
    if to_add:
        for fid in to_add:
            await db.execute(
                text(f"INSERT INTO {junc} (film_id, {junc_fk}) VALUES (:fid, :tid) ON CONFLICT DO NOTHING"),
                {"fid": fid, "tid": tag_id},
            )
    if to_remove:
        await db.execute(
            text(f"DELETE FROM {junc} WHERE {junc_fk} = :tid AND film_id = ANY(:fids)"),
            {"tid": tag_id, "fids": to_remove},
        )
    await db.commit()


async def run_review(
    db: AsyncSession,
    dimension: str,
    tag: str,
    description: str,
    model_alias: str,
    batch_size: int = 10,
) -> AsyncGenerator[dict, None]:
    """Async generator yielding progress and result events for SSE."""

    if dimension not in DIMENSION_MAP:
        yield {"type": "error", "message": f"Unknown dimension: {dimension}"}
        return

    model = MODEL_ALIASES.get(model_alias, model_alias)

    tag_id = await fetch_tag_id(db, dimension, tag)
    if tag_id is None:
        yield {"type": "error", "message": f"Tag '{tag}' not found in dimension '{dimension}'"}
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield {"type": "error", "message": "ANTHROPIC_API_KEY not configured on server"}
        return

    client = anthropic.AsyncAnthropic(api_key=api_key)

    all_films = await fetch_all_films(db)
    currently_tagged = await fetch_tagged_film_ids(db, dimension, tag)

    total_films = len(all_films)
    all_results: dict[int, bool] = {}
    total_input = 0
    total_output = 0
    results_path = results_file_path(dimension, tag)

    # Resume from previous progress if exists
    if results_path.exists():
        all_results = load_progress(results_path)
        logger.info("Resuming review with %d previously reviewed films", len(all_results))

    films_to_review = [f for f in all_films if f["film_id"] not in all_results]
    total_to_review = len(films_to_review)
    total_batches = (total_to_review + batch_size - 1) // batch_size

    yield {
        "type": "started",
        "total_films": total_to_review,
        "total_batches": total_batches,
        "currently_tagged": len(currently_tagged),
        "resumed_from": len(all_results),
    }

    for i in range(0, total_to_review, batch_size):
        batch = films_to_review[i : i + batch_size]
        batch_num = i // batch_size + 1
        prompt = build_batch_prompt(batch, tag, description)

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            results = parse_response(response.content[0].text)
            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens
            all_results.update(results)
        except anthropic.RateLimitError:
            await asyncio.sleep(30)
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                results = parse_response(response.content[0].text)
                total_input += response.usage.input_tokens
                total_output += response.usage.output_tokens
                all_results.update(results)
            except Exception as e:
                logger.error("Retry failed for batch %d: %s", batch_num, e)
        except Exception as e:
            logger.error("Batch %d failed: %s", batch_num, e)

        save_progress(results_path, all_results)

        yield {
            "type": "progress",
            "batch": batch_num,
            "total_batches": total_batches,
            "films_reviewed": min(i + batch_size, total_to_review),
            "total_films": total_to_review,
            "input_tokens": total_input,
            "output_tokens": total_output,
        }

        await asyncio.sleep(0.5)

    to_add, to_remove = compute_changes(all_films, all_results, currently_tagged)
    films_by_id = {f["film_id"]: f for f in all_films}

    if "haiku" in model:
        cost = total_input * 0.80 / 1_000_000 + total_output * 4.0 / 1_000_000
    elif "sonnet" in model:
        cost = total_input * 3.0 / 1_000_000 + total_output * 15.0 / 1_000_000
    else:
        cost = total_input * 15.0 / 1_000_000 + total_output * 75.0 / 1_000_000

    yield {
        "type": "result",
        "total_reviewed": len(all_results),
        "currently_tagged": len(currently_tagged),
        "should_be_tagged": sum(1 for v in all_results.values() if v),
        "to_add": [
            {"film_id": fid, "title": films_by_id[fid]["original_title"], "year": films_by_id[fid].get("year")}
            for fid in to_add if fid in films_by_id
        ],
        "to_remove": [
            {"film_id": fid, "title": films_by_id[fid]["original_title"], "year": films_by_id[fid].get("year")}
            for fid in to_remove if fid in films_by_id
        ],
        "input_tokens": total_input,
        "output_tokens": total_output,
        "estimated_cost": round(cost, 2),
    }
