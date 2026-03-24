"""
Batch TMDB resolver for the Film Database project.

Takes parsed_films.json and resolves each title against TMDB,
producing resolved_films.json and unresolved_films.json.

Usage:
    python scripts/tmdb_resolver.py --input scripts/data/parsed_films.json --batch-size 50
    python scripts/tmdb_resolver.py --start-year 1960 --end-year 1970
    python scripts/tmdb_resolver.py --retry-unresolved
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

from app.services.tmdb_service import TMDBService, TMDBError  # noqa: E402
from app.services.tmdb_mapper import TMDBMapper  # noqa: E402

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, **kwargs):
        total = kwargs.get("total", None)
        desc = kwargs.get("desc", "")
        for i, item in enumerate(iterable):
            if total:
                print(f"\r{desc} {i + 1}/{total}", end="", flush=True)
            yield item
        print()

logger = logging.getLogger(__name__)


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


def build_resolved_key(film: dict) -> str:
    """Build a unique key for a film entry to detect already-resolved titles."""
    return f"{film['year']}|{film['title'].lower().strip()}"


async def resolve_batch(
    films: list[dict],
    tmdb: TMDBService,
    mapper: TMDBMapper,
    resolved: list[dict],
    unresolved: list[dict],
    resolved_keys: set[str],
    output_dir: Path,
    batch_size: int,
):
    """
    Resolve a batch of films, saving checkpoints every batch_size films.
    """
    resolved_path = output_dir / "resolved_films.json"
    unresolved_path = output_dir / "unresolved_films.json"
    count = 0

    for film in tqdm(films, total=len(films), desc="Resolving films"):
        key = build_resolved_key(film)

        # Skip already resolved
        if key in resolved_keys:
            continue

        title = film.get("original_title_hint") or film["title"]
        year = film.get("year")

        try:
            details = await tmdb.resolve_title(title, year=year)

            if details:
                # Also get French details for French title
                fr_details = None
                try:
                    fr_details = await tmdb.get_film_details_fr(details["tmdb_id"])
                except TMDBError:
                    pass

                mapped = await mapper.map_film_to_db(details, fr_details)
                mapped["_source"] = {
                    "parsed_title": film["title"],
                    "parsed_year": film["year"],
                    "region": film.get("region", ""),
                    "notes": film.get("notes", ""),
                }
                resolved.append(mapped)
                resolved_keys.add(key)
            else:
                # Try with the original title if we used a hint
                if film.get("original_title_hint") and film["title"] != title:
                    details = await tmdb.resolve_title(film["title"], year=year)
                    if details:
                        fr_details = None
                        try:
                            fr_details = await tmdb.get_film_details_fr(details["tmdb_id"])
                        except TMDBError:
                            pass

                        mapped = await mapper.map_film_to_db(details, fr_details)
                        mapped["_source"] = {
                            "parsed_title": film["title"],
                            "parsed_year": film["year"],
                            "region": film.get("region", ""),
                            "notes": film.get("notes", ""),
                        }
                        resolved.append(mapped)
                        resolved_keys.add(key)
                    else:
                        unresolved.append(film)
                else:
                    unresolved.append(film)

        except TMDBError as e:
            logger.error("TMDB error for '%s' (%s): %s", film["title"], year, e)
            unresolved.append(film)
        except Exception as e:
            logger.error("Unexpected error for '%s' (%s): %s", film["title"], year, e)
            unresolved.append(film)

        count += 1

        # Checkpoint every batch_size films
        if count % batch_size == 0:
            save_json(resolved_path, resolved)
            save_json(unresolved_path, unresolved)
            logger.info("Checkpoint saved: %d resolved, %d unresolved",
                        len(resolved), len(unresolved))

    # Final save
    save_json(resolved_path, resolved)
    save_json(unresolved_path, unresolved)


def print_summary(resolved: list[dict], unresolved: list[dict]):
    """Print resolution summary."""
    total = len(resolved) + len(unresolved)
    print("\n" + "=" * 60)
    print("RESOLUTION SUMMARY")
    print("=" * 60)
    print(f"Total processed: {total}")
    print(f"Resolved:   {len(resolved)} ({100 * len(resolved) / max(total, 1):.1f}%)")
    print(f"Unresolved: {len(unresolved)} ({100 * len(unresolved) / max(total, 1):.1f}%)")

    # Match rate per decade
    decade_resolved = defaultdict(int)
    decade_total = defaultdict(int)

    for film in resolved:
        src = film.get("_source", {})
        year = src.get("parsed_year", 0)
        decade = (year // 10) * 10
        decade_resolved[decade] += 1
        decade_total[decade] += 1

    for film in unresolved:
        year = film.get("year", 0)
        decade = (year // 10) * 10
        decade_total[decade] += 1

    print("\nMatch rate per decade:")
    for decade in sorted(decade_total):
        if decade == 0:
            continue
        res = decade_resolved.get(decade, 0)
        tot = decade_total[decade]
        pct = 100 * res / max(tot, 1)
        print(f"  {decade}s: {res}/{tot} ({pct:.0f}%)")

    print("=" * 60)


async def run_resolver(args):
    """Main resolver logic."""
    load_dotenv()

    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("Error: TMDB_API_KEY not set. Add it to .env or environment.")
        sys.exit(1)

    input_path = Path(args.input)
    output_dir = input_path.parent

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Load input films
    all_films = load_json(input_path)
    print(f"Loaded {len(all_films)} films from {input_path}")

    # Filter by year range if specified
    films = all_films
    if args.start_year:
        films = [f for f in films if f.get("year", 0) >= args.start_year]
    if args.end_year:
        films = [f for f in films if f.get("year", 0) <= args.end_year]

    if args.start_year or args.end_year:
        yr_range = f"{args.start_year or '...'}-{args.end_year or '...'}"
        print(f"Filtered to {len(films)} films in year range {yr_range}")

    # Load existing results for resume capability
    resolved_path = output_dir / "resolved_films.json"
    unresolved_path = output_dir / "unresolved_films.json"

    resolved = load_json(resolved_path) if not args.retry_unresolved else load_json(resolved_path)
    unresolved_existing = load_json(unresolved_path)

    # Build set of already-resolved keys
    resolved_keys = set()
    for r in resolved:
        src = r.get("_source", {})
        key = f"{src.get('parsed_year', '')}|{src.get('parsed_title', '').lower().strip()}"
        resolved_keys.add(key)

    # If retrying unresolved, use those as input
    if args.retry_unresolved:
        films = unresolved_existing
        unresolved_existing = []
        print(f"Retrying {len(films)} previously unresolved films")

    unresolved = []

    # Skip already resolved
    films_to_process = [
        f for f in films if build_resolved_key(f) not in resolved_keys
    ]
    print(f"Films to process (after skipping resolved): {len(films_to_process)}")

    if not films_to_process:
        print("Nothing to process.")
        print_summary(resolved, unresolved_existing)
        return

    async with TMDBService(api_key) as tmdb:
        mapper = TMDBMapper(tmdb)
        await resolve_batch(
            films_to_process,
            tmdb,
            mapper,
            resolved,
            unresolved,
            resolved_keys,
            output_dir,
            args.batch_size,
        )

    print_summary(resolved, unresolved)


# =============================================================================
# Smoke test: validate the 3 reference films from CLAUDE.md
# =============================================================================

async def smoke_test():
    """
    Test TMDB resolution with the three reference films:
    - 2001: A Space Odyssey (1968)
    - La Haine (1995)
    - Mulholland Drive (2001)
    """
    load_dotenv()

    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("Error: TMDB_API_KEY not set. Add it to .env or environment.")
        sys.exit(1)

    print("=" * 60)
    print("SMOKE TEST — 3 Reference Films")
    print("=" * 60)

    reference_films = [
        ("2001: A Space Odyssey", 1968),
        ("La Haine", 1995),
        ("Mulholland Drive", 2001),
    ]

    async with TMDBService(api_key) as tmdb:
        mapper = TMDBMapper(tmdb)

        for title, year in reference_films:
            print(f"\n{'─' * 50}")
            print(f"Resolving: {title} ({year})")
            print(f"{'─' * 50}")

            details = await tmdb.resolve_title(title, year=year)
            if not details:
                print(f"  ❌ FAILED to resolve {title}")
                continue

            fr_details = None
            try:
                fr_details = await tmdb.get_film_details_fr(details["tmdb_id"])
            except TMDBError:
                pass

            mapped = await mapper.map_film_to_db(details, fr_details)
            film = mapped["film"]

            # Print readable summary
            print(f"  TMDB ID:    {film['tmdb_id']}")
            print(f"  Title:      {film['original_title']}")
            print(f"  Date:       {film['first_release_date']}")
            print(f"  Duration:   {film['duration']} min")
            print(f"  IMDB ID:    {film['imdb_id']}")
            print(f"  Budget:     ${film['budget']:,}" if film['budget'] else "  Budget:     N/A")
            print(f"  Revenue:    ${film['revenue']:,}" if film['revenue'] else "  Revenue:    N/A")
            print(f"  Poster:     {film['poster_url']}")

            print(f"  Titles:     {[t['title'] for t in mapped['titles']]}")
            print(f"  Categories: {mapped['categories']}")

            directors = [c for c in mapped["crew"] if c["role"] == "Director"]
            print(f"  Director:   {', '.join(d['firstname'] + ' ' + d['lastname'] for d in directors)}")
            print(f"  Cast ({len(mapped['cast'])} members):")
            for actor in mapped["cast"][:5]:
                print(f"    - {actor['firstname']} {actor['lastname']} as {actor['character_name']}")

            print(f"  Studios:    {[s['name'] for s in mapped['studios']]}")
            print(f"  Keywords:   {mapped['keywords'][:8]}")

            # Validation checks
            errors = []
            if not film["tmdb_id"]:
                errors.append("Missing tmdb_id")
            if not film["poster_url"] or not film["poster_url"].startswith("https://"):
                errors.append("poster_url is not a full URL")
            if len(mapped["cast"]) < 5:
                errors.append(f"Cast has only {len(mapped['cast'])} entries (expected ≥5)")
            if not directors:
                errors.append("No Director found in crew")
            # Budget/revenue check only for 2001 (known to have data)
            if title == "2001: A Space Odyssey":
                if not film["budget"]:
                    errors.append("Budget missing for 2001")
                if not film["revenue"]:
                    errors.append("Revenue missing for 2001")

            if errors:
                print(f"  ⚠️  Validation issues: {errors}")
            else:
                print(f"  ✅ All validation checks passed")

    print(f"\n{'=' * 60}")
    print("Smoke test complete.")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Batch resolve film titles against TMDB")
    parser.add_argument(
        "--input",
        default="scripts/data/parsed_films.json",
        help="Path to parsed_films.json (default: scripts/data/parsed_films.json)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Save checkpoint every N films (default: 50)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="Process films from this year onwards",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Process films up to this year",
    )
    parser.add_argument(
        "--retry-unresolved",
        action="store_true",
        help="Re-attempt previously unresolved films",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test with 3 reference films instead of batch processing",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.smoke_test:
        asyncio.run(smoke_test())
    else:
        asyncio.run(run_resolver(args))


if __name__ == "__main__":
    main()
