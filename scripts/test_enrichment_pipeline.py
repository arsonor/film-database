"""
End-to-end validation of the Claude enrichment pipeline.

Tests the enrichment of the 3 reference films (2001: A Space Odyssey,
La Haine, Mulholland Drive) and compares output against the expected
classifications from CLAUDE.md.

Usage:
    python scripts/test_enrichment_pipeline.py
"""

import asyncio
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.claude_enricher import ClaudeEnricher  # noqa: E402
from app.services.taxonomy_config import REFERENCE_EXAMPLES  # noqa: E402

logger = logging.getLogger(__name__)


# =============================================================================
# Mock TMDB-mapped data for the 3 reference films
# (Simulates the output of TMDBMapper.map_film_to_db())
# =============================================================================

REFERENCE_TMDB_DATA = {
    "2001": {
        "film": {
            "original_title": "2001: A Space Odyssey",
            "duration": 149,
            "color": True,
            "first_release_date": "1968-04-02",
            "summary": "Humanity finds a mysterious object buried beneath the lunar surface and sets off to find its origins with the help of HAL 9000, the world's most advanced supercomputer.",
            "poster_url": "https://image.tmdb.org/t/p/w500/ve72VENBiEuJSdhLMEfJCqGfbFn.jpg",
            "backdrop_url": None,
            "imdb_id": "tt0062622",
            "tmdb_id": 62,
            "budget": 12000000,
            "revenue": 190000000,
        },
        "titles": [
            {"language_code": "en", "title": "2001: A Space Odyssey", "is_original": True},
            {"language_code": "fr", "title": "2001 : L'Odyssée de l'espace", "is_original": False},
        ],
        "categories": ["Science-Fiction", "Adventure"],
        "historic_subcategories": [],
        "crew": [
            {"firstname": "Stanley", "lastname": "Kubrick", "tmdb_id": 240, "role": "Director", "photo_url": None},
            {"firstname": "Stanley", "lastname": "Kubrick", "tmdb_id": 240, "role": "Writer", "photo_url": None},
            {"firstname": "Arthur C.", "lastname": "Clarke", "tmdb_id": 2994, "role": "Writer", "photo_url": None},
        ],
        "cast": [
            {"firstname": "Keir", "lastname": "Dullea", "tmdb_id": 7506, "character_name": "Dr. Dave Bowman", "cast_order": 0, "photo_url": None},
            {"firstname": "Gary", "lastname": "Lockwood", "tmdb_id": 7507, "character_name": "Dr. Frank Poole", "cast_order": 1, "photo_url": None},
            {"firstname": "William", "lastname": "Sylvester", "tmdb_id": 7508, "character_name": "Dr. Heywood R. Floyd", "cast_order": 2, "photo_url": None},
            {"firstname": "Daniel", "lastname": "Richter", "tmdb_id": 150703, "character_name": "Moon-Watcher", "cast_order": 3, "photo_url": None},
            {"firstname": "Leonard", "lastname": "Rossiter", "tmdb_id": 7509, "character_name": "Dr. Andrei Smyslov", "cast_order": 4, "photo_url": None},
            {"firstname": "Douglas", "lastname": "Rain", "tmdb_id": 15218, "character_name": "HAL 9000 (voice)", "cast_order": 5, "photo_url": None},
        ],
        "studios": [{"name": "Metro-Goldwyn-Mayer", "country": "US"}],
        "languages": [{"code": "en", "name": "English"}],
        "keywords": ["artificial intelligence", "man vs machine", "space travel", "evolution", "astronaut"],
        "production_countries": ["US", "GB"],
    },
    "la_haine": {
        "film": {
            "original_title": "La Haine",
            "duration": 98,
            "color": False,
            "first_release_date": "1995-05-31",
            "summary": "After a young Arab is arrested and beaten unconscious by police, a riot erupts in the housing projects just outside of Paris. Three friends — Vinz, Hubert, and Saïd — wander around the city in the aftermath.",
            "poster_url": "https://image.tmdb.org/t/p/w500/2w0faxGnSJR4Xv7FHZYvQ0y3L4l.jpg",
            "backdrop_url": None,
            "imdb_id": "tt0113247",
            "tmdb_id": 3405,
            "budget": 2920000,
            "revenue": 600000,
        },
        "titles": [
            {"language_code": "fr", "title": "La Haine", "is_original": True},
            {"language_code": "en", "title": "Hate", "is_original": False},
        ],
        "categories": ["Drama"],
        "historic_subcategories": [],
        "crew": [
            {"firstname": "Mathieu", "lastname": "Kassovitz", "tmdb_id": 11544, "role": "Director", "photo_url": None},
            {"firstname": "Mathieu", "lastname": "Kassovitz", "tmdb_id": 11544, "role": "Writer", "photo_url": None},
        ],
        "cast": [
            {"firstname": "Vincent", "lastname": "Cassel", "tmdb_id": 1785, "character_name": "Vinz", "cast_order": 0, "photo_url": None},
            {"firstname": "Hubert", "lastname": "Koundé", "tmdb_id": 19580, "character_name": "Hubert", "cast_order": 1, "photo_url": None},
            {"firstname": "Saïd", "lastname": "Taghmaoui", "tmdb_id": 19581, "character_name": "Saïd", "cast_order": 2, "photo_url": None},
            {"firstname": "Abdel Ahmed", "lastname": "Ghili", "tmdb_id": 1197896, "character_name": "Abdel", "cast_order": 3, "photo_url": None},
            {"firstname": "Solo", "lastname": "", "tmdb_id": 1197897, "character_name": "Santo", "cast_order": 4, "photo_url": None},
        ],
        "studios": [{"name": "Canal+", "country": "FR"}],
        "languages": [{"code": "fr", "name": "French"}],
        "keywords": ["police brutality", "racism", "banlieue", "friendship", "violence"],
        "production_countries": ["FR"],
    },
    "mulholland_drive": {
        "film": {
            "original_title": "Mulholland Drive",
            "duration": 147,
            "color": True,
            "first_release_date": "2001-06-06",
            "summary": "Blonde Betty Elms has only just arrived in Hollywood to become a movie star when she meets an enigmatic brunette with amnesia. As the two set off to solve the second woman's identity, they are enveloped in a twisting web of mystery.",
            "poster_url": "https://image.tmdb.org/t/p/w500/tVxGt7ZiFBtAiHRg7W1bpbYOBbY.jpg",
            "backdrop_url": None,
            "imdb_id": "tt0166924",
            "tmdb_id": 1018,
            "budget": 15000000,
            "revenue": 20100000,
        },
        "titles": [
            {"language_code": "en", "title": "Mulholland Drive", "is_original": True},
            {"language_code": "fr", "title": "Mulholland Drive", "is_original": False},
        ],
        "categories": ["Drama", "Thriller"],
        "historic_subcategories": [],
        "crew": [
            {"firstname": "David", "lastname": "Lynch", "tmdb_id": 5602, "role": "Director", "photo_url": None},
            {"firstname": "David", "lastname": "Lynch", "tmdb_id": 5602, "role": "Writer", "photo_url": None},
        ],
        "cast": [
            {"firstname": "Naomi", "lastname": "Watts", "tmdb_id": 1397, "character_name": "Betty Elms / Diane Selwyn", "cast_order": 0, "photo_url": None},
            {"firstname": "Laura", "lastname": "Harring", "tmdb_id": 1399, "character_name": "Rita / Camilla Rhodes", "cast_order": 1, "photo_url": None},
            {"firstname": "Justin", "lastname": "Theroux", "tmdb_id": 8210, "character_name": "Adam Kesher", "cast_order": 2, "photo_url": None},
            {"firstname": "Ann", "lastname": "Miller", "tmdb_id": 30584, "character_name": "Coco Lenoix", "cast_order": 3, "photo_url": None},
            {"firstname": "Robert", "lastname": "Forster", "tmdb_id": 8874, "character_name": "Detective Harry McKnight", "cast_order": 4, "photo_url": None},
        ],
        "studios": [{"name": "Les Films Alain Sarde", "country": "FR"}],
        "languages": [{"code": "en", "name": "English"}],
        "keywords": ["dream", "hollywood", "amnesia", "mystery", "surrealism", "identity"],
        "production_countries": ["US", "FR"],
    },
}


def compare_dimension(
    expected: list | dict | str | None,
    actual: list | dict | str | None,
    dim_name: str,
) -> dict:
    """
    Compare expected vs actual values for a dimension.

    Returns dict with: expected, actual, matches, misses, extras, accuracy.
    """
    if isinstance(expected, list) and isinstance(actual, list):
        expected_set = set(str(v) for v in expected)
        actual_set = set(str(v) for v in actual)
        matches = expected_set & actual_set
        misses = expected_set - actual_set
        extras = actual_set - expected_set
        accuracy = len(matches) / max(len(expected_set), 1)
        return {
            "expected": sorted(expected_set),
            "actual": sorted(actual_set),
            "matches": sorted(matches),
            "misses": sorted(misses),
            "extras": sorted(extras),
            "accuracy": accuracy,
        }
    elif isinstance(expected, dict) and isinstance(actual, dict):
        # For source: compare type
        exp_type = expected.get("type")
        act_type = actual.get("type")
        match = exp_type == act_type
        return {
            "expected": str(expected),
            "actual": str(actual),
            "matches": [exp_type] if match else [],
            "misses": [exp_type] if not match else [],
            "extras": [],
            "accuracy": 1.0 if match else 0.0,
        }
    else:
        match = str(expected) == str(actual)
        return {
            "expected": str(expected),
            "actual": str(actual),
            "matches": [],
            "misses": [],
            "extras": [],
            "accuracy": 1.0 if match else 0.0,
        }


def print_comparison(film_name: str, expected: dict, actual: dict):
    """Print a comparison table for a film's enrichment."""
    print(f"\n{'=' * 70}")
    print(f"  {film_name}")
    print(f"{'=' * 70}")

    dimensions = [
        ("categories", "categories"),
        ("cinema_type", "cinema_type"),
        ("cultural_movement", "cultural_movement"),
        ("time_context", "time_context"),
        ("place_environment", "place_environment"),
        ("themes", "themes"),
        ("characters_type", "characters_type"),
        ("character_context", "character_context"),
        ("atmosphere", "atmosphere"),
        ("motivations", "motivations"),
        ("message", "message"),
        ("source", "source"),
    ]

    accuracies = {}

    for dim_label, dim_key in dimensions:
        exp = expected.get(dim_key, [])
        act = actual.get(dim_key, [])
        comp = compare_dimension(exp, act, dim_label)
        accuracies[dim_label] = comp["accuracy"]

        status = "✅" if comp["accuracy"] >= 0.8 else ("⚠️" if comp["accuracy"] >= 0.5 else "❌")
        print(f"\n  {status} {dim_label} ({comp['accuracy']:.0%})")
        print(f"     Expected: {comp['expected']}")
        print(f"     Actual:   {comp['actual']}")
        if comp.get("misses"):
            print(f"     Missing:  {comp['misses']}")
        if comp.get("extras"):
            print(f"     Extra:    {comp['extras']}")

    overall = sum(accuracies.values()) / max(len(accuracies), 1)
    print(f"\n  Overall accuracy: {overall:.0%}")

    # Warn for low-accuracy dimensions
    low_dims = [d for d, a in accuracies.items() if a < 0.8]
    if low_dims:
        print(f"\n  ⚠️  Dimensions below 80%: {', '.join(low_dims)}")
        print(f"     Consider tuning the enrichment prompt for these dimensions.")

    return accuracies, overall


async def run_test():
    """Run the enrichment test on all 3 reference films."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("=" * 70)
        print("  ERROR: ANTHROPIC_API_KEY not set")
        print("=" * 70)
        print()
        print("  This test requires an Anthropic API key to call Claude.")
        print("  Set it in your .env file:")
        print("    ANTHROPIC_API_KEY=sk-ant-...")
        print()
        print("  Get your key at: https://console.anthropic.com/settings/keys")
        sys.exit(1)

    enricher = ClaudeEnricher(api_key=api_key)

    print("=" * 70)
    print("  ENRICHMENT PIPELINE VALIDATION")
    print("  Testing with 3 reference films from CLAUDE.md")
    print(f"  Model: {enricher.model}")
    print("=" * 70)

    all_accuracies = {}
    all_overalls = []

    for key, ref in REFERENCE_EXAMPLES.items():
        title = ref["title"]
        expected = ref["enrichment"]
        tmdb_data = REFERENCE_TMDB_DATA.get(key)

        if not tmdb_data:
            print(f"\n  ⚠️  No mock TMDB data for {key}, skipping")
            continue

        print(f"\n  Enriching: {title} ({ref['year']})...")

        try:
            actual = await enricher.enrich_film(tmdb_data)
        except Exception as e:
            print(f"\n  ❌ Error enriching {title}: {e}")
            continue

        accuracies, overall = print_comparison(title, expected, actual)
        all_accuracies[title] = accuracies
        all_overalls.append(overall)

    # Overall summary
    print(f"\n{'=' * 70}")
    print("  OVERALL SUMMARY")
    print(f"{'=' * 70}")

    if all_overalls:
        grand_avg = sum(all_overalls) / len(all_overalls)
        print(f"\n  Average accuracy across all films: {grand_avg:.0%}")

        # Aggregate per-dimension accuracy
        dim_avgs: dict[str, list[float]] = defaultdict(list)
        for title_accs in all_accuracies.values():
            for dim, acc in title_accs.items():
                dim_avgs[dim].append(acc)

        print("\n  Per-dimension average accuracy:")
        for dim in sorted(dim_avgs):
            avg = sum(dim_avgs[dim]) / len(dim_avgs[dim])
            status = "✅" if avg >= 0.8 else ("⚠️" if avg >= 0.5 else "❌")
            print(f"    {status} {dim:25s}: {avg:.0%}")

        if grand_avg < 0.8:
            print("\n  ⚠️  Overall accuracy is below 80%.")
            print("     Consider tuning the enrichment prompt before bulk processing.")
        else:
            print("\n  ✅ Pipeline is well-calibrated for bulk enrichment.")

    print(f"\n{'=' * 70}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
