"""
Cross-platform database setup script for the Film Database project.

Creates the database schema and seeds taxonomy tables.
Works on Windows, macOS, and Linux.

Usage:
    python database/setup_db.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed_taxonomy.sql"


def split_sql(sql: str) -> list[str]:
    """
    Split SQL text into individual statements, respecting $$ blocks
    (PL/pgSQL function bodies contain semicolons that aren't statement separators).
    """
    statements = []
    current = ""
    in_dollar_block = False

    for line in sql.split("\n"):
        stripped = line.strip()

        # Track $$ blocks
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


async def execute_sql_file(engine, filepath: Path, label: str):
    """Execute all statements in a SQL file."""
    if not filepath.exists():
        print(f"  ERROR: {filepath} not found")
        sys.exit(1)

    sql = filepath.read_text(encoding="utf-8")
    statements = split_sql(sql)

    executed = 0
    errors = 0
    async with engine.begin() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            try:
                await conn.execute(text(stmt))
                executed += 1
            except Exception as e:
                # Some benign errors: CREATE TABLE IF NOT EXISTS when table exists, etc.
                err_str = str(e).lower()
                if "already exists" in err_str or "does not exist" in err_str:
                    logger.debug("%s: %s (benign)", label, e)
                else:
                    logger.warning("%s statement error: %s", label, e)
                    errors += 1

    print(f"  {label}: {executed} statements executed, {errors} errors")


async def main():
    load_dotenv(PROJECT_ROOT / ".env")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("=" * 60)
        print("  ERROR: DATABASE_URL not set")
        print("=" * 60)
        print()
        print("  Set DATABASE_URL in your .env file:")
        print("    DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/film_database")
        print()
        print("  Make sure PostgreSQL is running and the database exists:")
        print("    createdb film_database")
        print("  or:")
        print("    psql -c \"CREATE DATABASE film_database;\"")
        sys.exit(1)

    print("=" * 60)
    print("  FILM DATABASE SETUP")
    print("=" * 60)

    # Step 1: Test connection
    print("\n[1] Testing database connection...")
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  Connected: {version[:60]}...")
    except Exception as e:
        print(f"  ERROR: Cannot connect to database: {e}")
        print()
        print("  Troubleshooting:")
        print("  1. Is PostgreSQL running?")
        print("  2. Does the database exist? Run: createdb film_database")
        print(f"  3. Check DATABASE_URL: {database_url[:40]}...")
        sys.exit(1)

    # Step 2: Check if schema exists
    print("\n[2] Checking existing schema...")
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'film')"
        ))
        schema_exists = result.scalar()

    if schema_exists:
        print("  Schema already exists. Re-running will update/skip existing objects.")
    else:
        print("  No existing schema found. Creating from scratch.")

    # Step 3: Run schema.sql
    print("\n[3] Running schema.sql...")
    await execute_sql_file(engine, SCHEMA_PATH, "schema.sql")

    # Step 4: Run seed_taxonomy.sql
    print("\n[4] Running seed_taxonomy.sql...")
    await execute_sql_file(engine, SEED_PATH, "seed_taxonomy.sql")

    # Step 5: Verify
    print("\n[5] Verifying setup...")
    async with engine.connect() as conn:
        # Count tables
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        table_count = result.scalar()
        print(f"  Tables in database: {table_count}")

        # Count rows in taxonomy tables
        taxonomy_tables = [
            ("person_job", "role_name"),
            ("category", "category_name"),
            ("cinema_type", "technique_name"),
            ("place_context", "environment"),
            ("time_context", "time_period"),
            ("theme_context", "theme_name"),
            ("character_context", "context_name"),
            ("atmosphere", "atmosphere_name"),
            ("motivation_relation", "motivation_name"),
            ("message_conveyed", "message_name"),
            ("stream_platform", "platform_name"),
            ("language", "language_code"),
        ]

        print("\n  Taxonomy table row counts:")
        for table, _ in taxonomy_tables:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"    {table:30s}: {count}")
            except Exception as e:
                print(f"    {table:30s}: ERROR - {e}")

    await engine.dispose()

    print("\n" + "=" * 60)
    print("  SETUP COMPLETE")
    print("=" * 60)
    print()
    print("  Next steps:")
    print("    python scripts/seed_reference_films.py --offline")
    print("    python scripts/verify_db.py")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
