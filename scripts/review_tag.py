"""
Review a taxonomy tag across all films using Claude Haiku.

For each film in the database, asks Claude whether the tag applies,
then reports which films should be added/removed.

Usage:
  # Dry-run (default): show proposed changes
  python scripts/review_tag.py --dimension atmospheres --tag steamy

  # Apply changes to the database
  python scripts/review_tag.py --dimension atmospheres --tag steamy --apply

  # Use a different model
  python scripts/review_tag.py --dimension atmospheres --tag steamy --model claude-sonnet-4-5-20241022

  # Adjust batch size (films per API call)
  python scripts/review_tag.py --dimension atmospheres --tag steamy --batch-size 15

  # Resume from a previous run (skip already-reviewed films)
  python scripts/review_tag.py --dimension atmospheres --tag steamy --resume
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import anthropic
import asyncpg
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Dimension → (lookup_table, id_col, name_col, junction_table, junction_fk)
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

# Tag descriptions for ambiguous tags — helps Claude understand the intent
TAG_DESCRIPTIONS = {
    "steamy": "films with strong sensuality, eroticism, or sexually explicit scenes",
}


def get_tag_description(tag: str) -> str:
    if tag in TAG_DESCRIPTIONS:
        return TAG_DESCRIPTIONS[tag]
    return f"films that should be classified as '{tag}'"


async def fetch_all_films(pool: asyncpg.Pool) -> list[dict]:
    """Fetch all films with basic info."""
    rows = await pool.fetch("""
        SELECT f.film_id, f.original_title,
               EXTRACT(YEAR FROM f.first_release_date)::int AS year,
               f.summary
        FROM film f
        ORDER BY f.film_id
    """)
    return [dict(r) for r in rows]


async def fetch_tagged_film_ids(pool: asyncpg.Pool, dimension: str, tag: str) -> set[int]:
    """Fetch film IDs currently tagged with the given tag."""
    lookup_table, id_col, name_col, junc_table, junc_fk = DIMENSION_MAP[dimension]
    rows = await pool.fetch(f"""
        SELECT jt.film_id
        FROM {junc_table} jt
        JOIN {lookup_table} lt ON jt.{junc_fk} = lt.{id_col}
        WHERE lt.{name_col} = $1
    """, tag)
    return {r["film_id"] for r in rows}


async def fetch_tag_id(pool: asyncpg.Pool, dimension: str, tag: str) -> int | None:
    """Get the lookup table ID for the tag."""
    lookup_table, id_col, name_col, _, _ = DIMENSION_MAP[dimension]
    row = await pool.fetchrow(
        f"SELECT {id_col} FROM {lookup_table} WHERE {name_col} = $1", tag
    )
    return row[id_col] if row else None


def build_batch_prompt(films: list[dict], tag: str, description: str) -> str:
    """Build a prompt asking Claude to review a batch of films for a tag."""
    film_lines = []
    for f in films:
        year_str = f"({f['year']})" if f.get("year") else ""
        summary = (f.get("summary") or "No summary available.")[:300]
        film_lines.append(f"[{f['film_id']}] {f['original_title']} {year_str} — {summary}")

    films_block = "\n".join(film_lines)

    return f"""Review each film below and decide whether it should be tagged as "{tag}".
Definition: {description}

For each film, respond with ONLY its ID and YES or NO. One per line, format: ID:YES or ID:NO
Do not add explanations. Do not skip any film.

Films:
{films_block}"""


def parse_response(text: str) -> dict[int, bool]:
    """Parse Claude's response into {film_id: should_have_tag}."""
    results = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Handle formats like "123:YES", "123: YES", "[123]:YES", "123 - YES"
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


async def review_batch(
    client: anthropic.AsyncAnthropic,
    films: list[dict],
    tag: str,
    description: str,
    model: str,
) -> dict[int, bool]:
    """Send a batch of films to Claude for review."""
    prompt = build_batch_prompt(films, tag, description)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        results = parse_response(text)

        # Track token usage
        usage = response.usage
        return results, usage.input_tokens, usage.output_tokens

    except anthropic.RateLimitError:
        logger.warning("Rate limited, waiting 30s...")
        await asyncio.sleep(30)
        return await review_batch(client, films, tag, description, model)
    except anthropic.APIStatusError as e:
        logger.error("API error: %s", e)
        return {}, 0, 0


async def apply_changes(
    pool: asyncpg.Pool,
    dimension: str,
    tag_id: int,
    to_add: list[int],
    to_remove: list[int],
):
    """Apply tag additions and removals to the database."""
    _, _, _, junc_table, junc_fk = DIMENSION_MAP[dimension]

    async with pool.acquire() as conn:
        if to_add:
            await conn.executemany(
                f"INSERT INTO {junc_table} (film_id, {junc_fk}) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                [(fid, tag_id) for fid in to_add],
            )
            logger.info("Added tag to %d films", len(to_add))

        if to_remove:
            await conn.execute(
                f"DELETE FROM {junc_table} WHERE {junc_fk} = $1 AND film_id = ANY($2)",
                tag_id, to_remove,
            )
            logger.info("Removed tag from %d films", len(to_remove))


def save_progress(results_file: Path, results: dict[int, bool]):
    """Save intermediate results to a JSON file."""
    # Convert int keys to strings for JSON
    data = {str(k): v for k, v in results.items()}
    results_file.write_text(json.dumps(data, indent=2))


def load_progress(results_file: Path) -> dict[int, bool]:
    """Load previous results from a JSON file."""
    if not results_file.exists():
        return {}
    data = json.loads(results_file.read_text())
    return {int(k): v for k, v in data.items()}


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Review a taxonomy tag across all films using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dimension", required=True, choices=list(DIMENSION_MAP.keys()),
                        help="Taxonomy dimension")
    parser.add_argument("--tag", required=True, help="Tag name to review")
    parser.add_argument("--description", help="Custom description of what the tag means")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001",
                        help="Claude model to use (default: haiku)")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Films per API call (default: 10)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes to DB (default: dry-run)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from previous run")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL", "")
    # Convert SQLAlchemy URL to asyncpg format
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    if not dsn:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    description = args.description or get_tag_description(args.tag)
    results_file = Path(f"scripts/data/review_{args.dimension}_{args.tag}.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    pool = await asyncpg.create_pool(dsn)
    client = anthropic.AsyncAnthropic(api_key=api_key)

    try:
        # Verify tag exists
        tag_id = await fetch_tag_id(pool, args.dimension, args.tag)
        if tag_id is None:
            logger.error("Tag '%s' not found in dimension '%s'", args.tag, args.dimension)
            sys.exit(1)

        # Fetch data
        all_films = await fetch_all_films(pool)
        currently_tagged = await fetch_tagged_film_ids(pool, args.dimension, args.tag)

        logger.info("Total films: %d | Currently tagged '%s': %d",
                     len(all_films), args.tag, len(currently_tagged))

        # Load previous progress if resuming
        all_results: dict[int, bool] = {}
        if args.resume:
            all_results = load_progress(results_file)
            logger.info("Resumed with %d previously reviewed films", len(all_results))

        # Filter out already-reviewed films
        films_to_review = [f for f in all_films if f["film_id"] not in all_results]
        logger.info("Films to review: %d", len(films_to_review))

        # Process in batches
        total_input = 0
        total_output = 0
        start_time = time.time()

        for i in range(0, len(films_to_review), args.batch_size):
            batch = films_to_review[i : i + args.batch_size]
            batch_num = i // args.batch_size + 1
            total_batches = (len(films_to_review) + args.batch_size - 1) // args.batch_size

            results, inp_tokens, out_tokens = await review_batch(
                client, batch, args.tag, description, args.model
            )
            total_input += inp_tokens
            total_output += out_tokens
            all_results.update(results)

            # Progress
            reviewed = min(i + args.batch_size, len(films_to_review))
            elapsed = time.time() - start_time
            rate = reviewed / elapsed if elapsed > 0 else 0
            eta = (len(films_to_review) - reviewed) / rate if rate > 0 else 0

            missing = len(batch) - len(results)
            miss_str = f" ({missing} unparsed)" if missing > 0 else ""

            logger.info(
                "Batch %d/%d — %d/%d films — %.0f films/min — ETA %.0fs — "
                "tokens: %dK in / %dK out%s",
                batch_num, total_batches, reviewed, len(films_to_review),
                rate * 60, eta, total_input // 1000, total_output // 1000,
                miss_str,
            )

            # Save progress after each batch
            save_progress(results_file, all_results)

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

        # Compute changes
        to_add = []
        to_remove = []
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

        # Report
        print(f"\n{'='*60}")
        print(f"Review complete: '{args.tag}' in {args.dimension}")
        print(f"{'='*60}")
        print(f"Total films reviewed: {len(all_results)}")
        print(f"Currently tagged:     {len(currently_tagged)}")
        print(f"Should be tagged:     {sum(1 for v in all_results.values() if v)}")
        print(f"To ADD:               {len(to_add)}")
        print(f"To REMOVE:            {len(to_remove)}")
        print(f"Tokens used:          {total_input:,} input + {total_output:,} output")

        # Estimate cost (Haiku pricing)
        if "haiku" in args.model:
            cost = total_input * 0.80 / 1_000_000 + total_output * 4.0 / 1_000_000
        elif "sonnet" in args.model:
            cost = total_input * 3.0 / 1_000_000 + total_output * 15.0 / 1_000_000
        else:
            cost = total_input * 15.0 / 1_000_000 + total_output * 75.0 / 1_000_000
        print(f"Estimated cost:       ${cost:.2f}")

        if to_add:
            print(f"\n--- Films to ADD '{args.tag}' ---")
            add_films = {f["film_id"]: f for f in all_films}
            for fid in to_add[:50]:
                f = add_films[fid]
                print(f"  + [{fid}] {f['original_title']} ({f.get('year', '?')})")
            if len(to_add) > 50:
                print(f"  ... and {len(to_add) - 50} more")

        if to_remove:
            print(f"\n--- Films to REMOVE '{args.tag}' ---")
            rem_films = {f["film_id"]: f for f in all_films}
            for fid in to_remove[:50]:
                f = rem_films[fid]
                print(f"  - [{fid}] {f['original_title']} ({f.get('year', '?')})")
            if len(to_remove) > 50:
                print(f"  ... and {len(to_remove) - 50} more")

        # Apply if requested
        if args.apply and (to_add or to_remove):
            print(f"\nApplying changes...")
            await apply_changes(pool, args.dimension, tag_id, to_add, to_remove)
            print("Done!")
        elif to_add or to_remove:
            print(f"\nDry-run mode. Use --apply to execute changes.")
            print(f"Results saved to: {results_file}")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
