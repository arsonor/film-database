"""
Batch Claude enrichment runner for the Film Database project.

Takes resolved TMDB data and runs Claude enrichment on each film to classify
it into the full custom taxonomy.

Usage:
    python scripts/claude_enrichment_runner.py --input scripts/data/resolved_films.json --batch-size 10
    python scripts/claude_enrichment_runner.py --start-index 0 --end-index 50
    python scripts/claude_enrichment_runner.py --review-only
    python scripts/claude_enrichment_runner.py --model claude-opus-4-20250514
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.claude_enricher import ClaudeEnricher  # noqa: E402

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        total = kwargs.get("total", None)
        desc = kwargs.get("desc", "")
        for i, item in enumerate(iterable):
            if total:
                print(f"\r{desc} {i + 1}/{total}", end="", flush=True)
            yield item
        print()

logger = logging.getLogger(__name__)

# Anthropic pricing (per million tokens) — Sonnet 4
SONNET_INPUT_PRICE = 3.00    # $/M input tokens
SONNET_OUTPUT_PRICE = 15.00  # $/M output tokens
OPUS_INPUT_PRICE = 15.00
OPUS_OUTPUT_PRICE = 75.00


def load_json(path: Path) -> list | dict:
    """Load a JSON file, returning empty list if not found."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    """Save data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def build_film_key(film: dict) -> str:
    """Build a unique key for a film entry."""
    src = film.get("_source", {})
    tmdb_id = film.get("film", {}).get("tmdb_id")
    if tmdb_id:
        return str(tmdb_id)
    return f"{src.get('parsed_year', '')}|{src.get('parsed_title', '').lower().strip()}"


async def run_enrichment(args):
    """Main enrichment logic."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        print("Add it to your .env file or set it as an environment variable.")
        print("Get your key at: https://console.anthropic.com/settings/keys")
        sys.exit(1)

    input_path = Path(args.input)
    output_dir = input_path.parent
    enriched_path = output_dir / "enriched_films.json"
    review_path = output_dir / "enrichment_review.json"

    # Load input
    if args.review_only:
        if not review_path.exists():
            print(f"Error: Review file not found: {review_path}")
            sys.exit(1)
        all_films = load_json(review_path)
        print(f"Loaded {len(all_films)} films from review queue")
    else:
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            sys.exit(1)
        all_films = load_json(input_path)
        print(f"Loaded {len(all_films)} films from {input_path}")

    # Slice by index
    films = all_films
    if args.start_index is not None:
        films = films[args.start_index:]
    if args.end_index is not None:
        end = args.end_index - (args.start_index or 0)
        films = films[:end]

    if args.start_index is not None or args.end_index is not None:
        print(f"Processing slice: {len(films)} films "
              f"(index {args.start_index or 0} to {(args.start_index or 0) + len(films)})")

    # Load existing enriched films for resume
    enriched = load_json(enriched_path)
    enriched_keys = set()
    for ef in enriched:
        k = build_film_key(ef)
        enriched_keys.add(k)

    # Filter out already enriched
    films_to_process = []
    for f in films:
        key = build_film_key(f)
        if key not in enriched_keys:
            films_to_process.append(f)

    print(f"Films to process (after skipping enriched): {len(films_to_process)}")

    if not films_to_process:
        print("Nothing to process.")
        print_summary(enriched, [])
        return

    # Estimate cost
    est_input_tokens = len(films_to_process) * 3000   # ~3k input tokens per film
    est_output_tokens = len(films_to_process) * 800    # ~800 output tokens per film
    is_opus = "opus" in args.model.lower()
    input_price = OPUS_INPUT_PRICE if is_opus else SONNET_INPUT_PRICE
    output_price = OPUS_OUTPUT_PRICE if is_opus else SONNET_OUTPUT_PRICE
    est_cost = (est_input_tokens * input_price + est_output_tokens * output_price) / 1_000_000
    print(f"Estimated API cost: ${est_cost:.2f} ({args.model})")

    # Run enrichment
    enricher = ClaudeEnricher(api_key=api_key, model=args.model)
    review_queue: list[dict] = []

    for i, film in enumerate(tqdm(films_to_process, total=len(films_to_process), desc="Enriching")):
        title = film.get("film", {}).get("original_title", "Unknown")
        logger.info("Enriching %d/%d: %s", i + 1, len(films_to_process), title)

        try:
            enrichment = await enricher.enrich_film(film)

            # Merge enrichment into film data
            enriched_film = {**film, "enrichment": enrichment}
            enriched.append(enriched_film)
            enriched_keys.add(build_film_key(film))

            # Check for low confidence or new value suggestions
            needs_review = False
            confidence = enrichment.get("confidence", {})
            for dim, score in confidence.items():
                if isinstance(score, (int, float)) and score < 0.6:
                    needs_review = True
                    break
            if enrichment.get("new_values_suggested"):
                needs_review = True

            if needs_review:
                review_queue.append(enriched_film)

        except Exception as e:
            logger.error("Failed to enrich '%s': %s", title, e)
            # Add to review queue with error note
            error_film = {**film, "enrichment_error": str(e)}
            review_queue.append(error_film)

        # Checkpoint
        if (i + 1) % args.batch_size == 0:
            save_json(enriched_path, enriched)
            save_json(review_path, review_queue)
            logger.info("Checkpoint saved: %d enriched, %d for review",
                        len(enriched), len(review_queue))

        # Brief delay between requests
        if i < len(films_to_process) - 1:
            await asyncio.sleep(0.3)

    # Final save
    save_json(enriched_path, enriched)
    save_json(review_path, review_queue)
    print_summary(enriched, review_queue)


def print_summary(enriched: list[dict], review_queue: list[dict]):
    """Print enrichment summary with statistics."""
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"Total enriched: {len(enriched)}")
    print(f"Flagged for review: {len(review_queue)}")

    if not enriched:
        return

    # Average confidence per dimension
    dim_scores: dict[str, list[float]] = defaultdict(list)
    new_suggestions: list[str] = []

    for ef in enriched:
        enrichment = ef.get("enrichment", {})
        confidence = enrichment.get("confidence", {})
        for dim, score in confidence.items():
            if isinstance(score, (int, float)):
                dim_scores[dim].append(score)
        suggestions = enrichment.get("new_values_suggested", [])
        if isinstance(suggestions, list):
            new_suggestions.extend(suggestions)

    if dim_scores:
        print("\nAverage confidence per dimension:")
        for dim in sorted(dim_scores):
            scores = dim_scores[dim]
            avg = sum(scores) / len(scores) if scores else 0
            print(f"  {dim:25s}: {avg:.2f}")

    if new_suggestions:
        print(f"\nNew taxonomy values suggested ({len(new_suggestions)}):")
        for s in set(new_suggestions):
            print(f"  - {s}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Batch Claude enrichment for films")
    parser.add_argument(
        "--input",
        default="scripts/data/resolved_films.json",
        help="Path to resolved_films.json (default: scripts/data/resolved_films.json)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Save checkpoint every N films (default: 10)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=None,
        help="Start processing from this index",
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="Stop processing at this index",
    )
    parser.add_argument(
        "--review-only",
        action="store_true",
        help="Re-process films from the review queue",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_enrichment(args))


if __name__ == "__main__":
    main()
