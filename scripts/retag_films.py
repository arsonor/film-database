"""
Re-tag harness for the whole library (Step 24 build, Step 25 execution).

Four separate commands. `generate` never writes to the database; `apply` never
calls the API.

Usage:
    # 1. Snapshot the seven tag junctions (queryable rollback)
    python scripts/retag_films.py snapshot

    # 2. Generate enrichments (real-time API, JSONL output, DB untouched)
    python scripts/retag_films.py generate --sample scripts/data/retag/sample.txt
    python scripts/retag_films.py generate --sample sample.txt --sample-subset 15
    python scripts/retag_films.py generate --all --limit 3
    python scripts/retag_films.py generate --all --resume

    # 2b. Batch API variant (50% discount, ~24h turnaround)
    python scripts/retag_films.py generate --all --batch
    python scripts/retag_films.py generate --batch-status msgbatch_abc123
    python scripts/retag_films.py generate --batch-collect msgbatch_abc123

    # 3. Diff proposed tags against the live DB (report only, touches nothing)
    python scripts/retag_films.py diff

    # 4. Apply (dry-run by default; --commit to write; union mode by default)
    python scripts/retag_films.py apply                       # dry-run, union
    python scripts/retag_films.py apply --commit              # union: gains + weights, no deletes
    python scripts/retag_films.py apply --commit --mode replace
    python scripts/retag_films.py apply --commit --film-id 42

    # 5. Approve deferred removals from loss_review.md (written by union apply)
    python scripts/retag_films.py apply --commit --remove-tag "themes:fight"

Sample file format: one film per line, either a bare film_id or `Title (year)`.
`#` starts a comment (whole-line or trailing); blank lines are skipped. Titles
resolve against film.original_title and film_language.film_title; an ambiguous
title aborts with the candidates listed.

The three reference films (few-shot examples in the prompt) are excluded by
default — re-tagging a film whose validated answer is in the prompt is circular.
Override with --include-reference.

Merge policy on apply (PLAN.md Step 24, amended by Step 24.1): the default is
**union** — gains are inserted with weights (100 = defining, 50 = secondary),
weights are updated on existing tags the model re-proposed, and nothing is
deleted; removals are grouped by tag into loss_review.md and approved
individually with --remove-tag. `--mode replace` keeps the original
full-replace behaviour. In both modes film_period rows with
time_context.sort_order < 100 ("Years & eras" — Martin hand-corrected) are
never written or deleted from model output, and `franchise` is derived from
film.tmdb_collection_id rather than model-assigned. Awards, Source and
Geography are NOT applied — the enrichment carries them in the JSONL for later
use, but the re-tag touches tags only.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.claude_enricher import (  # noqa: E402
    DEFAULT_ENRICHMENT_MODEL,
    ENRICHMENT_SYSTEM_PROMPT,
    ClaudeEnricher,
)
from app.services.taxonomy_config import DERIVED_TAGS, REFERENCE_EXAMPLES  # noqa: E402
from app.services.tmdb_mapper import TMDBMapper  # noqa: E402
from app.services.tmdb_service import TMDBService  # noqa: E402

from _pricing import (  # noqa: E402
    BATCH_DISCOUNT,
    CACHE_READ_MULT,
    prices_for,
    totals_cost,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Paths & constants
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data" / "retag"
TMDB_CACHE_DIR = DATA_DIR / "tmdb"
ENRICHED_JSONL = DATA_DIR / "enriched.jsonl"
BATCH_STATE_PATH = DATA_DIR / "batch_state.json"
DIFF_REPORT_MD = DATA_DIR / "diff_report.md"
DIFF_REPORT_JSON = DATA_DIR / "diff_report.json"
LOSS_REVIEW_MD = DATA_DIR / "loss_review.md"

# (enrichment key, junction table, junction fk, lookup table, lookup pk, name column)
DIMENSIONS = [
    ("categories",        "film_genre",             "category_id",          "category",          "category_id",          "category_name"),
    ("themes",            "film_theme",             "theme_context_id",     "theme_context",     "theme_context_id",     "theme_name"),
    ("cinema_type",       "film_technique",         "cinema_type_id",       "cinema_type",       "cinema_type_id",       "technique_name"),
    ("character_context", "film_character_context", "character_context_id", "character_context", "character_context_id", "context_name"),
    ("atmosphere",        "film_atmosphere",        "atmosphere_id",        "atmosphere",        "atmosphere_id",        "atmosphere_name"),
    ("time_context",      "film_period",            "time_context_id",      "time_context",      "time_context_id",      "time_period"),
    ("place_environment", "film_place",             "place_context_id",     "place_context",     "place_context_id",     "environment"),
]

DIM_LABELS = {
    "categories": "Genre",
    "themes": "Theme",
    "cinema_type": "Cinema Type",
    "character_context": "Character",
    "atmosphere": "Atmosphere",
    "time_context": "Time Period",
    "place_environment": "Place",
}

JUNCTIONS = [d[1] for d in DIMENSIONS]

# Diff alarm buckets, keyed by a tag's BEFORE count (see PLAN.md Step 25).
COLD_START_MAX = 10       # before < 10: growth is the goal, no alarm...
COLD_START_CEILING = 800  # ...unless it lands above ~800 films (definition too loose)
SPARSE_MAX = 50           # 10-49: report only
ESTABLISHED_LOSS_FRAC = 0.5    # alarm on losing >50% of an established tag's films
ESTABLISHED_GAIN_RATIO = 2.5   # alarm on gaining >2.5x AND...
ESTABLISHED_GAIN_ABS = 100     # ...more than 100 films in absolute terms

# Weight distribution flags (provisional — recalibrated from the sample pass).
DEFINING_BAND = (0.30, 0.50)
DEFINING_FLAG_HIGH = 0.70  # distinction has collapsed
DEFINING_FLAG_LOW = 0.15   # over-strict


# =============================================================================
# Shared helpers
# =============================================================================

def get_dsn() -> str:
    db_url = os.getenv("DATABASE_URL", "")
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    if not dsn:
        print("Error: DATABASE_URL not set.")
        sys.exit(1)
    return dsn


def get_api_key() -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    return api_key


def load_jsonl(path: Path) -> dict[int, dict]:
    """Load enriched.jsonl as {film_id: entry}; later lines win."""
    entries: dict[int, dict] = {}
    if not path.exists():
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries[int(entry["film_id"])] = entry
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning("Skipping bad JSONL line %d: %s", lineno, e)
    return entries


def append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def cache_control_1h() -> tuple[dict, bool]:
    """Cache-control param with a 1-hour TTL if the installed SDK supports it.

    A 4048-film batch will not stay inside a 5-minute window, so cache misses
    across the run are the single biggest cost risk. Returns (param, is_1h).
    """
    try:
        from anthropic.types import CacheControlEphemeralParam
        if "ttl" in getattr(CacheControlEphemeralParam, "__annotations__", {}):
            return {"type": "ephemeral", "ttl": "1h"}, True
    except Exception:  # pragma: no cover - very old SDK
        pass
    return {"type": "ephemeral"}, False


async def resolve_reference_film_ids(conn: asyncpg.Connection) -> dict[int, str]:
    """Resolve the three REFERENCE_EXAMPLES films to film_ids (title+year)."""
    resolved: dict[int, str] = {}
    for ref in REFERENCE_EXAMPLES.values():
        rows = await conn.fetch(
            """
            SELECT DISTINCT f.film_id
            FROM film f
            LEFT JOIN film_language fl ON fl.film_id = f.film_id
            WHERE (lower(f.original_title) = lower($1) OR lower(fl.film_title) = lower($1))
              AND f.first_release_date IS NOT NULL
              AND EXTRACT(YEAR FROM f.first_release_date)::int = $2
            """,
            ref["title"], ref["year"],
        )
        if len(rows) == 1:
            resolved[rows[0]["film_id"]] = f"{ref['title']} ({ref['year']})"
        elif len(rows) > 1:
            logger.warning(
                "Reference film %r (%s) matched %d rows — excluding all of them",
                ref["title"], ref["year"], len(rows),
            )
            for r in rows:
                resolved[r["film_id"]] = f"{ref['title']} ({ref['year']})"
    return resolved


# =============================================================================
# Command: snapshot
# =============================================================================

async def cmd_snapshot(args) -> None:
    conn = await asyncpg.connect(get_dsn())
    try:
        existing = []
        for j in JUNCTIONS:
            if await conn.fetchval("SELECT to_regclass($1)", f"{j}_pre_retag"):
                existing.append(f"{j}_pre_retag")

        if existing and not args.yes:
            print("A previous snapshot exists and will be DISCARDED:")
            for t in existing:
                print(f"  - {t}")
            confirm = input("Overwrite it? [y/N] ").strip().lower()
            if confirm != "y":
                print("Aborted.")
                return

        print("Snapshotting the seven tag junctions...\n")
        print(f"  {'junction':<26} {'live rows':>10} {'snapshot rows':>14}")
        for j in JUNCTIONS:
            await conn.execute(f"DROP TABLE IF EXISTS {j}_pre_retag")
            await conn.execute(f"CREATE TABLE {j}_pre_retag AS SELECT * FROM {j}")
            live = await conn.fetchval(f"SELECT count(*) FROM {j}")
            snap = await conn.fetchval(f"SELECT count(*) FROM {j}_pre_retag")
            marker = "" if live == snap else "  <-- MISMATCH"
            print(f"  {j:<26} {live:>10,} {snap:>14,}{marker}")

        stamp = datetime.now().strftime("%Y%m%d")
        print("\nRun this pg_dump alongside (file-level backup of the whole DB):")
        print(f"  pg_dump -U postgres -d film_database -F c -f backup_pre_retag_{stamp}.dump")
        print("\nRestore procedure (plain SQL, per junction):")
        print("  -- whole junction:")
        print("  BEGIN; DELETE FROM film_theme;")
        print("  INSERT INTO film_theme SELECT * FROM film_theme_pre_retag; COMMIT;")
        print("  -- one film:")
        print("  BEGIN; DELETE FROM film_theme WHERE film_id = 42;")
        print("  INSERT INTO film_theme SELECT * FROM film_theme_pre_retag WHERE film_id = 42; COMMIT;")
        print("  -- same pattern for:", ", ".join(JUNCTIONS))
        print("\nFull-DB fallback:")
        print(f"  pg_restore -U postgres -d film_database --clean backup_pre_retag_{stamp}.dump")
    finally:
        await conn.close()


# =============================================================================
# Command: generate — film selection
# =============================================================================

SAMPLE_TITLE_RE = re.compile(r"^(?P<title>.+?)\s*\((?P<year>\d{4})\)$")


def parse_sample_file(path: Path) -> list[str]:
    """Return the meaningful entries of a sample file (comments stripped)."""
    if not path.exists():
        print(f"Error: sample file not found: {path}")
        sys.exit(1)
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            entries.append(line)
    return entries


async def resolve_sample_entries(conn: asyncpg.Connection, entries: list[str]) -> list[dict]:
    """Resolve sample lines to film rows. Aborts listing every problem found."""
    resolved: list[dict] = []
    problems: list[str] = []

    for entry in entries:
        if entry.isdigit():
            row = await conn.fetchrow(
                "SELECT film_id, tmdb_id, original_title FROM film WHERE film_id = $1",
                int(entry),
            )
            if row:
                resolved.append(dict(row))
            else:
                problems.append(f"film_id {entry}: not in the database")
            continue

        m = SAMPLE_TITLE_RE.match(entry)
        if not m:
            problems.append(f"{entry!r}: not a film_id and not `Title (year)`")
            continue

        title, year = m.group("title"), int(m.group("year"))
        rows = await conn.fetch(
            """
            SELECT DISTINCT f.film_id, f.tmdb_id, f.original_title,
                   EXTRACT(YEAR FROM f.first_release_date)::int AS year
            FROM film f
            LEFT JOIN film_language fl ON fl.film_id = f.film_id
            WHERE (lower(f.original_title) = lower($1) OR lower(fl.film_title) = lower($1))
              AND f.first_release_date IS NOT NULL
              AND EXTRACT(YEAR FROM f.first_release_date)::int = $2
            ORDER BY f.film_id
            """,
            title, year,
        )
        if len(rows) == 1:
            resolved.append({k: rows[0][k] for k in ("film_id", "tmdb_id", "original_title")})
        elif not rows:
            problems.append(f"{entry!r}: no match on original_title or film_language titles")
        else:
            cands = "; ".join(
                f"film_id={r['film_id']} {r['original_title']} ({r['year']})" for r in rows
            )
            problems.append(f"{entry!r}: AMBIGUOUS — {cands}. Use the film_id instead.")

    if problems:
        print("Sample file could not be fully resolved — aborting (nothing generated):")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    # Deduplicate, preserving order
    seen: set[int] = set()
    unique = []
    for r in resolved:
        if r["film_id"] not in seen:
            seen.add(r["film_id"])
            unique.append(r)
    return unique


async def select_films(conn: asyncpg.Connection, args) -> list[dict]:
    """Apply --sample/--all, --sample-subset, reference exclusion, --resume, --limit."""
    if args.sample:
        entries = parse_sample_file(Path(args.sample))
        films = await resolve_sample_entries(conn, entries)
        print(f"Sample file: {len(entries)} entries -> {len(films)} films resolved")
        if args.sample_subset:
            films = films[: args.sample_subset]
            print(f"--sample-subset: keeping the first {len(films)}")
    else:
        rows = await conn.fetch(
            "SELECT film_id, tmdb_id, original_title FROM film ORDER BY film_id"
        )
        films = [dict(r) for r in rows]
        print(f"--all: {len(films)} films in the database")

    if not args.include_reference:
        ref_ids = await resolve_reference_film_ids(conn)
        if ref_ids:
            print("Excluding reference films (few-shot examples in the prompt):")
            for fid, label in sorted(ref_ids.items()):
                print(f"  - film_id={fid}  {label}")
            films = [f for f in films if f["film_id"] not in ref_ids]

    no_tmdb = [f for f in films if not f["tmdb_id"]]
    if no_tmdb:
        print(f"Skipping {len(no_tmdb)} films without a tmdb_id (cannot re-fetch TMDB):")
        for f in no_tmdb[:10]:
            print(f"  - film_id={f['film_id']}  {f['original_title']}")
        if len(no_tmdb) > 10:
            print(f"  ... and {len(no_tmdb) - 10} more")
        films = [f for f in films if f["tmdb_id"]]

    if args.resume:
        done = set(load_jsonl(ENRICHED_JSONL))
        before = len(films)
        films = [f for f in films if f["film_id"] not in done]
        print(f"--resume: skipping {before - len(films)} films already in {ENRICHED_JSONL.name}")

    if args.limit:
        films = films[: args.limit]
        print(f"--limit: keeping the first {len(films)}")

    return films


# =============================================================================
# Command: generate — TMDB payloads and film blocks
# =============================================================================

async def get_mapped_film(
    film: dict, tmdb: TMDBService | None, mapper: TMDBMapper | None
) -> tuple[dict, TMDBService | None, TMDBMapper | None]:
    """TMDB payload for one film: disk cache first, fetch + cache on miss.

    Re-fetching (rather than rebuilding from the DB) is deliberate: TMDB
    keywords are not stored by create_film and are useful tagging signal, and
    it keeps the re-tag input identical in shape to the Add Film input.
    """
    cache_path = TMDB_CACHE_DIR / f"{film['tmdb_id']}.json"
    if cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        if tmdb is None:
            tmdb_key = os.getenv("TMDB_API_KEY")
            if not tmdb_key:
                print("Error: TMDB_API_KEY not set (needed to fetch uncached films).")
                sys.exit(1)
            tmdb = TMDBService(api_key=tmdb_key)
            mapper = TMDBMapper(tmdb)
        en = await tmdb.get_film_details(film["tmdb_id"])
        fr = await tmdb.get_film_details_fr(film["tmdb_id"])
        payload = {"fetched_at": datetime.now(timezone.utc).isoformat(), "en": en, "fr": fr}
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8"
        )

    if mapper is None:
        # Mapper only builds URLs/structures from the payload — a service
        # instance is required by its constructor but no API key is used
        # when everything comes from cache.
        tmdb = tmdb or TMDBService(api_key=os.getenv("TMDB_API_KEY") or "cached-only")
        mapper = TMDBMapper(tmdb)

    mapped = await mapper.map_film_to_db(payload["en"], payload["fr"])
    return mapped, tmdb, mapper


async def get_setting_period_context(
    conn: asyncpg.Connection, film_id: int
) -> dict | None:
    """The film's current Years & eras tags (sort_order < 100) as extra context.

    Factual context only — the known chronological period genuinely helps
    Character/Place/Cinema Type. Existing tags are deliberately NOT passed
    (PLAN.md Step 24 guardrail 4: models shown an existing answer ratify it).
    """
    rows = await conn.fetch(
        """
        SELECT tc.time_period
        FROM film_period fp
        JOIN time_context tc ON tc.time_context_id = fp.time_context_id
        WHERE fp.film_id = $1 AND tc.sort_order < 100
        ORDER BY tc.sort_order
        """,
        film_id,
    )
    if not rows:
        return None
    return {"Setting period": ", ".join(r["time_period"] for r in rows)}


# =============================================================================
# Command: generate — real-time flow
# =============================================================================

async def cmd_generate(args) -> None:
    if args.batch_status:
        run_batch_status(args.batch_status)
        return
    if args.batch_collect:
        run_batch_collect(args)
        return

    if not args.sample and not args.all:
        print("Error: pick a selection — --sample FILE or --all "
              "(or --batch-status/--batch-collect for a running batch).")
        sys.exit(1)

    conn = await asyncpg.connect(get_dsn())
    tmdb: TMDBService | None = None
    mapper: TMDBMapper | None = None
    try:
        films = await select_films(conn, args)
        if not films:
            print("Nothing to generate.")
            return
        print(f"\n{len(films)} films to enrich (model: {args.model})")

        enricher = ClaudeEnricher(api_key=get_api_key(), model=args.model)

        if args.batch:
            await submit_batch(conn, films, enricher, args, tmdb, mapper)
            return

        for i, film in enumerate(films):
            title = film["original_title"]
            print(f"[{i + 1}/{len(films)}] {title} (film_id={film['film_id']})")

            mapped, tmdb, mapper = await get_mapped_film(film, tmdb, mapper)
            extra_context = await get_setting_period_context(conn, film["film_id"])

            before = dict(enricher.usage_totals)
            enrichment = await enricher.enrich_film(mapped, extra_context=extra_context)
            usage = {
                k: enricher.usage_totals[k] - before[k]
                for k in ("input", "output", "cache_read", "cache_write")
            }

            append_jsonl(ENRICHED_JSONL, {
                "film_id": film["film_id"],
                "tmdb_id": film["tmdb_id"],
                "title": title,
                "enrichment": enrichment,
                "usage": usage,
                "model": args.model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

            n_tags = sum(len(enrichment.get(d, [])) for d, *_ in DIMENSIONS)
            n_def = sum(len(v) for v in enrichment.get("defining", {}).values())
            ratio = f"{n_def / n_tags * 100:.0f}%" if n_tags else "n/a"
            u = enricher.usage_totals
            cached_in = u["cache_read"] + u["cache_write"]
            hit_rate = (u["cache_read"] / cached_in * 100) if cached_in else 0.0
            spent = totals_cost(args.model, u)
            print(f"    tags={n_tags} defining={n_def} ({ratio}) · "
                  f"cache read/write this call: {usage['cache_read']:,}/{usage['cache_write']:,} · "
                  f"running ${spent:.4f} over {u['calls']} calls, hit rate {hit_rate:.1f}%")

            if i < len(films) - 1:
                await asyncio.sleep(0.3)

        _print_generate_summary(enricher, args.model)
    finally:
        await conn.close()
        if tmdb:
            await tmdb.close()


def _print_generate_summary(enricher: ClaudeEnricher, model: str) -> None:
    u = enricher.usage_totals
    if not u["calls"]:
        return
    spent = totals_cost(model, u)
    cached_in = u["cache_read"] + u["cache_write"]
    hit_rate = (u["cache_read"] / cached_in * 100) if cached_in else 0.0
    print(f"\n{'=' * 58}")
    print(f"GENERATE — {u['calls']} calls, ${spent:.4f} (${spent / u['calls']:.4f}/film)")
    print(f"  input (full rate) : {u['input']:>10,} tok")
    print(f"  cache writes      : {u['cache_write']:>10,} tok")
    print(f"  cache reads       : {u['cache_read']:>10,} tok")
    print(f"  output            : {u['output']:>10,} tok")
    print(f"  cache hit rate    : {hit_rate:>9.1f}%")
    print(f"Output: {ENRICHED_JSONL}")


# =============================================================================
# Command: generate --batch (Batch API, ported from claude_batch_enrichment.py)
# =============================================================================

async def submit_batch(conn, films, enricher, args, tmdb, mapper) -> None:
    import anthropic

    cache_control, is_1h = cache_control_1h()
    if is_1h:
        print("Using 1-hour cache TTL (supported by the installed SDK).")
    else:
        print("NOTE: installed anthropic SDK does not support the 1h cache TTL "
              "({'type': 'ephemeral', 'ttl': '1h'}); falling back to the default 5m TTL. "
              "Expect cache misses across a long batch.")

    thinking = enricher._thinking_param()
    extra: dict = {"thinking": thinking} if thinking else {}

    print("Building film blocks (TMDB cache/fetch)...")
    requests = []
    id_to_film: dict[str, dict] = {}
    try:
        for i, film in enumerate(films):
            mapped, tmdb, mapper = await get_mapped_film(film, tmdb, mapper)
            extra_context = await get_setting_period_context(conn, film["film_id"])
            film_block = enricher._build_film_block(mapped, extra_context)
            custom_id = f"film_{film['film_id']}"

            # Same two-breakpoint structure as the real-time path, so batch
            # requests share the prefix cache instead of forking the prompt.
            requests.append({
                "custom_id": custom_id,
                "params": {
                    "model": enricher.model,
                    "max_tokens": 4096,
                    "system": [{
                        "type": "text",
                        "text": ENRICHMENT_SYSTEM_PROMPT,
                        "cache_control": cache_control,
                    }],
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": enricher._static_prefix,
                         "cache_control": cache_control},
                        {"type": "text", "text": film_block},
                    ]}],
                    **extra,
                },
            })
            id_to_film[custom_id] = {
                "film_id": film["film_id"],
                "tmdb_id": film["tmdb_id"],
                "title": film["original_title"],
            }
            if (i + 1) % 100 == 0:
                print(f"  built {i + 1}/{len(films)}")
    finally:
        if tmdb:
            await tmdb.close()

    in_price, out_price = prices_for(enricher.model)
    n = len(requests)
    # Warm-cache estimate: ~200 uncached input + ~21k cached prefix + ~900 output.
    per_film = (
        200 * in_price + 21_000 * in_price * CACHE_READ_MULT + 900 * out_price
    ) / 1_000_000 * BATCH_DISCOUNT
    print(f"\nEstimated batch cost: ${per_film * n:.2f} "
          f"(${per_film:.4f}/film warm-cache, {enricher.model}, Batch 50% discount)")

    if not args.yes:
        confirm = input(f"Submit batch of {n} requests? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    client = anthropic.Anthropic(api_key=get_api_key())
    batch = client.messages.batches.create(requests=requests)

    BATCH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_STATE_PATH.write_text(json.dumps({
        "batch_id": batch.id,
        "model": enricher.model,
        "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "id_to_film": id_to_film,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nBatch submitted: {batch.id} (status {batch.processing_status}, {n} requests)")
    print(f"  python scripts/retag_films.py generate --batch-status {batch.id}")
    print(f"  python scripts/retag_films.py generate --batch-collect {batch.id}")


def run_batch_status(batch_id: str) -> None:
    import anthropic

    client = anthropic.Anthropic(api_key=get_api_key())
    batch = client.messages.batches.retrieve(batch_id)

    print(f"Batch ID: {batch.id}")
    print(f"Status:   {batch.processing_status}")
    print(f"Created:  {batch.created_at}")
    c = batch.request_counts
    print(f"\n  Processing: {c.processing}")
    print(f"  Succeeded:  {c.succeeded}")
    print(f"  Errored:    {c.errored}")
    print(f"  Canceled:   {c.canceled}")
    print(f"  Expired:    {c.expired}")
    total = c.processing + c.succeeded + c.errored + c.canceled + c.expired
    if total:
        done = total - c.processing
        print(f"\n  Progress: {done / total * 100:.1f}%")
    if batch.processing_status == "ended":
        print(f"\nCollect with:\n  python scripts/retag_films.py generate --batch-collect {batch.id}")


def run_batch_collect(args) -> None:
    import anthropic

    if not BATCH_STATE_PATH.exists():
        print(f"Error: {BATCH_STATE_PATH} not found — was this batch submitted by this script?")
        sys.exit(1)
    state = json.loads(BATCH_STATE_PATH.read_text(encoding="utf-8"))
    id_to_film: dict[str, dict] = state.get("id_to_film", {})
    model = state.get("model", args.model)

    client = anthropic.Anthropic(api_key=get_api_key())
    batch = client.messages.batches.retrieve(args.batch_collect)
    if batch.processing_status != "ended":
        print(f"Batch status: {batch.processing_status} — wait for it to end before collecting.")
        return

    # Validation reuses the enricher's validator (no API calls made).
    enricher = ClaudeEnricher(api_key=get_api_key(), model=model)
    existing = set(load_jsonl(ENRICHED_JSONL))

    succeeded = errored = skipped = 0
    for result in client.messages.batches.results(args.batch_collect):
        film = id_to_film.get(result.custom_id)
        if not film:
            logger.warning("No film in batch state for custom_id=%s", result.custom_id)
            errored += 1
            continue
        if film["film_id"] in existing:
            skipped += 1
            continue

        if result.result.type != "succeeded":
            err = getattr(result.result, "error", result.result.type)
            logger.error("Batch result %s: %s", result.custom_id, err)
            errored += 1
            continue

        try:
            message = result.result.message
            text = next(
                (b.text for b in message.content if getattr(b, "type", None) == "text"),
                "",
            ).strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            enrichment = enricher._validate_enrichment(json.loads(text))
            usage = message.usage
            append_jsonl(ENRICHED_JSONL, {
                "film_id": film["film_id"],
                "tmdb_id": film["tmdb_id"],
                "title": film["title"],
                "enrichment": enrichment,
                "usage": {
                    "input": getattr(usage, "input_tokens", 0) or 0,
                    "output": getattr(usage, "output_tokens", 0) or 0,
                    "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
                    "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0,
                },
                "model": model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })
            succeeded += 1
        except (json.JSONDecodeError, StopIteration, AttributeError) as e:
            logger.error("Failed to parse batch result %s: %s", result.custom_id, e)
            errored += 1

    print(f"\nCollected: {succeeded} succeeded, {errored} errored, "
          f"{skipped} already present")
    print(f"Output: {ENRICHED_JSONL}")


# =============================================================================
# Command: diff
# =============================================================================

def _clean_tags(values: list) -> list[str]:
    """Enrichment tag list minus [NEW]-prefixed suggestions."""
    return [v for v in values
            if isinstance(v, str) and v and not v.startswith("[NEW]")]


async def _load_lookup(conn, dim_key: str) -> dict[str, dict]:
    """name -> {id, sort_order} for a dimension's lookup table."""
    _, _, _, lookup, pk, name_col = next(d for d in DIMENSIONS if d[0] == dim_key)
    where = "WHERE historic_subcategory_name IS NULL" if lookup == "category" else ""
    rows = await conn.fetch(
        f"SELECT {pk} AS id, {name_col} AS name, sort_order FROM {lookup} {where}"
    )
    return {r["name"]: {"id": r["id"], "sort_order": r["sort_order"]} for r in rows}


async def _load_current_tags(conn, dim_key: str, film_ids: list[int]) -> dict[int, set[str]]:
    _, junction, fk, lookup, pk, name_col = next(d for d in DIMENSIONS if d[0] == dim_key)
    rows = await conn.fetch(
        f"""
        SELECT j.film_id, l.{name_col} AS name
        FROM {junction} j JOIN {lookup} l ON l.{pk} = j.{fk}
        WHERE j.film_id = ANY($1::int[])
        """,
        film_ids,
    )
    out: dict[int, set[str]] = defaultdict(set)
    for r in rows:
        out[r["film_id"]].add(r["name"])
    return out


async def _load_global_counts(conn, dim_key: str) -> dict[str, int]:
    _, junction, fk, lookup, pk, name_col = next(d for d in DIMENSIONS if d[0] == dim_key)
    rows = await conn.fetch(
        f"""
        SELECT l.{name_col} AS name, count(j.film_id) AS n
        FROM {lookup} l LEFT JOIN {junction} j ON j.{fk} = l.{pk}
        {'WHERE l.historic_subcategory_name IS NULL' if lookup == 'category' else ''}
        GROUP BY l.{name_col}
        """
    )
    return {r["name"]: r["n"] for r in rows}


def _proposed_tags(
    dim_key: str, enrichment: dict, current: set[str],
    lookup: dict[str, dict], has_collection: bool = False,
) -> set[str]:
    """The tag set a film would carry after apply (simulates the merge policy)."""
    tags = {t for t in _clean_tags(enrichment.get(dim_key, [])) if t in lookup}
    tags -= DERIVED_TAGS.get(dim_key, set())
    if dim_key == "cinema_type":
        # 'franchise' is derived from film.tmdb_collection_id, never
        # model-assigned (the validator strips it). Present without a
        # collection id -> shows as a loss, which is the intended review
        # signal (a missing TMDB collection id is not proof of absence).
        if has_collection:
            tags.add("franchise")
        return tags
    if dim_key == "place_environment":
        # 'no particular' is derived too: it means "no other place tag
        # applies", so it appears exactly when the proposal is empty.
        if not tags and "no particular" in lookup:
            tags.add("no particular")
        return tags
    if dim_key != "time_context":
        return tags
    # film_period merge: sort_order < 100 rows are preserved from the DB, and
    # ONLY >= 100 rows come from the enrichment.
    preserved = {t for t in current
                 if t in lookup and lookup[t]["sort_order"] < 100}
    incoming = {t for t in tags if lookup[t]["sort_order"] >= 100}
    return preserved | incoming


async def cmd_diff(args) -> None:
    entries = load_jsonl(ENRICHED_JSONL)
    if not entries:
        print(f"Error: no enrichments found in {ENRICHED_JSONL} — run `generate` first.")
        sys.exit(1)

    conn = await asyncpg.connect(get_dsn())
    try:
        film_ids = list(entries)
        titles = {fid: e.get("title", f"film {fid}") for fid, e in entries.items()}
        print(f"Diffing {len(film_ids)} films against the live DB (touches nothing)...")

        report: dict = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "films_in_scope": len(film_ids),
            "dimensions": {},
            "tags": [],
            "alarms": [],
            "cold_start": [],
            "weight_distribution": {},
            "biggest_movers": [],
            "time_period_check": {},
        }

        per_film_changes: dict[int, dict] = defaultdict(lambda: {"gained": [], "lost": []})
        all_tag_rows = []
        cold_rows = []
        alarm_rows = []
        dim_summaries = {}
        time_check = {"films_checked": 0, "violations": []}

        coll_rows = await conn.fetch(
            "SELECT film_id, tmdb_collection_id FROM film WHERE film_id = ANY($1::int[])",
            film_ids,
        )
        has_collection = {r["film_id"]: r["tmdb_collection_id"] is not None for r in coll_rows}

        for dim_key, *_ in DIMENSIONS:
            lookup = await _load_lookup(conn, dim_key)
            current = await _load_current_tags(conn, dim_key, film_ids)
            global_counts = await _load_global_counts(conn, dim_key)

            gained: dict[str, list[int]] = defaultdict(list)
            lost: dict[str, list[int]] = defaultdict(list)
            scope_before: dict[str, int] = defaultdict(int)
            before_total = after_total = 0

            for fid in film_ids:
                cur = current.get(fid, set())
                new = _proposed_tags(dim_key, entries[fid]["enrichment"], cur, lookup,
                                     has_collection.get(fid, False))
                for t in cur:
                    if t in lookup:
                        scope_before[t] += 1
                before_total += len(cur)
                after_total += len(new)
                for t in new - cur:
                    gained[t].append(fid)
                for t in cur - new:
                    lost[t].append(fid)
                per_film_changes[fid]["gained"].extend(f"{dim_key}:{t}" for t in new - cur)
                per_film_changes[fid]["lost"].extend(f"{dim_key}:{t}" for t in cur - new)

                if dim_key == "time_context":
                    time_check["films_checked"] += 1
                    preserved = {t for t in cur
                                 if t in lookup and lookup[t]["sort_order"] < 100}
                    missing = preserved - new
                    if missing:
                        time_check["violations"].append(
                            {"film_id": fid, "title": titles[fid], "lost": sorted(missing)}
                        )

            dim_summaries[dim_key] = {
                "mean_tags_before": round(before_total / len(film_ids), 2),
                "mean_tags_after": round(after_total / len(film_ids), 2),
            }

            for tag in sorted(lookup):
                before_g = global_counts.get(tag, 0)
                g, l = gained.get(tag, []), lost.get(tag, [])
                after_proj = before_g + len(g) - len(l)
                delta = len(g) - len(l)
                if before_g < COLD_START_MAX:
                    bucket = "cold start"
                elif before_g < SPARSE_MAX:
                    bucket = "sparse"
                else:
                    bucket = "established"

                sb = scope_before.get(tag, 0)
                row = {
                    "dimension": dim_key, "tag": tag, "bucket": bucket,
                    "before": before_g, "after": after_proj, "delta": delta,
                    "scope_before": sb, "scope_after": sb + len(g) - len(l),
                    "gained": len(g), "lost": len(l),
                    "gained_films": [titles[f] for f in g[:5]],
                    "lost_films": [titles[f] for f in l[:5]],
                }
                all_tag_rows.append(row)

                if bucket == "cold start":
                    if g or l or before_g:
                        cold_rows.append(row)
                    if after_proj > COLD_START_CEILING:
                        alarm_rows.append({**row, "reason":
                            f"cold-start tag landed at {after_proj} films "
                            f"(> {COLD_START_CEILING}) — definition far too loose"})
                elif bucket == "established":
                    if len(l) > ESTABLISHED_LOSS_FRAC * before_g:
                        alarm_rows.append({**row, "reason":
                            f"lost {len(l)} of {before_g} films (>50%)"})
                    elif (after_proj > ESTABLISHED_GAIN_RATIO * before_g
                          and after_proj - before_g > ESTABLISHED_GAIN_ABS):
                        alarm_rows.append({**row, "reason":
                            f"grew {before_g} -> {after_proj} "
                            f"(>{ESTABLISHED_GAIN_RATIO}x and >+{ESTABLISHED_GAIN_ABS})"})

        # Weight distribution (from the JSONL, [NEW] excluded like apply does)
        overall_assigned = overall_defining = 0
        weight_by_dim = {}
        for dim_key, *_ in DIMENSIONS:
            assigned = defining = 0
            for e in entries.values():
                tags = _clean_tags(e["enrichment"].get(dim_key, []))
                dset = set(e["enrichment"].get("defining", {}).get(dim_key, []))
                assigned += len(tags)
                defining += len([t for t in tags if t in dset])
            weight_by_dim[dim_key] = {
                "assigned": assigned, "defining": defining,
                "share": round(defining / assigned, 3) if assigned else None,
            }
            overall_assigned += assigned
            overall_defining += defining
        overall_share = overall_defining / overall_assigned if overall_assigned else 0.0

        movers = sorted(
            per_film_changes.items(),
            key=lambda kv: len(kv[1]["gained"]) + len(kv[1]["lost"]),
            reverse=True,
        )[:30]

        # At small scope the library-wide delta is all noise (every row reads
        # ±1 against a base of hundreds) — sort by in-scope movement instead.
        small_scope = len(film_ids) < 200
        if small_scope:
            all_tag_rows.sort(key=lambda r: r["gained"] + r["lost"], reverse=True)
        else:
            all_tag_rows.sort(key=lambda r: abs(r["delta"]), reverse=True)
        report["small_scope"] = small_scope
        report["tags"] = all_tag_rows
        report["alarms"] = alarm_rows
        report["cold_start"] = cold_rows
        report["dimensions"] = dim_summaries
        report["weight_distribution"] = {
            "overall": {"assigned": overall_assigned, "defining": overall_defining,
                        "share": round(overall_share, 3)},
            "per_dimension": weight_by_dim,
        }
        report["biggest_movers"] = [
            {"film_id": fid, "title": titles[fid],
             "gained": ch["gained"], "lost": ch["lost"]}
            for fid, ch in movers
        ]
        report["time_period_check"] = time_check

        DIFF_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        DIFF_REPORT_JSON.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        DIFF_REPORT_MD.write_text(
            _render_diff_md(report, overall_share), encoding="utf-8"
        )

        print(f"\nReport written:\n  {DIFF_REPORT_MD}\n  {DIFF_REPORT_JSON}")
        print(f"\nHeadlines: {len(alarm_rows)} alarms · defining share "
              f"{overall_share * 100:.1f}% (band {DEFINING_BAND[0] * 100:.0f}-"
              f"{DEFINING_BAND[1] * 100:.0f}%) · time-period violations: "
              f"{len(time_check['violations'])}")
    finally:
        await conn.close()


def _render_diff_md(report: dict, overall_share: float) -> str:
    lines = [
        "# Re-tag diff report",
        "",
        f"Generated {report['generated_at']} — {report['films_in_scope']} films in scope.",
        "",
        "> Counts are *projected library totals*: a tag's current count across the whole",
        "> database, adjusted by the gains/losses within the diffed films. Alarm",
        "> thresholds and the 30-50% defining band are **provisional** and get",
        "> recalibrated from the Step 25 sample pass.",
        "",
        "## 1. Cold-start coverage (before < 10)",
        "",
        "Growth is the goal for these tags — the ~38 tags introduced by migration 026",
        "start at zero. Eyeball the sample films for sanity.",
        "",
        "| Dimension | Tag | Before | After | Sample of films gained |",
        "|---|---|---:|---:|---|",
    ]
    for r in report["cold_start"]:
        sample = "; ".join(r["gained_films"]) or "—"
        lines.append(f"| {DIM_LABELS[r['dimension']]} | {r['tag']} | "
                     f"{r['before']} | {r['after']} | {sample} |")

    lines += ["", "## 2. Alarms", ""]
    if not report["alarms"]:
        lines.append("No alarms fired.")
    else:
        lines += [
            "| Dimension | Tag | Before | After | Reason | Examples (gained / lost) |",
            "|---|---|---:|---:|---|---|",
        ]
        for r in report["alarms"]:
            ex = f"+ {'; '.join(r['gained_films']) or '—'} / − {'; '.join(r['lost_films']) or '—'}"
            lines.append(f"| {DIM_LABELS[r['dimension']]} | {r['tag']} | "
                         f"{r['before']} | {r['after']} | {r['reason']} | {ex} |")

    sort_note = ("sorted by in-scope movement — scope is small, the library-wide "
                 "delta is noise" if report.get("small_scope") else "sorted by |delta|")
    lines += [
        "", f"## 3. Per-tag table ({sort_note})", "",
        "| Dimension | Tag | Bucket | Library before | Library after | Delta | In-scope before | In-scope after | Gained | Lost |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in report["tags"]:
        lines.append(f"| {DIM_LABELS[r['dimension']]} | {r['tag']} | {r['bucket']} | "
                     f"{r['before']} | {r['after']} | {r['delta']:+d} | "
                     f"{r['scope_before']} | {r['scope_after']} | "
                     f"{r['gained']} | {r['lost']} |")

    lines += [
        "", "## 4. Per-dimension summary (mean tags per film, scope only)", "",
        "| Dimension | Before | After |", "|---|---:|---:|",
    ]
    for dim, s in report["dimensions"].items():
        lines.append(f"| {DIM_LABELS[dim]} | {s['mean_tags_before']} | {s['mean_tags_after']} |")

    wd = report["weight_distribution"]
    flag = ""
    if overall_share > DEFINING_FLAG_HIGH:
        flag = f" ⚠️ above {DEFINING_FLAG_HIGH * 100:.0f}% — the distinction has collapsed"
    elif overall_share < DEFINING_FLAG_LOW:
        flag = f" ⚠️ below {DEFINING_FLAG_LOW * 100:.0f}% — over-strict"
    lines += [
        "", "## 5. Weight distribution", "",
        f"Overall: **{wd['overall']['defining']} defining of {wd['overall']['assigned']} "
        f"assigned ({overall_share * 100:.1f}%)** — expected band "
        f"{DEFINING_BAND[0] * 100:.0f}-{DEFINING_BAND[1] * 100:.0f}%.{flag}",
        "",
        "| Dimension | Assigned | Defining | Share |", "|---|---:|---:|---:|",
    ]
    for dim, s in wd["per_dimension"].items():
        share = f"{s['share'] * 100:.1f}%" if s["share"] is not None else "n/a"
        lines.append(f"| {DIM_LABELS[dim]} | {s['assigned']} | {s['defining']} | {share} |")

    lines += ["", "## 6. Biggest movers (top 30 films by tag changes)", ""]
    for m in report["biggest_movers"]:
        lines.append(f"- **{m['title']}** (film_id={m['film_id']}): "
                     f"+{len(m['gained'])} / −{len(m['lost'])}")
        if m["gained"]:
            lines.append(f"  - gained: {', '.join(m['gained'])}")
        if m["lost"]:
            lines.append(f"  - lost: {', '.join(m['lost'])}")

    tc = report["time_period_check"]
    lines += ["", "## 7. Time Period check (sort_order < 100 preservation)", ""]
    if tc["violations"]:
        lines.append(f"**{len(tc['violations'])} VIOLATIONS** out of {tc['films_checked']} films:")
        for v in tc["violations"]:
            lines.append(f"- {v['title']} (film_id={v['film_id']}): would lose {', '.join(v['lost'])}")
    else:
        lines.append(f"OK — no `sort_order < 100` row would be lost "
                     f"({tc['films_checked']} films checked).")

    return "\n".join(lines) + "\n"


# =============================================================================
# Command: apply
# =============================================================================

class _DryRunRollback(Exception):
    """Raised to abort the per-film transaction after counting, on --dry-run."""


def _parse_status_count(status: str) -> int:
    """'DELETE 5' / 'INSERT 0 3' -> row count."""
    try:
        return int(status.rsplit(" ", 1)[-1])
    except (ValueError, IndexError):
        return 0


async def _current_dim_tags(conn, dim_key: str, fid: int) -> dict[str, int | None]:
    """name -> weight for one film's current junction rows in a dimension."""
    _, junction, fk, lookup, pk, name_col = next(d for d in DIMENSIONS if d[0] == dim_key)
    rows = await conn.fetch(
        f"""
        SELECT l.{name_col} AS name, j.weight
        FROM {junction} j JOIN {lookup} l ON l.{pk} = j.{fk}
        WHERE j.film_id = $1
        """,
        fid,
    )
    return {r["name"]: r["weight"] for r in rows}


async def _tag_library_count(conn, dim_key: str, tag: str) -> int:
    _, junction, fk, lookup, pk, name_col = next(d for d in DIMENSIONS if d[0] == dim_key)
    extra = "AND l.historic_subcategory_name IS NULL" if lookup == "category" else ""
    return await conn.fetchval(
        f"""
        SELECT count(*) FROM {junction} j JOIN {lookup} l ON l.{pk} = j.{fk}
        WHERE l.{name_col} = $1 {extra}
        """,
        tag,
    )


def _valid_apply_tags(dim_key: str, enrichment: dict, lookup: dict[str, dict]) -> list[str]:
    """Model tags applicable to a dimension: known names, no [NEW], no derived
    tags (`franchise`, `no particular` — written by derivation, not the model),
    and for Time Period only the sort_order >= 100 rows — Years & eras is
    Martin's hand-corrected data and is never written from the model in either
    mode."""
    derived = DERIVED_TAGS.get(dim_key, set())
    tags = [t for t in _clean_tags(enrichment.get(dim_key, []))
            if t in lookup and t not in derived]
    if dim_key == "time_context":
        tags = [t for t in tags if lookup[t]["sort_order"] >= 100]
    return tags


async def _derive_franchise(
    conn, fid: int, lookups: dict, totals: dict,
    losses: dict, derived_losses: set,
) -> None:
    """Part E: `franchise` is set from film.tmdb_collection_id, not the model.

    Missing but derivably present -> insert with weight NULL (derived, not
    model-judged). Present without a collection id -> never deleted here; it
    goes to the loss review as a signal, because TMDB can lack a collection id
    for a film that really is part of a series.
    """
    has_coll = await conn.fetchval(
        "SELECT tmdb_collection_id IS NOT NULL FROM film WHERE film_id = $1", fid)
    fr_id = lookups["cinema_type"]["franchise"]["id"]
    fr_present = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM film_technique WHERE film_id = $1 AND cinema_type_id = $2)",
        fid, fr_id)
    if has_coll and not fr_present:
        await conn.execute(
            "INSERT INTO film_technique (film_id, cinema_type_id, weight) "
            "VALUES ($1, $2, NULL) ON CONFLICT DO NOTHING", fid, fr_id)
        totals["franchise_derived"] += 1
    elif fr_present and not has_coll:
        losses[("cinema_type", "franchise")].append(fid)
        derived_losses.add(("cinema_type", "franchise"))


async def _derive_no_particular(conn, fid: int, lookups: dict, totals: dict) -> None:
    """Part C (Step 24.2): 'no particular' means "no other place tag applies" —
    a fact about the row set, so it is computed, not model-assigned.

    Deliberately asymmetric with `franchise` (insert-only): a missing TMDB
    collection id is not proof a film stands alone, so franchise absence is a
    review signal — but the presence of another place tag IS proof by
    definition that 'no particular' is wrong, so here the removal is automatic.
    Union's no-delete rule protects model judgements; derived values are
    computed and are exempt. Do not "harmonise" the two rules.
    """
    np = lookups["place_environment"].get("no particular")
    if np is None:
        return
    others = await conn.fetchval(
        "SELECT count(*) FROM film_place WHERE film_id = $1 AND place_context_id != $2",
        fid, np["id"])
    np_present = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM film_place WHERE film_id = $1 AND place_context_id = $2)",
        fid, np["id"])
    if others == 0 and not np_present:
        await conn.execute(
            "INSERT INTO film_place (film_id, place_context_id, weight) "
            "VALUES ($1, $2, NULL) ON CONFLICT DO NOTHING", fid, np["id"])
        totals["np_derived_inserts"] += 1
    elif others > 0 and np_present:
        await conn.execute(
            "DELETE FROM film_place WHERE film_id = $1 AND place_context_id = $2",
            fid, np["id"])
        totals["np_derived_removals"] += 1


async def _write_loss_review(conn, losses: dict, derived_losses: set,
                             entries: dict, dry_run: bool) -> None:
    titles = {fid: e.get("title", f"film {fid}") for fid, e in entries.items()}
    LOSS_REVIEW_MD.parent.mkdir(parents=True, exist_ok=True)
    if not losses:
        LOSS_REVIEW_MD.write_text(
            "# Loss review\n\nNo losses — every current tag in scope was "
            "re-proposed by the model.\n", encoding="utf-8")
        print(f"\nLoss review: no losses. ({LOSS_REVIEW_MD})")
        return

    lines = [
        "# Loss review — removals deferred by union apply",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat()} — "
        f"{len(entries)} films in scope.",
        "",
        "Union mode deletes nothing. Each section is a tag the model did not",
        "re-propose for some films in scope; entries marked `(derived)` are the",
        "`franchise` signal (present without a TMDB collection id — possibly a",
        "TMDB gap, not a model judgement). Approve a removal with the printed",
        "command; it deletes the tag from exactly these films, in one transaction.",
        "",
    ]
    for (dim, tag), fids in sorted(losses.items(), key=lambda kv: len(kv[1]), reverse=True):
        cur = await _tag_library_count(conn, dim, tag)
        note = " (derived)" if (dim, tag) in derived_losses else ""
        sample = "; ".join(titles[f] for f in fids[:10])
        lines += [
            f"### {dim}:{tag}{note} — would be removed from {len(fids)} films",
            f"Current count: {cur} → {cur - len(fids)}",
            f"Sample: {sample}",
            f'Approve with: retag_films.py apply --commit --remove-tag "{dim}:{tag}"',
            "",
        ]
    LOSS_REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nLoss review written ({len(losses)} tags): {LOSS_REVIEW_MD}")


async def apply_union(conn, entries: dict, lookups: dict, dry_run: bool) -> None:
    """Default apply mode: insert gains and update weights on tags the model
    re-proposed; delete NOTHING. Existing tags the model did not propose keep
    weight NULL — the model never evaluated them, and writing 50 would invent
    information (consumers already treat weight != 100 as secondary). Their
    removal is deferred to loss_review.md + --remove-tag."""
    totals = {"films": 0, "gains": 0, "weight_updates": 0,
              "defining": 0, "secondary": 0, "franchise_derived": 0,
              "np_derived_inserts": 0, "np_derived_removals": 0,
              "bw_synced": 0, "unknown_tags": 0}
    losses: dict[tuple[str, str], list[int]] = defaultdict(list)
    derived_losses: set[tuple[str, str]] = set()

    for i, (fid, entry) in enumerate(entries.items(), 1):
        enrichment = entry["enrichment"]
        defining = enrichment.get("defining") or {}
        try:
            async with conn.transaction():
                for dim_key, junction, fk, lookup_t, pk, name_col in DIMENSIONS:
                    lookup = lookups[dim_key]
                    raw = _clean_tags(enrichment.get(dim_key, []))
                    unknown = [t for t in raw if t not in lookup]
                    for t in unknown:
                        logger.warning("film %s: unknown %s tag %r skipped", fid, dim_key, t)
                    totals["unknown_tags"] += len(unknown)
                    proposed = set(_valid_apply_tags(dim_key, enrichment, lookup))

                    current = await _current_dim_tags(conn, dim_key, fid)
                    dset = set(defining.get(dim_key, []))

                    for t in sorted(proposed):
                        w = 100 if t in dset else 50
                        if t not in current:
                            await conn.execute(
                                f"INSERT INTO {junction} (film_id, {fk}, weight) "
                                f"VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                                fid, lookup[t]["id"], w)
                            totals["gains"] += 1
                            totals["defining" if w == 100 else "secondary"] += 1
                        elif current[t] != w:
                            # The model re-evaluated an existing tag — record
                            # its judgement.
                            await conn.execute(
                                f"UPDATE {junction} SET weight = $3 "
                                f"WHERE film_id = $1 AND {fk} = $2",
                                fid, lookup[t]["id"], w)
                            totals["weight_updates"] += 1

                    loss_cands = set(current) - proposed
                    if dim_key == "time_context":
                        # Years & eras is preserved policy-side, never a loss.
                        loss_cands = {t for t in loss_cands
                                      if t in lookup and lookup[t]["sort_order"] >= 100}
                    # Derived tags are governed by their derivation rules, not
                    # the loss review.
                    loss_cands -= DERIVED_TAGS.get(dim_key, set())
                    for t in loss_cands:
                        losses[(dim_key, t)].append(fid)

                await _derive_franchise(conn, fid, lookups, totals, losses, derived_losses)
                await _derive_no_particular(conn, fid, lookups, totals)

                # Sync film.color from the 'black and white' tag, as create_film
                # does (sets FALSE when present, never TRUE).
                if "black and white" in _clean_tags(enrichment.get("cinema_type", [])):
                    await conn.execute(
                        "UPDATE film SET color = FALSE WHERE film_id = $1", fid)
                    totals["bw_synced"] += 1

                totals["films"] += 1
                if dry_run:
                    raise _DryRunRollback
        except _DryRunRollback:
            pass

        if i % 50 == 0 or i == len(entries):
            print(f"  [{i}/{len(entries)}] {entry.get('title', fid)}")

    await _write_loss_review(conn, losses, derived_losses, entries, dry_run)

    loss_films = sum(len(v) for v in losses.values())
    print(f"\n{'=' * 58}")
    print(f"APPLY mode=union {'(dry run — rolled back)' if dry_run else '(committed)'}")
    print(f"  films processed    : {totals['films']}")
    print(f"  gains inserted     : {totals['gains']} "
          f"({totals['defining']} defining, {totals['secondary']} secondary)")
    print(f"  weights updated    : {totals['weight_updates']} (existing tags the model re-proposed)")
    print(f"  franchise derived  : {totals['franchise_derived']} inserted from tmdb_collection_id")
    print(f"  'no particular'    : {totals['np_derived_inserts']} derived inserts, "
          f"{totals['np_derived_removals']} derived removals (exempt from no-delete)")
    print(f"  color synced B&W   : {totals['bw_synced']}")
    print(f"  model deletions    : 0 — {loss_films} tag-film losses deferred to loss_review.md")
    if totals["unknown_tags"]:
        print(f"  unknown tags       : {totals['unknown_tags']} skipped (see warnings)")
    print("  untouched          : award, source/film_origin, film_set_place, "
          "film_period rows with sort_order < 100")


async def apply_replace(conn, entries: dict, lookups: dict, dry_run: bool) -> None:
    """Full-replace mode (no longer the default): delete existing junction rows
    and insert the proposed set, preserving film_period rows with
    time_context.sort_order < 100 and never deleting the derived `franchise`."""
    totals = {"films": 0, "deleted": 0, "inserted": 0,
              "defining": 0, "secondary": 0, "franchise_derived": 0,
              "np_derived_inserts": 0, "np_derived_removals": 0,
              "bw_synced": 0, "unknown_tags": 0}
    losses: dict[tuple[str, str], list[int]] = defaultdict(list)
    derived_losses: set[tuple[str, str]] = set()

    fr_id = lookups["cinema_type"]["franchise"]["id"]

    for i, (fid, entry) in enumerate(entries.items(), 1):
        enrichment = entry["enrichment"]
        defining = enrichment.get("defining") or {}
        try:
            async with conn.transaction():
                for dim_key, junction, fk, lookup_t, pk, name_col in DIMENSIONS:
                    lookup = lookups[dim_key]
                    raw = _clean_tags(enrichment.get(dim_key, []))
                    unknown = [t for t in raw if t not in lookup]
                    for t in unknown:
                        logger.warning("film %s: unknown %s tag %r skipped", fid, dim_key, t)
                    totals["unknown_tags"] += len(unknown)
                    tags = _valid_apply_tags(dim_key, enrichment, lookup)

                    if dim_key == "time_context":
                        # Preserve Years & eras (sort_order < 100) — the only
                        # sub-dimension Martin hand-corrected. Replace >= 100.
                        status = await conn.execute(
                            """
                            DELETE FROM film_period
                            WHERE film_id = $1 AND time_context_id IN (
                                SELECT time_context_id FROM time_context
                                WHERE sort_order >= 100)
                            """, fid)
                    elif dim_key == "cinema_type":
                        # 'franchise' is derived data — never deleted here.
                        status = await conn.execute(
                            f"DELETE FROM {junction} WHERE film_id = $1 "
                            f"AND {fk} != $2", fid, fr_id)
                    else:
                        status = await conn.execute(
                            f"DELETE FROM {junction} WHERE film_id = $1", fid)
                    totals["deleted"] += _parse_status_count(status)

                    dset = set(defining.get(dim_key, []))
                    for t in tags:
                        w = 100 if t in dset else 50
                        status = await conn.execute(
                            f"""
                            INSERT INTO {junction} (film_id, {fk}, weight)
                            VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
                            """, fid, lookup[t]["id"], w)
                        n = _parse_status_count(status)
                        totals["inserted"] += n
                        if n:
                            totals["defining" if w == 100 else "secondary"] += 1

                await _derive_franchise(conn, fid, lookups, totals, losses, derived_losses)
                await _derive_no_particular(conn, fid, lookups, totals)

                # Sync film.color from the 'black and white' tag, as create_film
                # does (sets FALSE when present, never TRUE).
                if "black and white" in _clean_tags(enrichment.get("cinema_type", [])):
                    await conn.execute(
                        "UPDATE film SET color = FALSE WHERE film_id = $1", fid)
                    totals["bw_synced"] += 1

                totals["films"] += 1
                if dry_run:
                    raise _DryRunRollback
        except _DryRunRollback:
            pass

        if i % 50 == 0 or i == len(entries):
            print(f"  [{i}/{len(entries)}] {entry.get('title', fid)}")

    if losses:
        await _write_loss_review(conn, losses, derived_losses, entries, dry_run)

    print(f"\n{'=' * 58}")
    print(f"APPLY mode=replace {'(dry run — rolled back)' if dry_run else '(committed)'}")
    print(f"  films processed    : {totals['films']}")
    print(f"  rows deleted       : {totals['deleted']}")
    print(f"  rows inserted      : {totals['inserted']} "
          f"({totals['defining']} defining, {totals['secondary']} secondary)")
    print(f"  franchise derived  : {totals['franchise_derived']} inserted from tmdb_collection_id")
    print(f"  'no particular'    : {totals['np_derived_inserts']} derived inserts, "
          f"{totals['np_derived_removals']} derived removals")
    print(f"  color synced B&W   : {totals['bw_synced']}")
    if totals["unknown_tags"]:
        print(f"  unknown tags       : {totals['unknown_tags']} skipped (see warnings)")
    print("  untouched          : award, source/film_origin, film_set_place, "
          "film_period rows with sort_order < 100, derived franchise rows")


async def run_remove_tags(conn, entries: dict, lookups: dict,
                          specs: list[str], dry_run: bool) -> None:
    """Approve losses from loss_review.md: delete DIM:TAG from exactly the
    films in the current JSONL scope that lost it, in one transaction."""
    parsed: list[tuple[str, str]] = []
    for spec in specs:
        if ":" not in spec:
            print(f"Error: --remove-tag expects DIM:TAG, got {spec!r}")
            sys.exit(1)
        dim, tag = spec.split(":", 1)
        dim, tag = dim.strip(), tag.strip()
        if dim not in lookups:
            print(f"Error: unknown dimension {dim!r} (use one of: {', '.join(lookups)})")
            sys.exit(1)
        if tag not in lookups[dim]:
            print(f"Error: unknown {dim} tag {tag!r}")
            sys.exit(1)
        parsed.append((dim, tag))

    film_ids = list(entries)
    coll_rows = await conn.fetch(
        "SELECT film_id, tmdb_collection_id FROM film WHERE film_id = ANY($1::int[])",
        film_ids)
    has_collection = {r["film_id"]: r["tmdb_collection_id"] is not None for r in coll_rows}
    titles = {fid: e.get("title", f"film {fid}") for fid, e in entries.items()}

    plans: list[tuple[str, str, list[int]]] = []
    for dim, tag in parsed:
        lookup = lookups[dim]
        targets = []
        for fid, entry in entries.items():
            current = await _current_dim_tags(conn, dim, fid)
            if tag not in current:
                continue
            proposed = _proposed_tags(dim, entry["enrichment"], set(current),
                                      lookup, has_collection.get(fid, False))
            if tag not in proposed:
                targets.append(fid)
        plans.append((dim, tag, targets))

    for dim, tag, targets in plans:
        print(f"\n{dim}:{tag} — {'would remove' if dry_run else 'removing'} "
              f"from {len(targets)} films:")
        for fid in targets:
            print(f"  - {titles[fid]} (film_id={fid})")

    if dry_run:
        print("\nDry run — nothing deleted. Re-run with --commit to execute.")
        return

    async with conn.transaction():
        for dim, tag, targets in plans:
            if not targets:
                continue
            _, junction, fk, *_rest = next(d for d in DIMENSIONS if d[0] == dim)
            status = await conn.execute(
                f"DELETE FROM {junction} WHERE film_id = ANY($1::int[]) AND {fk} = $2",
                targets, lookups[dim][tag]["id"])
            n = _parse_status_count(status)
            logger.info("Removed %s:%s from %d films: %s", dim, tag, n, targets)
    print("\nRemovals committed.")


async def cmd_apply(args) -> None:
    entries = load_jsonl(ENRICHED_JSONL)
    if not entries:
        print(f"Error: no enrichments found in {ENRICHED_JSONL} — run `generate` first.")
        sys.exit(1)

    if args.film_id:
        missing = [fid for fid in args.film_id if fid not in entries]
        if missing:
            print(f"Error: film_id(s) not in {ENRICHED_JSONL.name}: {missing}")
            sys.exit(1)
        entries = {fid: entries[fid] for fid in args.film_id}
    if args.limit:
        entries = dict(list(entries.items())[: args.limit])

    dry_run = not args.commit

    conn = await asyncpg.connect(get_dsn())
    try:
        lookups = {dim: await _load_lookup(conn, dim) for dim, *_ in DIMENSIONS}

        if args.remove_tag:
            await run_remove_tags(conn, entries, lookups, args.remove_tag, dry_run)
            return

        label = "DRY RUN (no DB writes — use --commit)" if dry_run else "COMMIT"
        print(f"Applying {len(entries)} films — mode={args.mode} — {label}")
        if args.mode == "union":
            await apply_union(conn, entries, lookups, dry_run)
        else:
            await apply_replace(conn, entries, lookups, dry_run)
    finally:
        await conn.close()


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Re-tag harness: snapshot / generate / diff / apply (Step 24/25)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_snap = sub.add_parser("snapshot", help="Snapshot the seven tag junctions")
    p_snap.add_argument("--yes", "-y", action="store_true",
                        help="Overwrite a previous snapshot without asking")

    p_gen = sub.add_parser("generate", help="Generate enrichments (never writes to the DB)")
    p_gen.add_argument("--sample", metavar="FILE",
                       help="Sample file: one film_id or `Title (year)` per line")
    p_gen.add_argument("--all", action="store_true", help="All films in the database")
    p_gen.add_argument("--batch", action="store_true",
                       help="Submit via the Batch API instead of real-time")
    p_gen.add_argument("--batch-status", metavar="ID", help="Check a submitted batch")
    p_gen.add_argument("--batch-collect", metavar="ID",
                       help="Collect a finished batch into the JSONL")
    p_gen.add_argument("--limit", type=int, help="Only the first N selected films")
    p_gen.add_argument("--resume", action="store_true",
                       help="Skip film_ids already in enriched.jsonl")
    p_gen.add_argument("--sample-subset", type=int, metavar="N",
                       help="First N resolved sample entries (fast iteration)")
    p_gen.add_argument("--exclude-reference", dest="include_reference",
                       action="store_false", default=False,
                       help="Skip the three reference films (DEFAULT)")
    p_gen.add_argument("--include-reference", dest="include_reference",
                       action="store_true",
                       help="Re-tag the reference films too (overrides the default)")
    p_gen.add_argument("--model", default=DEFAULT_ENRICHMENT_MODEL,
                       help=f"Claude model (default: {DEFAULT_ENRICHMENT_MODEL})")
    p_gen.add_argument("--yes", "-y", action="store_true",
                       help="Skip the batch submit confirmation")

    sub.add_parser("diff", help="Diff the JSONL against the live DB (touches nothing)")

    p_apply = sub.add_parser("apply", help="Apply the JSONL to the DB (dry-run by default)")
    p_apply.add_argument("--dry-run", action="store_true", default=True,
                         help="Count everything, write nothing (DEFAULT)")
    p_apply.add_argument("--commit", action="store_true", help="Actually write")
    p_apply.add_argument("--mode", choices=["union", "replace"], default="union",
                         help="union (DEFAULT): insert gains + update weights, delete "
                              "nothing, defer removals to loss_review.md. "
                              "replace: full replace (Time Period < 100 preserved)")
    p_apply.add_argument("--remove-tag", action="append", metavar="DIM:TAG",
                         help="Approve a loss_review.md entry: delete DIM:TAG from the "
                              "scope films that lost it (repeatable; needs --commit)")
    p_apply.add_argument("--film-id", type=int, action="append",
                         help="Only this film_id (repeatable)")
    p_apply.add_argument("--limit", type=int, help="Only the first N films in the JSONL")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.command == "snapshot":
        asyncio.run(cmd_snapshot(args))
    elif args.command == "generate":
        asyncio.run(cmd_generate(args))
    elif args.command == "diff":
        asyncio.run(cmd_diff(args))
    elif args.command == "apply":
        asyncio.run(cmd_apply(args))


if __name__ == "__main__":
    main()
