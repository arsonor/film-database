"""
Backfill tmdb_collection_id for existing films.

Fetches belongs_to_collection from TMDB for all films that have a tmdb_id
but no tmdb_collection_id, and updates the column. Also auto-links any
newly discovered collection siblings via film_sequel.

Usage: python scripts/backfill_collection_ids.py
       python scripts/backfill_collection_ids.py --dry-run

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
    parser = argparse.ArgumentParser(description="Backfill tmdb_collection_id for existing films")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if not TMDB_API_KEY:
        print("ERROR: Set TMDB_API_KEY in .env")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Get films missing collection_id
        result = await db.execute(text("""
            SELECT film_id, original_title, tmdb_id
            FROM film
            WHERE tmdb_id IS NOT NULL AND tmdb_collection_id IS NULL
            ORDER BY film_id
        """))
        films = result.fetchall()
        print(f"Found {len(films)} films without tmdb_collection_id\n")

        if not films:
            print("Nothing to backfill.")
            await engine.dispose()
            return

        updated = 0
        linked = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for film_id, title, tmdb_id in films:
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/movie/{tmdb_id}",
                        params={"api_key": TMDB_API_KEY},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    collection = data.get("belongs_to_collection")
                    if collection and isinstance(collection, dict):
                        coll_id = collection.get("id")
                        coll_name = collection.get("name", "?")
                        print(f"  [FOUND]  {title} → collection {coll_id} ({coll_name})")

                        if not args.dry_run:
                            await db.execute(
                                text("UPDATE film SET tmdb_collection_id = :cid WHERE film_id = :fid"),
                                {"cid": coll_id, "fid": film_id},
                            )
                            updated += 1

                            # Auto-link with existing siblings
                            coll_result = await db.execute(text("""
                                SELECT film_id FROM film
                                WHERE tmdb_collection_id = :cid AND film_id != :fid
                            """), {"cid": coll_id, "fid": film_id})
                            sibling_ids = [row[0] for row in coll_result.fetchall()]

                            for sibling_id in sibling_ids:
                                await db.execute(text("""
                                    INSERT INTO film_sequel (film_id, related_film_id, relation_type)
                                    VALUES (:fid, :rid, 'sequel')
                                    ON CONFLICT DO NOTHING
                                """), {"fid": min(sibling_id, film_id), "rid": max(sibling_id, film_id)})
                                linked += 1
                    else:
                        print(f"  [NONE]   {title} — not part of a collection")

                    await asyncio.sleep(0.25)

                except Exception as e:
                    print(f"  [ERROR]  {title} (tmdb={tmdb_id}): {e}")

        if not args.dry_run:
            await db.commit()
            print(f"\nDone! {updated} films updated, {linked} sequel links created.")
        else:
            print(f"\n[DRY RUN] Would update {updated} films.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
