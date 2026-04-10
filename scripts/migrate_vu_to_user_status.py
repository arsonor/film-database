"""
Migrate film.vu to user_film_status.seen for a specific user.

Usage:
  python scripts/migrate_vu_to_user_status.py --user-uuid <supabase-user-uuid>
"""

import argparse
import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Migrate film.vu to user_film_status")
    parser.add_argument("--user-uuid", required=True, help="Supabase user UUID to assign seen films to")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without changing anything")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL", "")
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    if not dsn:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    conn = await asyncpg.connect(dsn)

    try:
        # Check user exists
        user = await conn.fetchrow("SELECT id, email, tier FROM user_profile WHERE id = $1", args.user_uuid)
        if not user:
            print(f"ERROR: User {args.user_uuid} not found in user_profile.")
            print("Make sure you've logged in via Supabase Auth first and the user_profile row exists.")
            sys.exit(1)

        print(f"User: {user['email']} (tier: {user['tier']})")

        # Count films with vu = TRUE
        count = await conn.fetchval("SELECT COUNT(*) FROM film WHERE vu = TRUE")
        print(f"Films with vu=TRUE: {count}")

        if args.dry_run:
            print(f"\nDRY RUN: Would insert {count} rows into user_film_status and drop film.vu column.")
            return

        # Migrate
        inserted = await conn.execute("""
            INSERT INTO user_film_status (user_id, film_id, seen)
            SELECT $1, film_id, TRUE FROM film WHERE vu = TRUE
            ON CONFLICT (user_id, film_id) DO UPDATE SET seen = TRUE
        """, args.user_uuid)
        print(f"Inserted/updated: {inserted}")

        # Drop vu column
        await conn.execute("ALTER TABLE film DROP COLUMN IF EXISTS vu")
        print("Dropped film.vu column.")

        print(f"\nMigration complete: {count} films marked as seen for {user['email']}.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
