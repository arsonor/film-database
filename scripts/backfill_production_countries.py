"""
Backfill film_production_country (and production_country lookup) from TMDB.

For every film with a tmdb_id, fetch /movie/{tmdb_id}, extract
production_countries, lazy-populate the production_country lookup, and
insert junction rows in film_production_country.

Run once after migration 020. Safe to re-run (idempotent — junction inserts
use ON CONFLICT DO NOTHING; the script also skips films that already have
junction rows unless --force is passed).

Usage:
    python scripts/backfill_production_countries.py
    python scripts/backfill_production_countries.py --dry-run
    python scripts/backfill_production_countries.py --force   # re-fetch all

Requires: TMDB_API_KEY and DATABASE_URL in .env
"""

import argparse
import asyncio
import os

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"


async def get_or_create_country(db: AsyncSession, code: str, name: str) -> int:
    r = await db.execute(
        text("SELECT country_id FROM production_country WHERE country_code = :code"),
        {"code": code},
    )
    cid = r.scalar_one_or_none()
    if cid:
        return cid
    r = await db.execute(
        text("""
            INSERT INTO production_country (country_code, country_name)
            VALUES (:code, :name) RETURNING country_id
        """),
        {"code": code, "name": name},
    )
    return r.scalar_one()


async def main():
    parser = argparse.ArgumentParser(description="Backfill film_production_country from TMDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch every film, even those with existing junction rows",
    )
    args = parser.parse_args()

    if not TMDB_API_KEY:
        print("ERROR: Set TMDB_API_KEY in .env")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        if args.force:
            sql = """
                SELECT film_id, original_title, tmdb_id
                FROM film WHERE tmdb_id IS NOT NULL
                ORDER BY film_id
            """
        else:
            sql = """
                SELECT f.film_id, f.original_title, f.tmdb_id
                FROM film f
                LEFT JOIN film_production_country fpc ON fpc.film_id = f.film_id
                WHERE f.tmdb_id IS NOT NULL AND fpc.film_id IS NULL
                ORDER BY f.film_id
            """
        result = await db.execute(text(sql))
        films = result.fetchall()
        print(f"Found {len(films)} films to backfill\n")

        ok = 0
        no_data = 0
        failed = 0
        link_count = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, (film_id, title, tmdb_id) in enumerate(films, 1):
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/movie/{tmdb_id}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"},
                    )
                    if resp.status_code == 404:
                        print(f"  [404]   {title} (tmdb={tmdb_id})")
                        failed += 1
                        await asyncio.sleep(0.25)
                        continue
                    resp.raise_for_status()
                    data = resp.json()

                    countries = data.get("production_countries", []) or []
                    if not countries:
                        print(f"  [{idx:>4}/{len(films)}] [NONE] {title}")
                        no_data += 1
                        await asyncio.sleep(0.25)
                        continue

                    codes = [
                        (pc.get("iso_3166_1"), pc.get("name") or pc.get("iso_3166_1"))
                        for pc in countries
                        if pc.get("iso_3166_1")
                    ]
                    summary = ", ".join(c for c, _ in codes)
                    print(f"  [{idx:>4}/{len(films)}] {title} → {summary}")

                    if not args.dry_run:
                        if args.force:
                            await db.execute(
                                text("DELETE FROM film_production_country WHERE film_id = :fid"),
                                {"fid": film_id},
                            )
                        for code, name in codes:
                            country_id = await get_or_create_country(db, code, name)
                            await db.execute(
                                text("""
                                    INSERT INTO film_production_country (film_id, country_id)
                                    VALUES (:fid, :cid) ON CONFLICT DO NOTHING
                                """),
                                {"fid": film_id, "cid": country_id},
                            )
                            link_count += 1
                    ok += 1
                    await asyncio.sleep(0.25)
                except Exception as e:
                    print(f"  [ERROR] {title} (tmdb={tmdb_id}): {e}")
                    failed += 1

        if not args.dry_run:
            await db.commit()

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Films processed:    {len(films)}")
        print(f"With country data:  {ok}")
        print(f"No country data:    {no_data}")
        print(f"Errors:             {failed}")
        print(f"Junction rows added: {link_count}")
        if args.dry_run:
            print("(DRY RUN — no changes written)")
        print(f"{'='*60}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
