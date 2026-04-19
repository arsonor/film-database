"""
Batch Claude enrichment with prompt caching for the Film Database project.

Uses the Anthropic Batch API (50% discount, 24h turnaround) with prompt caching
(90% input cost reduction on cached system prompt) to enrich films at scale.

Modes:
    --test N             Enrich N films via real-time API (with caching) for validation
    --submit             Submit all unenriched films as a batch job
    --status BATCH_ID    Check batch processing status
    --collect BATCH_ID   Download results and merge into enriched_films.json

Examples:
    python scripts/claude_batch_enrichment.py --test 5
    python scripts/claude_batch_enrichment.py --test 3 --film-ids 775,550,680
    python scripts/claude_batch_enrichment.py --submit
    python scripts/claude_batch_enrichment.py --status msgbatch_abc123
    python scripts/claude_batch_enrichment.py --collect msgbatch_abc123
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.taxonomy_config import (  # noqa: E402
    REFERENCE_EXAMPLES,
    TAXONOMY_DIMENSIONS,
    VALID_SOURCE_TYPES,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Pricing (per million tokens) — Claude Sonnet 4
# =============================================================================
SONNET_INPUT_PRICE = 3.00
SONNET_OUTPUT_PRICE = 15.00
SONNET_CACHE_WRITE_PRICE = 3.75   # 25% more than input
SONNET_CACHE_READ_PRICE = 0.30    # 90% less than input
# Batch API: 50% discount on all of the above
BATCH_DISCOUNT = 0.5

# =============================================================================
# File paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
RESOLVED_PATH = DATA_DIR / "resolved_films.json"
ENRICHED_PATH = DATA_DIR / "enriched_films.json"
REVIEW_PATH = DATA_DIR / "enrichment_review.json"
BATCH_STATE_PATH = DATA_DIR / "batch_state.json"


# =============================================================================
# System prompt — fixed across all films, will be cached
# =============================================================================

def build_system_prompt() -> str:
    """Build the full system prompt with taxonomy + examples (cacheable)."""
    dims = TAXONOMY_DIMENSIONS

    taxonomy_section = f"""## Taxonomy Dimensions — Use ONLY these values (or prefix new ones with [NEW])

### Categories (pick all that apply)
Valid: {', '.join(dims['categories'])}

### Cinema Type (techniques, movements, sub-genres, and cultural eras)
Valid: {', '.join(dims['cinema_type'])}
Note: Use "Collection" for films that are part of a major franchise (sequels, prequels, shared universe).

### Time Context (when is the film set — can be multiple)
Valid: {', '.join(dims['time_context'])}
IMPORTANT: For films released after 2000 set in their present day, use ONLY "contemporary". Do NOT add "end 20th".

### Place Context — Geography
Provide as: continent > country > state/city
Specify place_type for each: diegetic (in-film), shooting (real location), or fictional

### Place Context — Environment (pick all that apply, but ONLY if they characterize the film's overall setting)
Valid: {', '.join(dims['place_environment'])}
IMPORTANT: "huis clos" = entire film confined to one space. "road movie" = journey structures the narrative. Other environments should be significant/recurring settings, not just briefly visited locations.

### Themes (pick all that apply — be thorough, but only CENTRAL themes)
Valid: {', '.join(dims['themes'])}
IMPORTANT: Each theme must be a defining aspect of the film. "death" = death is a central narrative thread, not just an incidental event.

### Characters (group structure + context + archetypes — pick all that apply)
Valid: {', '.join(dims['character_context'])}
Note: Include "couple" when a romantic relationship is central to the story.

### Atmosphere (pick all that apply)
Valid: {', '.join(dims['atmosphere'])}

### Motivations & Relations (pick all that apply)
Valid: {', '.join(dims['motivations'])}
Note: "fight" = physical combat/action scenes are significant in the film.

### Message Conveyed (pick all that apply)
Valid: {', '.join(dims['message'])}

### Source / Origin
Type (one of): {', '.join(VALID_SOURCE_TYPES)}
Source title (if applicable):
Author (if applicable):

### Awards & Nominations
List the most significant awards and nominations for this film. Focus on:
- Academy Awards (Oscars)
- Cannes Film Festival (Palme d'Or, Grand Prix, Best Director, etc.)
- Venice Film Festival (Golden Lion, Grand Jury Prize, etc.)
- Berlin Film Festival (Golden Bear, Silver Bear, etc.)
- César Awards (for French films)
- BAFTA Awards
- Golden Globes
- Other major festivals or ceremonies if relevant

For each, provide: festival_name, category, year, result ("won" or "nominated").
Only include awards you are confident about. If unsure, include fewer rather than risk errors."""

    # Reference examples
    examples_parts = []
    for key, ref in REFERENCE_EXAMPLES.items():
        enrichment = ref["enrichment"]
        examples_parts.append(
            f"### Example: {ref['title']} ({ref['year']})\n"
            f"{json.dumps(enrichment, indent=2, default=str)}"
        )
    examples_section = "## Reference Examples\n\n" + "\n\n".join(examples_parts)

    # Output format
    output_format = """## Output Format
Respond with ONLY this JSON structure:
{
  "categories": ["..."],
  "cinema_type": ["..."],
  "time_context": ["..."],
  "geography": [
    {"continent": "...", "country": "...", "state_city": "..." or null, "place_type": "diegetic|shooting|fictional"}
  ],
  "place_environment": ["..."],
  "themes": ["..."],
  "character_context": ["..."],
  "atmosphere": ["..."],
  "motivations": ["..."],
  "message": ["..."],
  "source": {
    "type": "...",
    "title": "..." or null,
    "author": "..." or null
  },
  "awards": [
    {"festival_name": "Academy Awards", "category": "Best Visual Effects", "year": 1969, "result": "won"},
    {"festival_name": "Academy Awards", "category": "Best Director", "year": 1969, "result": "nominated"}
  ],
  "confidence": {
    "categories": 0.0-1.0,
    "cinema_type": 0.0-1.0,
    "time_context": 0.0-1.0,
    "geography": 0.0-1.0,
    "place_environment": 0.0-1.0,
    "themes": 0.0-1.0,
    "character_context": 0.0-1.0,
    "atmosphere": 0.0-1.0,
    "motivations": 0.0-1.0,
    "message": 0.0-1.0,
    "source": 0.0-1.0,
    "awards": 0.0-1.0
  },
  "new_values_suggested": []
}"""

    core = """You are a film classification expert. Given metadata about a film, you classify it into a precise custom taxonomy. You must be accurate, thorough, and use your deep knowledge of cinema.

Core principles:
- ONLY use values from the provided valid value lists unless no existing value fits, in which case prefix new suggestions with [NEW].
- Be comprehensive: assign ALL relevant values, not just the most obvious ones.
- A dimension can have ZERO values if nothing is truly pertinent. Do not force tags. An empty list is better than a wrong tag.
- Provide a confidence score (0.0-1.0) for each dimension. Use lower scores when you're uncertain or the film is obscure.
- Respond ONLY with the JSON structure specified. No preamble, no markdown backticks.

Tag selection philosophy — tags must characterize the film as a whole:
- Each tag should represent a DEFINING or SIGNIFICANT aspect of the film, not an incidental detail.
- Ask yourself: "Would someone who has seen this film agree this tag defines it?" If it's just a passing scene or minor element, do NOT include it.
Ex: For themes like "death": only tag if death is a CENTRAL theme or narrative thread, not merely because a character dies incidentally.
- For motivations: "fight" applies when there are significant action/combat scenes (physical confrontations, battle sequences), not just metaphorical struggles.
- For cinema_type: include "Collection" if the film is part of a major franchise with sequels/prequels.

Source rules:
- Identify if based on a novel, true story, play, original screenplay, etc.
- For adaptations, include the source title and author when known.

Awards rules:
- Only include awards you are confident about. Fewer correct entries are better than invented ones.
- Focus on: Academy Awards, Cannes, Venice, Berlin, César, BAFTA, Golden Globes."""

    return f"{core}\n\n{taxonomy_section}\n\n{examples_section}\n\n{output_format}"


# =============================================================================
# User prompt — per-film metadata only
# =============================================================================

def build_user_prompt(tmdb_mapped_data: dict) -> str:
    """Build the user prompt with just the film-specific metadata."""
    film = tmdb_mapped_data.get("film", {})
    crew = tmdb_mapped_data.get("crew", [])
    cast = tmdb_mapped_data.get("cast", [])
    categories = tmdb_mapped_data.get("categories", [])
    keywords = tmdb_mapped_data.get("keywords", [])
    production_countries = tmdb_mapped_data.get("production_countries", [])
    languages = tmdb_mapped_data.get("languages", [])

    directors = [
        f"{c['firstname']} {c['lastname']}" for c in crew if c.get("role") == "Director"
    ]
    cast_lines = [
        f"{c['firstname']} {c['lastname']} as {c.get('character_name', '?')}"
        for c in cast[:10]
    ]

    release_date = film.get("first_release_date", "")
    year = ""
    if isinstance(release_date, date):
        year = str(release_date.year)
    elif isinstance(release_date, str) and len(release_date) >= 4:
        year = release_date[:4]

    budget_str = f"${film['budget']:,}" if film.get("budget") else "Unknown"
    revenue_str = f"${film['revenue']:,}" if film.get("revenue") else "Unknown"

    return f"""Classify this film into the taxonomy defined in your instructions.

## Film Metadata
- Title: {film.get('original_title', 'Unknown')}
- Year: {year}
- Overview: {film.get('summary', 'No overview available')}
- TMDB Genres: {', '.join(categories) if categories else 'N/A'}
- TMDB Keywords: {', '.join(keywords[:20]) if keywords else 'N/A'}
- Director: {', '.join(directors) if directors else 'Unknown'}
- Key Cast: {'; '.join(cast_lines) if cast_lines else 'N/A'}
- Production Countries: {', '.join(production_countries) if production_countries else 'N/A'}
- Budget: {budget_str} | Revenue: {revenue_str}
- Languages: {', '.join(lang.get('name', lang.get('code', '')) for lang in languages) if languages else 'N/A'}"""


# =============================================================================
# Validation (reused from claude_enricher.py logic)
# =============================================================================

def validate_enrichment(enrichment: dict) -> dict:
    """Validate and clean enrichment output against known taxonomy values."""
    valid_sets = {dim: set(values) for dim, values in TAXONOMY_DIMENSIONS.items()}
    valid_source_types = set(VALID_SOURCE_TYPES)
    new_suggestions: list[str] = []

    list_dims = [
        "categories", "cinema_type", "time_context",
        "place_environment", "themes", "character_context",
        "atmosphere", "motivations", "message",
    ]

    for dim in list_dims:
        values = enrichment.get(dim, [])
        if not isinstance(values, list):
            enrichment[dim] = []
            continue
        valid_set = valid_sets.get(dim, set())
        cleaned = []
        for v in values:
            if not isinstance(v, str):
                continue
            if v.startswith("[NEW]"):
                new_suggestions.append(f"{dim}: {v}")
                cleaned.append(v)
            elif v in valid_set:
                cleaned.append(v)
            else:
                logger.warning("Invalid %s value removed: '%s'", dim, v)
        enrichment[dim] = cleaned

    # Validate source
    source = enrichment.get("source", {})
    if isinstance(source, dict):
        src_type = source.get("type", "")
        if src_type and src_type not in valid_source_types:
            if src_type.startswith("[NEW]"):
                new_suggestions.append(f"source_type: {src_type}")
            else:
                source["type"] = None
        enrichment["source"] = source
    else:
        enrichment["source"] = {"type": None, "title": None, "author": None}

    # Validate geography
    geography = enrichment.get("geography", [])
    if isinstance(geography, list):
        valid_place_types = {"diegetic", "shooting", "fictional"}
        enrichment["geography"] = [
            g for g in geography
            if isinstance(g, dict) and g.get("place_type") in valid_place_types
        ]

    # Validate awards
    awards = enrichment.get("awards", [])
    if isinstance(awards, list):
        cleaned_awards = []
        for award in awards:
            if not isinstance(award, dict) or not award.get("festival_name"):
                continue
            if award.get("result") not in ("won", "nominated"):
                continue
            if not isinstance(award.get("year"), (int, float)):
                continue
            cleaned_awards.append({
                "festival_name": award["festival_name"],
                "category": award.get("category"),
                "year": int(award["year"]),
                "result": award["result"],
            })
        enrichment["awards"] = cleaned_awards
    else:
        enrichment["awards"] = []

    # Ensure confidence dict
    if not isinstance(enrichment.get("confidence"), dict):
        enrichment["confidence"] = {dim: 0.5 for dim in list_dims}
        enrichment["confidence"]["geography"] = 0.5
        enrichment["confidence"]["source"] = 0.5
        enrichment["confidence"]["awards"] = 0.5

    existing_suggestions = enrichment.get("new_values_suggested", [])
    if isinstance(existing_suggestions, list):
        new_suggestions.extend(existing_suggestions)
    enrichment["new_values_suggested"] = new_suggestions

    return enrichment


# =============================================================================
# Helpers
# =============================================================================

def load_json(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def build_film_key(film: dict) -> str:
    tmdb_id = film.get("film", {}).get("tmdb_id")
    if tmdb_id:
        return str(tmdb_id)
    src = film.get("_source", {})
    return f"{src.get('parsed_year', '')}|{src.get('parsed_title', '').lower().strip()}"


def get_unenriched_films(resolved: list, enriched: list) -> list:
    """Filter resolved films that haven't been enriched yet."""
    enriched_keys = set()
    for ef in enriched:
        enriched_keys.add(build_film_key(ef))
    return [f for f in resolved if build_film_key(f) not in enriched_keys]


def parse_claude_json(text: str) -> dict:
    """Parse JSON from Claude response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


# =============================================================================
# Mode 1: --test N  (real-time API with prompt caching)
# =============================================================================

async def run_test(args):
    """Test enrichment on a few films using real-time API with prompt caching."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    resolved = load_json(RESOLVED_PATH)
    enriched = load_json(ENRICHED_PATH)
    print(f"Loaded {len(resolved)} resolved, {len(enriched)} already enriched")

    # Select films to test
    if args.film_ids:
        # Specific tmdb_ids requested
        target_ids = set(int(x) for x in args.film_ids.split(","))
        films = [f for f in resolved if f.get("film", {}).get("tmdb_id") in target_ids]
        if not films:
            print(f"Error: No films found with tmdb_ids {target_ids}")
            sys.exit(1)
    else:
        unenriched = get_unenriched_films(resolved, enriched)
        films = unenriched[:args.test]

    print(f"\nTesting enrichment on {len(films)} films (real-time API + prompt caching):\n")

    system_prompt = build_system_prompt()
    client = anthropic.AsyncAnthropic(api_key=api_key)
    model = args.model

    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_creation = 0
    results = []

    for i, film_data in enumerate(films):
        title = film_data.get("film", {}).get("original_title", "Unknown")
        tmdb_id = film_data.get("film", {}).get("tmdb_id", "?")
        print(f"  [{i+1}/{len(films)}] {title} (tmdb={tmdb_id})")

        user_prompt = build_user_prompt(film_data)

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.3,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Track token usage
            usage = response.usage
            input_tok = getattr(usage, "input_tokens", 0)
            output_tok = getattr(usage, "output_tokens", 0)
            cache_read = getattr(usage, "cache_read_input_tokens", 0)
            cache_create = getattr(usage, "cache_creation_input_tokens", 0)

            total_input += input_tok
            total_output += output_tok
            total_cache_read += cache_read
            total_cache_creation += cache_create

            text = response.content[0].text.strip()
            enrichment = parse_claude_json(text)
            enrichment = validate_enrichment(enrichment)

            # Show summary
            cats = enrichment.get("categories", [])
            themes = enrichment.get("themes", [])[:5]
            awards_count = len(enrichment.get("awards", []))
            print(f"    Categories: {cats}")
            print(f"    Themes: {themes}{'...' if len(enrichment.get('themes', [])) > 5 else ''}")
            print(f"    Awards: {awards_count}")
            print(f"    Tokens: in={input_tok} out={output_tok} cache_read={cache_read} cache_create={cache_create}")

            results.append({**film_data, "enrichment": enrichment})

        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({**film_data, "enrichment_error": str(e)})

        if i < len(films) - 1:
            await asyncio.sleep(0.5)

    # Cost summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Films tested:        {len(films)}")
    print(f"Input tokens:        {total_input:,}")
    print(f"Output tokens:       {total_output:,}")
    print(f"Cache read tokens:   {total_cache_read:,}")
    print(f"Cache create tokens: {total_cache_creation:,}")

    # Real-time cost
    cost_input = (total_input - total_cache_read - total_cache_creation) * SONNET_INPUT_PRICE / 1_000_000
    cost_output = total_output * SONNET_OUTPUT_PRICE / 1_000_000
    cost_cache_read = total_cache_read * SONNET_CACHE_READ_PRICE / 1_000_000
    cost_cache_create = total_cache_creation * SONNET_CACHE_WRITE_PRICE / 1_000_000
    total_cost = cost_input + cost_output + cost_cache_read + cost_cache_create
    print(f"\nReal-time cost:      ${total_cost:.4f}")

    # Extrapolate for full batch
    unenriched_count = len(get_unenriched_films(resolved, enriched))
    if len(films) > 0:
        per_film_input = total_input / len(films)
        per_film_output = total_output / len(films)
        per_film_cache_read = total_cache_read / len(films)

        # Batch estimate: all films get cache reads (system prompt cached), 50% discount
        est_batch_input = (per_film_input - per_film_cache_read) * unenriched_count
        est_batch_cache_read = per_film_cache_read * unenriched_count
        est_batch_output = per_film_output * unenriched_count
        est_batch_cost = (
            est_batch_input * SONNET_INPUT_PRICE / 1_000_000
            + est_batch_cache_read * SONNET_CACHE_READ_PRICE / 1_000_000
            + est_batch_output * SONNET_OUTPUT_PRICE / 1_000_000
        ) * BATCH_DISCOUNT

        print(f"\nEstimated batch cost for {unenriched_count} remaining films: ${est_batch_cost:.2f}")
        print(f"  (Batch API 50% discount + prompt caching)")

    print(f"{'='*60}")

    # Optionally save test results
    if args.save_test:
        enriched.extend([r for r in results if "enrichment" in r])
        save_json(ENRICHED_PATH, enriched)
        print(f"\nTest results saved to {ENRICHED_PATH}")

    await client.close()


# =============================================================================
# Mode 2: --submit  (Batch API)
# =============================================================================

def run_submit(args):
    """Submit a batch of enrichment requests to the Anthropic Batch API."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    resolved = load_json(RESOLVED_PATH)
    enriched = load_json(ENRICHED_PATH)
    unenriched = get_unenriched_films(resolved, enriched)

    if not unenriched:
        print("All films already enriched. Nothing to submit.")
        return

    # Deduplicate by tmdb_id (resolved_films.json can have dupes from different parsed titles)
    seen_tmdb_ids: set[int] = set()
    deduped: list[dict] = []
    dupes_skipped = 0
    for film_data in unenriched:
        tmdb_id = film_data.get("film", {}).get("tmdb_id")
        if tmdb_id and tmdb_id in seen_tmdb_ids:
            dupes_skipped += 1
            continue
        if tmdb_id:
            seen_tmdb_ids.add(tmdb_id)
        deduped.append(film_data)
    unenriched = deduped

    if dupes_skipped:
        print(f"  Skipped {dupes_skipped} duplicate tmdb_ids")
    print(f"Preparing batch: {len(unenriched)} films to enrich")

    system_prompt = build_system_prompt()
    model = args.model

    # Build batch requests
    requests = []
    id_to_film_key = {}  # Map custom_id → film key for result matching

    for i, film_data in enumerate(unenriched):
        tmdb_id = film_data.get("film", {}).get("tmdb_id")
        custom_id = f"film_{tmdb_id}" if tmdb_id else f"film_idx_{i}"
        user_prompt = build_user_prompt(film_data)

        requests.append({
            "custom_id": custom_id,
            "params": {
                "model": model,
                "max_tokens": 2000,
                "temperature": 0.3,
                "system": [{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                "messages": [{"role": "user", "content": user_prompt}],
            },
        })
        id_to_film_key[custom_id] = build_film_key(film_data)

    # Save mapping for result collection
    save_json(BATCH_STATE_PATH, {
        "id_to_film_key": id_to_film_key,
        "film_count": len(unenriched),
        "model": model,
    })

    # Cost estimate
    est_input_per = 3500  # system prompt (~3000) + user prompt (~500)
    est_output_per = 800
    est_cache_per = 3000  # system prompt portion that gets cached
    est_uncached_per = est_input_per - est_cache_per

    total_input_cost = len(unenriched) * est_uncached_per * SONNET_INPUT_PRICE / 1_000_000
    total_cache_cost = len(unenriched) * est_cache_per * SONNET_CACHE_READ_PRICE / 1_000_000
    total_output_cost = len(unenriched) * est_output_per * SONNET_OUTPUT_PRICE / 1_000_000
    est_total = (total_input_cost + total_cache_cost + total_output_cost) * BATCH_DISCOUNT

    print(f"\nEstimated cost: ${est_total:.2f}")
    print(f"  ({len(unenriched)} films × Sonnet 4 × Batch 50% discount + prompt caching)")
    print(f"  Results available within 24 hours.\n")

    if not args.yes:
        confirm = input("Submit batch? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    print("Submitting batch...")
    client = anthropic.Anthropic(api_key=api_key)

    batch = client.messages.batches.create(requests=requests)

    # Save batch ID
    state = load_json(BATCH_STATE_PATH)
    if not isinstance(state, dict):
        state = {}
    state["batch_id"] = batch.id
    state["submitted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_json(BATCH_STATE_PATH, state)

    print(f"\nBatch submitted successfully!")
    print(f"  Batch ID: {batch.id}")
    print(f"  Status:   {batch.processing_status}")
    print(f"  Requests: {len(requests)}")
    print(f"\nCheck status with:")
    print(f"  python scripts/claude_batch_enrichment.py --status {batch.id}")
    print(f"\nCollect results when done:")
    print(f"  python scripts/claude_batch_enrichment.py --collect {batch.id}")


# =============================================================================
# Mode 3: --status BATCH_ID
# =============================================================================

def run_status(args):
    """Check the status of a submitted batch."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    batch = client.messages.batches.retrieve(args.status)

    print(f"Batch ID:    {batch.id}")
    print(f"Status:      {batch.processing_status}")
    print(f"Created:     {batch.created_at}")

    counts = batch.request_counts
    print(f"\nRequest counts:")
    print(f"  Processing: {counts.processing}")
    print(f"  Succeeded:  {counts.succeeded}")
    print(f"  Errored:    {counts.errored}")
    print(f"  Canceled:   {counts.canceled}")
    print(f"  Expired:    {counts.expired}")

    total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
    if total > 0:
        pct = 100 * (counts.succeeded + counts.errored + counts.canceled + counts.expired) / total
        print(f"\n  Progress: {pct:.1f}% complete")

    if batch.processing_status == "ended":
        print(f"\nBatch complete! Collect results with:")
        print(f"  python scripts/claude_batch_enrichment.py --collect {batch.id}")


# =============================================================================
# Mode 4: --collect BATCH_ID
# =============================================================================

def run_collect(args):
    """Download batch results and merge into enriched_films.json."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Check status first
    batch = client.messages.batches.retrieve(args.collect)
    if batch.processing_status != "ended":
        print(f"Batch status: {batch.processing_status}")
        print("Wait for the batch to complete before collecting results.")
        return

    print(f"Batch {batch.id} is complete. Downloading results...")

    # Load resolved films for matching
    resolved = load_json(RESOLVED_PATH)
    resolved_by_key: dict[str, dict] = {}
    for film in resolved:
        resolved_by_key[build_film_key(film)] = film

    # Also build tmdb_id → film mapping for custom_id matching
    resolved_by_tmdb: dict[str, dict] = {}
    for film in resolved:
        tmdb_id = film.get("film", {}).get("tmdb_id")
        if tmdb_id:
            resolved_by_tmdb[f"film_{tmdb_id}"] = film

    # Load existing enriched
    enriched = load_json(ENRICHED_PATH)
    enriched_keys = set(build_film_key(ef) for ef in enriched)

    # Process results
    succeeded = 0
    errored = 0
    review_queue = []

    for result in client.messages.batches.results(args.collect):
        custom_id = result.custom_id

        # Find the original film data
        film_data = resolved_by_tmdb.get(custom_id)
        if not film_data:
            logger.warning("No film found for custom_id=%s", custom_id)
            errored += 1
            continue

        film_key = build_film_key(film_data)
        if film_key in enriched_keys:
            continue  # Already enriched (e.g., from test run)

        if result.result.type == "succeeded":
            try:
                text = result.result.message.content[0].text.strip()
                enrichment = parse_claude_json(text)
                enrichment = validate_enrichment(enrichment)

                enriched_film = {**film_data, "enrichment": enrichment}
                enriched.append(enriched_film)
                enriched_keys.add(film_key)
                succeeded += 1

                # Flag for review if low confidence
                confidence = enrichment.get("confidence", {})
                needs_review = any(
                    isinstance(s, (int, float)) and s < 0.6
                    for s in confidence.values()
                )
                if needs_review or enrichment.get("new_values_suggested"):
                    review_queue.append(enriched_film)

            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.error("Failed to parse result for %s: %s", custom_id, e)
                review_queue.append({**film_data, "enrichment_error": str(e)})
                errored += 1

        elif result.result.type == "errored":
            error_msg = str(result.result.error) if hasattr(result.result, "error") else "Unknown error"
            logger.error("Batch error for %s: %s", custom_id, error_msg)
            review_queue.append({**film_data, "enrichment_error": error_msg})
            errored += 1

        else:
            # expired or canceled
            logger.warning("Result %s has type=%s", custom_id, result.result.type)
            errored += 1

    # Save
    save_json(ENRICHED_PATH, enriched)
    save_json(REVIEW_PATH, review_queue)

    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Succeeded:       {succeeded}")
    print(f"Errored:         {errored}")
    print(f"Flagged review:  {len(review_queue)}")
    print(f"Total enriched:  {len(enriched)}")
    print(f"\nSaved to: {ENRICHED_PATH}")
    if review_queue:
        print(f"Review queue: {REVIEW_PATH}")
    print(f"{'='*60}")


# =============================================================================
# Main
# =============================================================================

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Batch Claude enrichment with prompt caching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Test on 5 random unenriched films:
    python scripts/claude_batch_enrichment.py --test 5

  Test on specific films (by tmdb_id):
    python scripts/claude_batch_enrichment.py --test 3 --film-ids 775,550,680

  Test and save results to enriched_films.json:
    python scripts/claude_batch_enrichment.py --test 5 --save-test

  Submit full batch:
    python scripts/claude_batch_enrichment.py --submit

  Check batch status:
    python scripts/claude_batch_enrichment.py --status msgbatch_abc123

  Collect results:
    python scripts/claude_batch_enrichment.py --collect msgbatch_abc123
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", type=int, metavar="N", help="Test N films via real-time API with caching")
    group.add_argument("--submit", action="store_true", help="Submit batch to Anthropic Batch API")
    group.add_argument("--status", type=str, metavar="BATCH_ID", help="Check batch status")
    group.add_argument("--collect", type=str, metavar="BATCH_ID", help="Collect batch results")

    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model (default: claude-sonnet-4-6)")
    parser.add_argument("--film-ids", type=str, help="Comma-separated tmdb_ids for --test (e.g., 775,550,680)")
    parser.add_argument("--save-test", action="store_true", help="Save test results to enriched_films.json")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt for --submit")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.test:
        asyncio.run(run_test(args))
    elif args.submit:
        run_submit(args)
    elif args.status:
        run_status(args)
    elif args.collect:
        run_collect(args)


if __name__ == "__main__":
    main()
