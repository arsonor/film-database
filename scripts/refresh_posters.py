"""
Quick script to refresh poster/backdrop URLs from TMDB for all films in the database.
Usage: python scripts/refresh_posters.py
"""

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
    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        print("ERROR: Set your real TMDB_API_KEY in .env first")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Get all films with tmdb_ids
        result = await db.execute(
            text("SELECT film_id, original_title, tmdb_id, poster_url FROM film WHERE tmdb_id IS NOT NULL")
        )
        films = result.fetchall()
        print(f"Found {len(films)} films with tmdb_ids")

        async with httpx.AsyncClient() as client:
            for film_id, title, tmdb_id, old_poster in films:
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/movie/{tmdb_id}",
                        params={"api_key": TMDB_API_KEY},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    poster_path = data.get("poster_path")
                    backdrop_path = data.get("backdrop_path")

                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                    backdrop_url = f"https://image.tmdb.org/t/p/w780{backdrop_path}" if backdrop_path else None

                    await db.execute(
                        text("""
                            UPDATE film
                            SET poster_url = :poster, backdrop_url = :backdrop
                            WHERE film_id = :fid
                        """),
                        {"poster": poster_url, "backdrop": backdrop_url, "fid": film_id},
                    )

                    changed = "UPDATED" if poster_url != old_poster else "unchanged"
                    print(f"  [{changed}] {title} (tmdb={tmdb_id}) → {poster_url}")

                except Exception as e:
                    print(f"  [ERROR] {title} (tmdb={tmdb_id}): {e}")

        await db.commit()
        print("\nDone! Poster URLs refreshed.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
