"""
Seed the 3 reference films into the PostgreSQL database.

Validates the entire pipeline end-to-end. Works in two modes:
- Full mode (default): uses TMDB + Claude APIs to fetch and enrich data
- Offline mode (--offline): uses pre-built fallback data, no API keys needed

Usage:
    python scripts/seed_reference_films.py                # Full mode
    python scripts/seed_reference_films.py --offline      # Offline mode
    python scripts/seed_reference_films.py --no-db        # Test pipeline only, skip DB
    python scripts/seed_reference_films.py --reset        # Delete 3 films, then re-insert
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.tmdb_service import TMDBService, TMDBError  # noqa: E402
from app.services.tmdb_mapper import TMDBMapper  # noqa: E402
from app.services.claude_enricher import ClaudeEnricher  # noqa: E402
from app.services.taxonomy_config import REFERENCE_EXAMPLES  # noqa: E402

# Import DBInserter class directly
sys.path.insert(0, str(Path(__file__).parent))
from db_inserter import DBInserter  # noqa: E402

logger = logging.getLogger(__name__)

REFERENCE_TMDB_IDS = [62, 3405, 1018]
FALLBACK_PATH = Path(__file__).parent / "data" / "reference_films_fallback.json"
SCHEMA_PATH = Path(__file__).parent.parent / "database" / "schema.sql"
SEED_PATH = Path(__file__).parent.parent / "database" / "seed_taxonomy.sql"

REFERENCE_FILMS = [
    {"key": "2001", "title": "2001: A Space Odyssey", "year": 1968, "tmdb_id": 62},
    {"key": "la_haine", "title": "La Haine", "year": 1995, "tmdb_id": 3405},
    {"key": "mulholland_drive", "title": "Mulholland Drive", "year": 2001, "tmdb_id": 1018},
]


def print_header(text_str: str):
    print(f"\n{'=' * 60}")
    print(f"  {text_str}")
    print(f"{'=' * 60}")


def print_step(num: int, text_str: str):
    print(f"\n  [{num}] {text_str}")


def print_ok(text_str: str):
    print(f"      OK: {text_str}")


def print_fail(text_str: str):
    print(f"      FAIL: {text_str}")


def print_info(text_str: str):
    print(f"      {text_str}")


# =============================================================================
# Database helpers
# =============================================================================

async def check_db_connection(database_url: str) -> bool:
    """Test database connectivity."""
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return False


async def check_schema_exists(database_url: str) -> bool:
    """Check if the film table exists (proxy for schema being loaded)."""
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'film')"
            ))
            exists = result.scalar()
        await engine.dispose()
        return bool(exists)
    except Exception:
        return False


async def run_sql_file(database_url: str, sql_path: Path):
    """Execute a SQL file against the database."""
    sql = sql_path.read_text(encoding="utf-8")
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        # Split on semicolons but handle the trigger function definition
        # which contains semicolons inside $$ blocks
        await conn.execute(text(sql))
    await engine.dispose()


async def setup_schema(database_url: str):
    """Run schema.sql and seed_taxonomy.sql."""
    print_info("Running schema.sql...")
    engine = create_async_engine(database_url, echo=False)

    # Read and execute schema
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with engine.begin() as conn:
        # Execute statements one by one to handle PL/pgSQL blocks
        # Split carefully: the trigger function has $$ delimiters
        statements = _split_sql(schema_sql)
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    # Some statements like CREATE INDEX IF NOT EXISTS may warn
                    logger.debug("SQL statement note: %s", e)

    print_ok("schema.sql executed")

    # Seed taxonomy
    print_info("Running seed_taxonomy.sql...")
    seed_sql = SEED_PATH.read_text(encoding="utf-8")
    async with engine.begin() as conn:
        statements = _split_sql(seed_sql)
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    logger.debug("SQL statement note: %s", e)

    print_ok("seed_taxonomy.sql executed")
    await engine.dispose()


def _split_sql(sql: str) -> list[str]:
    """
    Split SQL text into individual statements, respecting $$ blocks.
    """
    statements = []
    current = ""
    in_dollar_block = False

    for line in sql.split("\n"):
        stripped = line.strip()

        # Track $$ blocks (PL/pgSQL function bodies)
        if "$$" in stripped:
            count = stripped.count("$$")
            if count % 2 == 1:
                in_dollar_block = not in_dollar_block

        current += line + "\n"

        # End of statement (semicolon outside $$ block)
        if stripped.endswith(";") and not in_dollar_block:
            statements.append(current.strip())
            current = ""

    if current.strip():
        statements.append(current.strip())

    return statements


async def reset_reference_films(database_url: str):
    """Delete the 3 reference films from the database."""
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        result = await conn.execute(
            text("DELETE FROM film WHERE tmdb_id IN (62, 3405, 1018)")
        )
        print_info(f"Deleted {result.rowcount} reference films from database")
    await engine.dispose()


# =============================================================================
# Pipeline: Full mode
# =============================================================================

async def run_full_mode(database_url: str | None, skip_db: bool):
    """Full pipeline: TMDB fetch -> Claude enrich -> DB insert."""
    tmdb_key = os.getenv("TMDB_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not tmdb_key:
        print_fail("TMDB_API_KEY not set. Use --offline mode or set the key in .env")
        return False
    if not anthropic_key:
        print_fail("ANTHROPIC_API_KEY not set. Use --offline mode or set the key in .env")
        return False

    print_ok("TMDB API key found")
    print_ok("Anthropic API key found")

    films_data = []

    async with TMDBService(tmdb_key) as tmdb:
        mapper = TMDBMapper(tmdb)
        enricher = ClaudeEnricher(api_key=anthropic_key)

        for ref in REFERENCE_FILMS:
            print_step(REFERENCE_FILMS.index(ref) + 1, f"Processing: {ref['title']} ({ref['year']})")

            # Step A: Resolve from TMDB
            print_info("Resolving from TMDB...")
            try:
                details = await tmdb.resolve_title(ref["title"], year=ref["year"])
                if not details:
                    print_fail(f"Could not resolve '{ref['title']}' from TMDB")
                    continue
                print_ok(f"TMDB match: tmdb_id={details['tmdb_id']}")
            except TMDBError as e:
                print_fail(f"TMDB error: {e}")
                continue

            # Get French details
            fr_details = None
            try:
                fr_details = await tmdb.get_film_details_fr(details["tmdb_id"])
            except TMDBError:
                pass

            # Step B: Map to DB structure
            print_info("Mapping TMDB data...")
            mapped = await mapper.map_film_to_db(details, fr_details)
            print_ok(f"Mapped: {len(mapped['cast'])} cast, {len(mapped['crew'])} crew")

            # Step C: Enrich with Claude
            print_info("Enriching with Claude...")
            try:
                enrichment = await enricher.enrich_film(mapped)
                print_ok(f"Enrichment complete: {len(enrichment.get('themes', []))} themes, "
                         f"{len(enrichment.get('atmosphere', []))} atmospheres")
            except Exception as e:
                print_fail(f"Enrichment error: {e}")
                # Fall back to reference enrichment
                ref_data = REFERENCE_EXAMPLES.get(ref["key"], {})
                enrichment = ref_data.get("enrichment", {})
                print_info("Using reference enrichment as fallback")

            # Step D: Compare with expected
            expected = REFERENCE_EXAMPLES.get(ref["key"], {}).get("enrichment", {})
            if expected:
                _print_accuracy(ref["title"], expected, enrichment)

            # Merge
            film_data = {**mapped, "enrichment": enrichment}
            films_data.append(film_data)

    # Step E: Insert into DB
    if not skip_db and database_url:
        await _insert_films(database_url, films_data)

    return True


# =============================================================================
# Pipeline: Offline mode
# =============================================================================

async def run_offline_mode(database_url: str | None, skip_db: bool):
    """Offline pipeline: load fallback data -> DB insert."""
    if not FALLBACK_PATH.exists():
        print_fail(f"Fallback data not found: {FALLBACK_PATH}")
        return False

    with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
        films_data = json.load(f)

    print_ok(f"Loaded {len(films_data)} films from fallback data")

    for film in films_data:
        title = film.get("film", {}).get("original_title", "Unknown")
        enrichment = film.get("enrichment", {})
        themes_count = len(enrichment.get("themes", []))
        atmosphere_count = len(enrichment.get("atmosphere", []))
        cast_count = len(film.get("cast", []))
        print_info(f"{title}: {cast_count} cast, {themes_count} themes, {atmosphere_count} atmospheres")

    if not skip_db and database_url:
        await _insert_films(database_url, films_data)

    return True


# =============================================================================
# DB insertion
# =============================================================================

async def _insert_films(database_url: str, films_data: list[dict]):
    """Insert films into the database using DBInserter."""
    print_step(4, "Inserting into database...")

    inserter = DBInserter(database_url)
    try:
        for film_data in films_data:
            title = film_data.get("film", {}).get("original_title", "Unknown")
            try:
                success = await inserter.insert_film(film_data)
                if success:
                    print_ok(f"Inserted: {title}")
                else:
                    print_fail(f"Skipped: {title}")
            except Exception as e:
                print_fail(f"Error inserting {title}: {e}")
    finally:
        await inserter.close()

    print_info(f"Stats: {inserter.stats['inserted']} inserted, "
               f"{inserter.stats['updated']} updated, "
               f"{inserter.stats['errors']} errors")


# =============================================================================
# Accuracy comparison
# =============================================================================

def _print_accuracy(title: str, expected: dict, actual: dict):
    """Print a brief accuracy comparison between expected and actual enrichment."""
    dims = [
        "categories", "cinema_type", "cultural_movement", "time_context",
        "themes", "characters_type", "character_context", "atmosphere",
        "motivations", "message", "place_environment",
    ]

    total_expected = 0
    total_matched = 0

    for dim in dims:
        exp = set(expected.get(dim, []))
        act = set(actual.get(dim, []))
        matched = exp & act
        total_expected += len(exp)
        total_matched += len(matched)

    accuracy = total_matched / max(total_expected, 1)
    status = "OK" if accuracy >= 0.7 else "LOW"
    print_info(f"Accuracy vs reference: {accuracy:.0%} ({total_matched}/{total_expected} values matched) [{status}]")


# =============================================================================
# Main
# =============================================================================

async def main_async(args):
    load_dotenv()

    print_header("SEED REFERENCE FILMS")

    database_url = os.getenv("DATABASE_URL")
    tmdb_key = os.getenv("TMDB_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # Determine mode
    offline = args.offline
    if not offline and (not tmdb_key or not anthropic_key):
        print_info("API keys not found, switching to offline mode")
        offline = True

    mode = "OFFLINE" if offline else "FULL"
    print_info(f"Mode: {mode}")

    # Check DB connection
    skip_db = args.no_db
    if not skip_db:
        if not database_url:
            print_fail("DATABASE_URL not set in .env")
            print_info("Set DATABASE_URL or use --no-db to skip database insertion")
            sys.exit(1)

        print_step(1, "Checking database connection...")
        if not await check_db_connection(database_url):
            print_fail("Cannot connect to PostgreSQL")
            print_info(f"DATABASE_URL: {database_url[:30]}...")
            print_info("Make sure PostgreSQL is running and the URL is correct")
            sys.exit(1)
        print_ok("Connected to PostgreSQL")

        # Check schema
        print_step(2, "Checking schema...")
        if not await check_schema_exists(database_url):
            print_info("Schema not found, setting up...")
            try:
                await setup_schema(database_url)
            except Exception as e:
                print_fail(f"Schema setup failed: {e}")
                print_info("Try running: python database/setup_db.py")
                sys.exit(1)
        else:
            print_ok("Schema exists")

        # Reset if requested
        if args.reset:
            print_step(2, "Resetting reference films...")
            await reset_reference_films(database_url)
    else:
        print_info("Skipping database (--no-db)")

    # Run pipeline
    print_step(3, f"Running {mode.lower()} pipeline...")
    if offline:
        success = await run_offline_mode(database_url, skip_db)
    else:
        success = await run_full_mode(database_url, skip_db)

    if not success:
        print_header("FAILED")
        sys.exit(1)

    # Run verification if DB was used
    if not skip_db and database_url:
        print_step(5, "Running verification...")
        await _quick_verify(database_url)

    print_header("DONE")


async def _quick_verify(database_url: str):
    """Quick verification of the 3 reference films."""
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # Check films exist
        result = await session.execute(
            text("SELECT original_title, tmdb_id, duration, first_release_date FROM film WHERE tmdb_id IN (62, 3405, 1018) ORDER BY original_title")
        )
        films = result.fetchall()

        if len(films) != 3:
            print_fail(f"Expected 3 films, found {len(films)}")
        else:
            for f in films:
                print_ok(f"{f[0]} (tmdb={f[1]}, {f[2]}min, {f[3]})")

        # Check completeness
        result = await session.execute(text("""
            SELECT f.original_title,
              (SELECT COUNT(*) FROM film_genre fg WHERE fg.film_id = f.film_id) as categories,
              (SELECT COUNT(*) FROM film_theme fth WHERE fth.film_id = f.film_id) as themes,
              (SELECT COUNT(*) FROM film_atmosphere fa WHERE fa.film_id = f.film_id) as atmospheres,
              (SELECT COUNT(*) FROM film_motivation fmo WHERE fmo.film_id = f.film_id) as motivations,
              (SELECT COUNT(*) FROM casting ca WHERE ca.film_id = f.film_id) as cast_count,
              (SELECT COUNT(*) FROM crew c WHERE c.film_id = f.film_id) as crew_count
            FROM film f WHERE f.tmdb_id IN (62, 3405, 1018) ORDER BY f.original_title
        """))
        rows = result.fetchall()
        all_pass = True
        for r in rows:
            title, cats, themes, atmos, motivs, cast_ct, crew_ct = r
            issues = []
            if cats < 2: issues.append(f"categories={cats}<2")
            if themes < 5: issues.append(f"themes={themes}<5")
            if atmos < 3: issues.append(f"atmospheres={atmos}<3")
            if motivs < 3: issues.append(f"motivations={motivs}<3")
            if cast_ct < 5: issues.append(f"cast={cast_ct}<5")
            if crew_ct < 2: issues.append(f"crew={crew_ct}<2")

            if issues:
                print_fail(f"{title}: {', '.join(issues)}")
                all_pass = False
            else:
                print_ok(f"{title}: {cats} categories, {themes} themes, {atmos} atmospheres, "
                         f"{motivs} motivations, {cast_ct} cast, {crew_ct} crew")

        if all_pass:
            print_info("All verification checks PASSED")
        else:
            print_info("Some checks FAILED — run scripts/verify_db.py for details")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Seed 3 reference films into the database")
    parser.add_argument("--offline", action="store_true",
                        help="Use pre-built fallback data (no API keys needed)")
    parser.add_argument("--no-db", action="store_true",
                        help="Skip database insertion, only test pipeline")
    parser.add_argument("--reset", action="store_true",
                        help="Delete 3 reference films before re-inserting")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
