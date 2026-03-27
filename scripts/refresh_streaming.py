"""
Refresh streaming platform data for all films in the database.

Fetches watch/providers from TMDB for each film, maps to our platform names,
and replaces the film_exploitation rows. This is a full refresh — existing
platform associations are cleared and rebuilt from current TMDB data.

Streaming availability is volatile (films move between platforms regularly),
so this script should be run periodically (e.g., monthly).

Usage:
    python scripts/refresh_streaming.py              # full refresh
    python scripts/refresh_streaming.py --dry-run    # preview without writing
    python scripts/refresh_streaming.py --country BE  # use Belgium instead of France

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

# Same mapping as tmdb_mapper.py — keep in sync
PROVIDER_NAME_MAP = {
    "Netflix": "Netflix",
    "Amazon Prime Video": "Amazon Prime Video",
    "Amazon Video": "Amazon Prime Video",
    "Disney Plus": "Disney+",
    "Disney+": "Disney+",
    "Canal+": "Canal+",
    "Canal+ Cinema": "Canal+",
    "Apple TV Plus": "Apple TV+",
    "Apple TV+": "Apple TV+",
    "Hulu": "Hulu",
    "HBO Max": "HBO Max",
    "Max": "HBO Max",
    "Paramount Plus": "Paramount+",
    "Paramount+": "Paramount+",
    "Mubi": "Mubi",
    "MUBI": "Mubi",
    "The Criterion Channel": "Criterion Channel",
    "Criterion Channel": "Criterion Channel",
    "Arte": "Arte",
}


def map_providers(providers_data: dict, country: str) -> list[str]:
    """Extract flatrate (subscription) streaming platforms for a country."""
    country_data = providers_data.get("results", {}).get(country, {})
    platforms = []
    seen = set()
    for p in country_data.get("flatrate", []):
        name = p.get("provider_name", "")
        mapped = PROVIDER_NAME_MAP.get(name)
        if mapped and mapped not in seen:
            seen.add(mapped)
            platforms.append(mapped)
    return platforms


async def main():
    parser = argparse.ArgumentParser(description="Refresh streaming platforms from TMDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--country", default="FR", help="ISO country code for providers (default: FR)")
    args = parser.parse_args()

    if not TMDB_API_KEY:
        print("ERROR: Set TMDB_API_KEY in .env")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Load platform_id lookup
        result = await db.execute(text("SELECT platform_id, platform_name FROM stream_platform"))
        platform_lookup = {row[1]: row[0] for row in result.fetchall()}
        print(f"Known platforms: {', '.join(sorted(platform_lookup.keys()))}\n")

        # Get all films
        result = await db.execute(text("""
            SELECT film_id, original_title, tmdb_id
            FROM film WHERE tmdb_id IS NOT NULL
            ORDER BY film_id
        """))
        films = result.fetchall()
        print(f"Found {len(films)} films to refresh (country={args.country})\n")

        total_updated = 0
        total_platforms = 0
        unmapped_providers: dict[str, int] = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for film_id, title, tmdb_id in films:
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/movie/{tmdb_id}/watch/providers",
                        params={"api_key": TMDB_API_KEY},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    platforms = map_providers(data, args.country)

                    # Also track unmapped providers for visibility
                    country_data = data.get("results", {}).get(args.country, {})
                    for p in country_data.get("flatrate", []):
                        pname = p.get("provider_name", "")
                        if pname not in PROVIDER_NAME_MAP:
                            unmapped_providers[pname] = unmapped_providers.get(pname, 0) + 1

                    if platforms:
                        print(f"  [FOUND]  {title} → {', '.join(platforms)}")
                    else:
                        print(f"  [NONE]   {title} — no subscription streaming in {args.country}")

                    if not args.dry_run:
                        # Clear existing
                        await db.execute(
                            text("DELETE FROM film_exploitation WHERE film_id = :fid"),
                            {"fid": film_id},
                        )
                        # Insert new
                        for pname in platforms:
                            pid = platform_lookup.get(pname)
                            if pid:
                                await db.execute(
                                    text("""
                                        INSERT INTO film_exploitation (film_id, platform_id)
                                        VALUES (:fid, :pid) ON CONFLICT DO NOTHING
                                    """),
                                    {"fid": film_id, "pid": pid},
                                )
                                total_platforms += 1

                        total_updated += 1

                    await asyncio.sleep(0.25)

                except Exception as e:
                    print(f"  [ERROR]  {title} (tmdb={tmdb_id}): {e}")

        if not args.dry_run:
            await db.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY (country={args.country})")
        print(f"{'='*60}")
        print(f"Films processed:     {len(films)}")
        print(f"Films with platforms: {total_updated}")
        print(f"Platform links:      {total_platforms}")
        if args.dry_run:
            print("(DRY RUN — no changes written)")

        if unmapped_providers:
            print(f"\nUnmapped TMDB providers (not in our platform list):")
            for pname, count in sorted(unmapped_providers.items(), key=lambda x: -x[1]):
                print(f"  {pname} ({count} films)")
            print("To add these, insert into stream_platform table + add to PROVIDER_NAME_MAP in tmdb_mapper.py and this script.")

        print(f"{'='*60}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
