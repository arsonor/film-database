"""
Fetch TMDB vote_average and vote_count for all films, then compute
Bayesian weighted scores and update the database.

Weighted formula (same concept as IMDb Top 250):
  weighted = (v / (v + m)) * R + (m / (v + m)) * C
where:
  R = film's vote_average
  v = film's vote_count
  m = minimum votes threshold (25th percentile of vote counts)
  C = mean vote_average across all films

Usage:
  python scripts/refresh_tmdb_scores.py
  python scripts/refresh_tmdb_scores.py --dry-run
"""

import argparse
import asyncio
import os
import statistics

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

BATCH_SIZE = 40
BATCH_DELAY = 10.5  # TMDB rate limit: 40 requests per 10 seconds


async def fetch_scores(client: httpx.AsyncClient, tmdb_id: int) -> dict | None:
    try:
        resp = await client.get(
            f"{TMDB_BASE}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise
    except httpx.RequestError:
        return None


def compute_weighted_scores(
    films: list[dict],
) -> list[dict]:
    """Compute Bayesian weighted scores for all films with valid data."""
    scored = [f for f in films if f["vote_average"] and f["vote_count"] and f["vote_count"] > 0]
    if not scored:
        return films

    vote_counts = [f["vote_count"] for f in scored]
    m = statistics.median(vote_counts)
    C = statistics.mean(f["vote_average"] for f in scored)

    print(f"  Weighted formula params: m={m:.0f} (median votes), C={C:.2f} (mean score)")
    print(f"  Films with votes: {len(scored)} / {len(films)}")

    for f in films:
        v = f.get("vote_count") or 0
        R = f.get("vote_average") or 0
        if v > 0 and R > 0:
            f["weighted_score"] = round((v / (v + m)) * R + (m / (v + m)) * C, 2)
        else:
            f["weighted_score"] = None

    return films


async def main(dry_run: bool = False):
    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        print("ERROR: Set your real TMDB_API_KEY in .env first")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await db.execute(
            text("SELECT film_id, original_title, tmdb_id FROM film WHERE tmdb_id IS NOT NULL ORDER BY film_id")
        )
        rows = result.fetchall()
        total = len(rows)
        print(f"Found {total} films with tmdb_ids")

        films_data: list[dict] = []
        errors = 0

        async with httpx.AsyncClient(timeout=15.0) as client:
            for i in range(0, total, BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                tasks = []
                for film_id, title, tmdb_id in batch:
                    tasks.append((film_id, title, tmdb_id, fetch_scores(client, tmdb_id)))

                for film_id, title, tmdb_id, coro in tasks:
                    scores = await coro
                    if scores:
                        films_data.append({
                            "film_id": film_id,
                            "title": title,
                            "vote_average": scores["vote_average"],
                            "vote_count": scores["vote_count"],
                        })
                    else:
                        errors += 1
                        films_data.append({
                            "film_id": film_id,
                            "title": title,
                            "vote_average": None,
                            "vote_count": None,
                        })

                done = min(i + BATCH_SIZE, total)
                print(f"  Fetched {done}/{total} ({errors} errors)", end="\r")

                if done < total:
                    await asyncio.sleep(BATCH_DELAY)

        print()

        films_data = compute_weighted_scores(films_data)

        if dry_run:
            print("\n-- DRY RUN: top 20 by weighted score --")
            ranked = sorted(
                [f for f in films_data if f.get("weighted_score")],
                key=lambda f: f["weighted_score"],
                reverse=True,
            )
            for f in ranked[:20]:
                print(
                    f"  {f['weighted_score']:5.2f}  "
                    f"(avg={f['vote_average']:.1f}, votes={f['vote_count']:,})  "
                    f"{f['title']}"
                )
            print(f"\n  ... and {len(ranked) - 20} more films with scores")
            return

        print("Updating database...")
        updated = 0
        for f in films_data:
            await db.execute(
                text("""
                    UPDATE film
                    SET tmdb_score = :score,
                        tmdb_vote_count = :votes,
                        weighted_score = :weighted
                    WHERE film_id = :film_id
                """),
                {
                    "film_id": f["film_id"],
                    "score": f["vote_average"],
                    "votes": f["vote_count"],
                    "weighted": f["weighted_score"],
                },
            )
            updated += 1

        await db.commit()
        print(f"Done! Updated {updated} films.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch TMDB scores and compute weighted ratings")
    parser.add_argument("--dry-run", action="store_true", help="Preview results without updating DB")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
