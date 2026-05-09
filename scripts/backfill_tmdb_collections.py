"""
Backfill the tmdb_collection lookup table.

For every distinct film.tmdb_collection_id in the DB, fetch /collection/{id}
from TMDB and upsert into tmdb_collection (collection_id, collection_name,
poster_path, backdrop_path).

Run once after migration 020. Safe to re-run (idempotent — re-fetches and
updates names/posters).

Usage:
    python scripts/backfill_tmdb_collections.py
    python scripts/backfill_tmdb_collections.py --dry-run

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


async def main():
    parser = argparse.ArgumentParser(description="Backfill tmdb_collection from TMDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if not TMDB_API_KEY:
        print("ERROR: Set TMDB_API_KEY in .env")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Distinct collection ids in use
        result = await db.execute(
            text("""
                SELECT DISTINCT tmdb_collection_id
                FROM film
                WHERE tmdb_collection_id IS NOT NULL
                ORDER BY tmdb_collection_id
            """)
        )
        collection_ids = [row[0] for row in result.fetchall()]
        print(f"Found {len(collection_ids)} unique TMDB collection ids in use\n")

        # Skip ones we already have populated (idempotent re-run shortcut)
        if not args.dry_run:
            existing_result = await db.execute(
                text("SELECT collection_id FROM tmdb_collection")
            )
            existing = {row[0] for row in existing_result.fetchall()}
            todo = [cid for cid in collection_ids if cid not in existing]
            print(f"  {len(existing)} already populated, {len(todo)} to fetch\n")
        else:
            todo = collection_ids

        ok = 0
        failed = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, cid in enumerate(todo, 1):
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/collection/{cid}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"},
                    )
                    if resp.status_code == 404:
                        print(f"  [404]   collection {cid} not found, skipping")
                        failed += 1
                        await asyncio.sleep(0.25)
                        continue
                    resp.raise_for_status()
                    data = resp.json()

                    name = data.get("name") or f"Collection {cid}"
                    poster = data.get("poster_path")
                    backdrop = data.get("backdrop_path")
                    print(f"  [{idx:>4}/{len(todo)}] {cid} — {name}")

                    if not args.dry_run:
                        await db.execute(
                            text("""
                                INSERT INTO tmdb_collection
                                    (collection_id, collection_name, poster_path, backdrop_path)
                                VALUES (:cid, :cname, :poster, :backdrop)
                                ON CONFLICT (collection_id) DO UPDATE SET
                                    collection_name = EXCLUDED.collection_name,
                                    poster_path = EXCLUDED.poster_path,
                                    backdrop_path = EXCLUDED.backdrop_path,
                                    updated_at = NOW()
                            """),
                            {"cid": cid, "cname": name, "poster": poster, "backdrop": backdrop},
                        )
                    ok += 1
                    await asyncio.sleep(0.25)
                except Exception as e:
                    print(f"  [ERROR] collection {cid}: {e}")
                    failed += 1

        if not args.dry_run:
            await db.commit()

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Successful: {ok}")
        print(f"Failed:     {failed}")
        if args.dry_run:
            print("(DRY RUN — no changes written)")
        print(f"{'='*60}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
