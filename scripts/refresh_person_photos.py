"""
Fix person tmdb_ids and refresh photo URLs using TMDB movie credits.

The original person tmdb_ids in the database are WRONG — they don't match
the IDs that TMDB returns in movie credits. This script:

1. For each film, fetches credits from TMDB (/movie/{id}?append_to_response=credits)
2. For each person in our DB who is cast/crew for that film, matches them against
   TMDB credits by NAME (case-insensitive, accent-tolerant)
3. Updates both tmdb_id and photo_url to the correct TMDB values

Usage:
    python scripts/refresh_person_photos.py --dry-run    # preview without writing
    python scripts/refresh_person_photos.py              # fix tmdb_ids + update photos
    python scripts/refresh_person_photos.py --verbose    # show detailed matching info
    python scripts/refresh_person_photos.py --diagnose   # print current person table state

Requires: TMDB_API_KEY and DATABASE_URL in .env
"""

import argparse
import asyncio
import os
import unicodedata

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"


def normalize(name: str) -> str:
    """Normalize a name for fuzzy matching: lowercase, strip accents, collapse whitespace."""
    # Decompose unicode characters, strip combining marks (accents)
    nfkd = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(stripped.lower().split())


async def diagnose_db(session_factory):
    """Print current state of person table."""
    async with session_factory() as db:
        result = await db.execute(text("""
            SELECT person_id, COALESCE(firstname, '') || ' ' || lastname AS name,
                   tmdb_id, photo_url
            FROM person
            ORDER BY person_id
        """))
        rows = result.fetchall()
        print(f"\n{'='*80}")
        print(f"PERSON TABLE: {len(rows)} rows")
        print(f"{'='*80}")
        for pid, name, tid, photo in rows:
            photo_status = "HAS PHOTO" if photo else "null"
            print(f"  id={pid:3d}  tmdb={str(tid):>10s}  {photo_status:10s}  {name}")
        print()


async def fix_persons(session_factory, dry_run: bool, verbose: bool):
    """Fix person tmdb_ids and photos by matching names against TMDB credits."""
    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        print("ERROR: Set your real TMDB_API_KEY in .env first")
        return

    async with session_factory() as db:
        # Get all films
        result = await db.execute(
            text("SELECT film_id, original_title, tmdb_id FROM film WHERE tmdb_id IS NOT NULL")
        )
        films = result.fetchall()
        print(f"Found {len(films)} films\n")

        # For each film, get the persons linked to it in our DB
        # Build a map: film_id → list of (person_id, full_name, current_tmdb_id)
        film_persons: dict[int, list[tuple[int, str, int | None]]] = {}
        for film_id, _, _ in films:
            # Get cast
            r = await db.execute(text("""
                SELECT DISTINCT p.person_id,
                       COALESCE(p.firstname, '') || ' ' || p.lastname AS name,
                       p.tmdb_id
                FROM person p
                LEFT JOIN casting ca ON p.person_id = ca.person_id AND ca.film_id = :fid
                LEFT JOIN crew cr ON p.person_id = cr.person_id AND cr.film_id = :fid
                WHERE ca.film_id = :fid OR cr.film_id = :fid
            """), {"fid": film_id})
            film_persons[film_id] = [(row[0], row[1], row[2]) for row in r.fetchall()]

        total_fixed_id = 0
        total_fixed_photo = 0
        all_matched_person_ids = set()

        async with httpx.AsyncClient(timeout=30.0) as client:
            for film_id, title, film_tmdb_id in films:
                print(f"--- {title} (tmdb={film_tmdb_id}) ---")

                try:
                    resp = await client.get(
                        f"{TMDB_BASE}/movie/{film_tmdb_id}",
                        params={"api_key": TMDB_API_KEY, "append_to_response": "credits"},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    credits = data.get("credits", {})
                    cast_list = credits.get("cast", [])
                    crew_list = credits.get("crew", [])
                    all_credits = cast_list + crew_list

                    # Build a lookup: normalized_name → (tmdb_id, profile_path, original_name)
                    # For people with multiple credits (e.g. director + writer), keep first profile_path
                    tmdb_by_name: dict[str, tuple[int, str | None, str]] = {}
                    for person in all_credits:
                        tmdb_name = person.get("name", "")
                        tmdb_id = person.get("id")
                        profile_path = person.get("profile_path")
                        norm = normalize(tmdb_name)
                        if norm not in tmdb_by_name:
                            tmdb_by_name[norm] = (tmdb_id, profile_path, tmdb_name)
                        elif profile_path and tmdb_by_name[norm][1] is None:
                            # Update if this entry has a photo and previous didn't
                            tmdb_by_name[norm] = (tmdb_id, profile_path, tmdb_name)

                    print(f"  TMDB credits: {len(cast_list)} cast + {len(crew_list)} crew")
                    db_persons = film_persons.get(film_id, [])
                    print(f"  DB persons for this film: {len(db_persons)}")

                    for person_id, db_name, old_tmdb_id in db_persons:
                        norm_db = normalize(db_name)
                        match = tmdb_by_name.get(norm_db)

                        if not match:
                            # Try partial matching: check if our DB name is contained in any TMDB name or vice versa
                            for norm_tmdb, (tid, pp, orig) in tmdb_by_name.items():
                                if norm_db in norm_tmdb or norm_tmdb in norm_db:
                                    match = (tid, pp, orig)
                                    if verbose:
                                        print(f"    [FUZZY]  '{db_name}' ~ '{orig}'")
                                    break

                        if not match:
                            if verbose:
                                print(f"    [MISS]   {db_name} — not found in TMDB credits")
                            continue

                        new_tmdb_id, profile_path, tmdb_name = match
                        new_photo = f"https://image.tmdb.org/t/p/w185{profile_path}" if profile_path else None

                        all_matched_person_ids.add(person_id)

                        # Check if tmdb_id needs fixing
                        id_changed = old_tmdb_id != new_tmdb_id
                        # Get current photo
                        r = await db.execute(
                            text("SELECT photo_url FROM person WHERE person_id = :pid"),
                            {"pid": person_id},
                        )
                        old_photo = r.scalar_one_or_none()
                        photo_changed = new_photo is not None and new_photo != old_photo

                        if not id_changed and not photo_changed:
                            print(f"    [OK]     {db_name} (tmdb={old_tmdb_id})")
                            continue

                        parts = []
                        if id_changed:
                            parts.append(f"tmdb: {old_tmdb_id}→{new_tmdb_id}")
                            total_fixed_id += 1
                        if photo_changed:
                            parts.append(f"photo: {'new' if old_photo is None else 'updated'}")
                            total_fixed_photo += 1

                        print(f"    [FIX]    {db_name} ({', '.join(parts)})")

                        if not dry_run:
                            update_fields = {}
                            set_parts = []
                            if id_changed:
                                # First clear old tmdb_id to avoid unique constraint conflict
                                # (another person might have the target tmdb_id, but that shouldn't happen)
                                set_parts.append("tmdb_id = :new_tid")
                                update_fields["new_tid"] = new_tmdb_id
                            if photo_changed:
                                set_parts.append("photo_url = :new_photo")
                                update_fields["new_photo"] = new_photo

                            if set_parts:
                                update_fields["pid"] = person_id
                                sql = f"UPDATE person SET {', '.join(set_parts)} WHERE person_id = :pid"
                                try:
                                    await db.execute(text(sql), update_fields)
                                except Exception as e:
                                    print(f"    [ERROR]  Failed to update {db_name}: {e}")

                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"  [ERROR] {e}")

        if not dry_run:
            await db.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"tmdb_ids fixed:   {total_fixed_id}")
        print(f"Photos updated:   {total_fixed_photo}")
        print(f"Persons matched:  {len(all_matched_person_ids)} / 46")
        if dry_run:
            print("(DRY RUN — no changes written)")
        print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Fix person tmdb_ids and refresh photos from TMDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", action="store_true", help="Show detailed matching info")
    parser.add_argument("--diagnose", action="store_true", help="Print current person table state")
    args = parser.parse_args()

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        if args.diagnose:
            await diagnose_db(session_factory)
            return

        await fix_persons(session_factory, args.dry_run, args.verbose)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
