"""
Backfill person details (gender, birth/death dates, nationality) from TMDB.

Fetches /person/{tmdb_id} for all persons that have a tmdb_id but are missing
gender, date_of_birth, or nationality. Updates the DB with the retrieved data.

Usage:
    python scripts/backfill_person_details.py              # full backfill
    python scripts/backfill_person_details.py --dry-run    # preview without writing
    python scripts/backfill_person_details.py --verbose    # show all persons, not just updates

Requires: TMDB_API_KEY and DATABASE_URL in .env
"""

import argparse
import asyncio
import os
from datetime import date

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

# TMDB gender codes → our DB values
TMDB_GENDER_MAP = {1: "F", 2: "M"}


def extract_nationality(place_of_birth: str | None) -> str | None:
    """
    Extract a rough nationality from TMDB's place_of_birth string.
    TMDB returns strings like "London, England, UK" or "New York City, New York, USA".
    We take the last part as the country/nationality.
    """
    if not place_of_birth:
        return None
    parts = [p.strip() for p in place_of_birth.split(",")]
    return parts[-1] if parts else None


async def main():
    parser = argparse.ArgumentParser(description="Backfill person details from TMDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", action="store_true", help="Show all persons")
    args = parser.parse_args()

    if not TMDB_API_KEY:
        print("ERROR: Set TMDB_API_KEY in .env")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Get persons missing details (have tmdb_id but missing gender OR birth date OR nationality)
        result = await db.execute(text("""
            SELECT person_id, firstname, lastname, tmdb_id, gender,
                   date_of_birth, date_of_death, nationality
            FROM person
            WHERE tmdb_id IS NOT NULL
              AND (gender IS NULL OR date_of_birth IS NULL OR nationality IS NULL)
            ORDER BY person_id
        """))
        persons = result.fetchall()
        print(f"Found {len(persons)} persons missing details\n")

        if not persons:
            print("Nothing to backfill.")
            await engine.dispose()
            return

        updated = 0
        skipped = 0
        errors = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for person_id, firstname, lastname, tmdb_id, cur_gender, cur_dob, cur_dod, cur_nat in persons:
                name = f"{firstname or ''} {lastname}".strip()
                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/person/{tmdb_id}",
                        params={"api_key": TMDB_API_KEY},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    # Extract fields
                    new_gender = TMDB_GENDER_MAP.get(data.get("gender")) if cur_gender is None else None
                    raw_dob = data.get("birthday") if cur_dob is None else None
                    raw_dod = data.get("deathday") if cur_dod is None else None
                    new_dob = date.fromisoformat(raw_dob) if raw_dob else None
                    new_dod = date.fromisoformat(raw_dod) if raw_dod else None
                    new_nat = extract_nationality(data.get("place_of_birth")) if cur_nat is None else None

                    # Build update
                    updates = {}
                    if new_gender:
                        updates["gender"] = new_gender
                    if new_dob:
                        updates["date_of_birth"] = new_dob
                    if new_dod:
                        updates["date_of_death"] = new_dod
                    if new_nat:
                        updates["nationality"] = new_nat

                    if updates:
                        print(f"  [UPDATE] {name} (tmdb={tmdb_id}): {updates}")
                        if not args.dry_run:
                            set_parts = []
                            params = {"pid": person_id}
                            for key, val in updates.items():
                                set_parts.append(f"{key} = :{key}")
                                params[key] = val
                            await db.execute(
                                text(f"UPDATE person SET {', '.join(set_parts)} WHERE person_id = :pid"),
                                params,
                            )
                        updated += 1
                    else:
                        if args.verbose:
                            print(f"  [SKIP]   {name} — TMDB has no additional data")
                        skipped += 1

                    # Rate limiting: 0.25s between requests
                    await asyncio.sleep(0.25)

                except Exception as e:
                    print(f"  [ERROR]  {name} (tmdb={tmdb_id}): {e}")
                    errors += 1

        if not args.dry_run:
            await db.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Persons processed: {len(persons)}")
        print(f"Updated:           {updated}")
        print(f"Skipped (no data): {skipped}")
        print(f"Errors:            {errors}")
        if args.dry_run:
            print("(DRY RUN — no changes written)")
        print(f"{'='*60}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
