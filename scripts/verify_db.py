"""
Database verification script for the Film Database project.

Runs 17 verification queries against the 3 reference films and prints
formatted results with a PASS/FAIL summary.

Usage:
    python scripts/verify_db.py
    python scripts/verify_db.py --tmdb-id 62
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(data, headers=(), tablefmt="simple", **kwargs):
        lines = []
        if headers:
            lines.append("  ".join(str(h).ljust(20) for h in headers))
            lines.append("-" * (22 * len(headers)))
        for row in data:
            lines.append("  ".join(str(c).ljust(20) if c is not None else "NULL".ljust(20) for c in row))
        return "\n".join(lines)

logger = logging.getLogger(__name__)


def print_header(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_query(num: int, title: str):
    print(f"\n  [{num}] {title}")
    print(f"  {'-' * 60}")


def print_table(rows, headers):
    if not rows:
        print("      (no data)")
        return
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def build_in_clause(tmdb_ids):
    """Build a safe IN clause string from tmdb_ids tuple."""
    return ", ".join(str(int(tid)) for tid in tmdb_ids)


QUERIES = [
    {
        "num": 1,
        "title": "Film core data",
        "sql": """
            SELECT film_id, original_title, duration, color, first_release_date,
                   budget, revenue, tmdb_id, imdb_id
            FROM film WHERE tmdb_id IN ({ids})
            ORDER BY original_title
        """,
        "headers": ["film_id", "title", "duration", "color", "release_date", "budget", "revenue", "tmdb_id", "imdb_id"],
    },
    {
        "num": 2,
        "title": "Titles per film",
        "sql": """
            SELECT f.original_title, l.language_name, fl.film_title, fl.is_original
            FROM film f
            JOIN film_language fl ON f.film_id = fl.film_id
            JOIN language l ON fl.language_id = l.language_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, fl.is_original DESC
        """,
        "headers": ["film", "language", "title", "is_original"],
    },
    {
        "num": 3,
        "title": "Crew per film",
        "sql": """
            SELECT f.original_title, p.firstname, p.lastname, pj.role_name
            FROM film f
            JOIN crew c ON f.film_id = c.film_id
            JOIN person p ON c.person_id = p.person_id
            JOIN person_job pj ON c.job_id = pj.job_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, pj.role_name, p.lastname
        """,
        "headers": ["film", "firstname", "lastname", "role"],
    },
    {
        "num": 4,
        "title": "Cast per film (ordered)",
        "sql": """
            SELECT f.original_title, p.firstname, p.lastname, ca.character_name, ca.cast_order
            FROM film f
            JOIN casting ca ON f.film_id = ca.film_id
            JOIN person p ON ca.person_id = p.person_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, ca.cast_order
        """,
        "headers": ["film", "firstname", "lastname", "character", "order"],
    },
    {
        "num": 5,
        "title": "Categories per film",
        "sql": """
            SELECT f.original_title, c.category_name, c.historic_subcategory_name
            FROM film f
            JOIN film_genre fg ON f.film_id = fg.film_id
            JOIN category c ON fg.category_id = c.category_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, c.category_name
        """,
        "headers": ["film", "category", "subcategory"],
    },
    {
        "num": 6,
        "title": "Themes per film",
        "sql": """
            SELECT f.original_title, tc.theme_name
            FROM film f
            JOIN film_theme ft ON f.film_id = ft.film_id
            JOIN theme_context tc ON ft.theme_context_id = tc.theme_context_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, tc.theme_name
        """,
        "headers": ["film", "theme"],
    },
    {
        "num": 7,
        "title": "Atmosphere per film",
        "sql": """
            SELECT f.original_title, a.atmosphere_name
            FROM film f
            JOIN film_atmosphere fa ON f.film_id = fa.film_id
            JOIN atmosphere a ON fa.atmosphere_id = a.atmosphere_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, a.atmosphere_name
        """,
        "headers": ["film", "atmosphere"],
    },
    {
        "num": 8,
        "title": "Characters per film",
        "sql": """
            SELECT f.original_title, cc.context_name
            FROM film f
            JOIN film_character_context fcc ON f.film_id = fcc.film_id
            JOIN character_context cc ON fcc.character_context_id = cc.character_context_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, cc.sort_order, cc.context_name
        """,
        "headers": ["film", "character_context"],
    },
    {
        "num": 10,
        "title": "Motivations per film",
        "sql": """
            SELECT f.original_title, mr.motivation_name
            FROM film f
            JOIN film_motivation fm ON f.film_id = fm.film_id
            JOIN motivation_relation mr ON fm.motivation_id = mr.motivation_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, mr.motivation_name
        """,
        "headers": ["film", "motivation"],
    },
    {
        "num": 11,
        "title": "Message per film",
        "sql": """
            SELECT f.original_title, mc.message_name
            FROM film f
            JOIN film_message fmsg ON f.film_id = fmsg.film_id
            JOIN message_conveyed mc ON fmsg.message_id = mc.message_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, mc.message_name
        """,
        "headers": ["film", "message"],
    },
    {
        "num": 12,
        "title": "Geography & Place per film",
        "sql": """
            SELECT f.original_title, g.continent, g.country, g.state_city, fsp.place_type
            FROM film f
            JOIN film_set_place fsp ON f.film_id = fsp.film_id
            JOIN geography g ON fsp.geography_id = g.geography_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title
        """,
        "headers": ["film", "continent", "country", "state_city", "place_type"],
    },
    {
        "num": 13,
        "title": "Place environment & Time context per film",
        "sql": """
            SELECT DISTINCT f.original_title, pc.environment, tc.time_period
            FROM film f
            LEFT JOIN film_place fp ON f.film_id = fp.film_id
            LEFT JOIN place_context pc ON fp.place_context_id = pc.place_context_id
            LEFT JOIN film_period fper ON f.film_id = fper.film_id
            LEFT JOIN time_context tc ON fper.time_context_id = tc.time_context_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title
        """,
        "headers": ["film", "environment", "time_period"],
    },
    {
        "num": 14,
        "title": "Cinema type & Source per film",
        "sql": """
            SELECT DISTINCT f.original_title, ct.technique_name, s.source_type, s.source_title
            FROM film f
            LEFT JOIN film_technique ft ON f.film_id = ft.film_id
            LEFT JOIN cinema_type ct ON ft.cinema_type_id = ct.cinema_type_id
            LEFT JOIN film_origin fo ON f.film_id = fo.film_id
            LEFT JOIN source s ON fo.source_id = s.source_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title
        """,
        "headers": ["film", "cinema_type", "source_type", "source_title"],
    },
    {
        "num": 15,
        "title": "Awards per film",
        "sql": """
            SELECT f.original_title, a.festival_name, a.category, a.award_year, a.result
            FROM film f
            JOIN award a ON f.film_id = a.film_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, a.award_year, a.festival_name
        """,
        "headers": ["film", "festival", "category", "year", "result"],
    },
    {
        "num": 16,
        "title": "Streaming platforms per film",
        "sql": """
            SELECT f.original_title, sp.platform_name
            FROM film f
            JOIN film_exploitation fe ON f.film_id = fe.film_id
            JOIN stream_platform sp ON fe.platform_id = sp.platform_id
            WHERE f.tmdb_id IN ({ids})
            ORDER BY f.original_title, sp.platform_name
        """,
        "headers": ["film", "platform"],
    },
]

COMPLETENESS_QUERY = """
    SELECT f.original_title, f.tmdb_id,
      (SELECT COUNT(*) FROM film_genre fg WHERE fg.film_id = f.film_id) as categories,
      (SELECT COUNT(*) FROM film_technique ft WHERE ft.film_id = f.film_id) as cinema_types,
      (SELECT COUNT(*) FROM film_theme fth WHERE fth.film_id = f.film_id) as themes,
      (SELECT COUNT(*) FROM film_atmosphere fa WHERE fa.film_id = f.film_id) as atmospheres,
      (SELECT COUNT(*) FROM film_motivation fmo WHERE fmo.film_id = f.film_id) as motivations,
      (SELECT COUNT(*) FROM film_message fms WHERE fms.film_id = f.film_id) as messages,
      (SELECT COUNT(*) FROM film_character_context fcc WHERE fcc.film_id = f.film_id) as characters,
      (SELECT COUNT(*) FROM film_period fp WHERE fp.film_id = f.film_id) as time_periods,
      (SELECT COUNT(*) FROM film_set_place fsp WHERE fsp.film_id = f.film_id) as geographies,
      (SELECT COUNT(*) FROM film_place fpl WHERE fpl.film_id = f.film_id) as environments,
      (SELECT COUNT(*) FROM crew c WHERE c.film_id = f.film_id) as crew_count,
      (SELECT COUNT(*) FROM casting ca WHERE ca.film_id = f.film_id) as cast_count,
      (SELECT COUNT(*) FROM award aw WHERE aw.film_id = f.film_id) as awards_count
    FROM film f
    WHERE f.tmdb_id IN ({ids})
    ORDER BY f.original_title
"""

MIN_COUNTS = {
    "categories": 2,
    "themes": 5,
    "atmospheres": 3,
    "motivations": 3,
    "messages": 2,
    "cast_count": 5,
    "crew_count": 2,
    "time_periods": 1,
    "awards_count": 1,
}


async def run_query(engine, sql, tmdb_ids):
    """Run a single query in its own connection (no shared transaction)."""
    in_clause = build_in_clause(tmdb_ids)
    final_sql = sql.format(ids=in_clause)
    async with engine.connect() as conn:
        result = await conn.execute(text(final_sql))
        return result.fetchall()


async def run_verification(args):
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not set in .env")
        sys.exit(1)

    if args.tmdb_id:
        tmdb_ids = (args.tmdb_id,)
        print_header(f"VERIFYING FILM (tmdb_id={args.tmdb_id})")
    else:
        tmdb_ids = (62, 406, 1018)
        print_header("VERIFYING 3 REFERENCE FILMS")

    engine = create_async_engine(database_url, echo=False)

    try:
        # Run each query in its own connection
        for q in QUERIES:
            print_query(q["num"], q["title"])
            try:
                rows = await run_query(engine, q["sql"], tmdb_ids)
                print_table(rows, q["headers"])
            except Exception as e:
                print(f"      Error: {e}")

        # Completeness check
        print_query(17, "COMPLETENESS CHECK")
        try:
            rows = await run_query(engine, COMPLETENESS_QUERY, tmdb_ids)

            headers = [
                "film", "tmdb_id", "categories", "cinema",
                "themes", "atmospheres", "motivations", "messages",
                "characters", "time", "geo", "env", "crew", "cast", "awards",
            ]
            print_table(rows, headers)

            print(f"\n  {'=' * 60}")
            print(f"  PASS/FAIL SUMMARY")
            print(f"  {'=' * 60}")

            all_pass = True

            if len(rows) == 0:
                print(f"  FAIL: No films found with tmdb_id IN {tmdb_ids}")
                all_pass = False
            elif len(rows) < len(tmdb_ids):
                print(f"  FAIL: Expected {len(tmdb_ids)} films, found {len(rows)}")
                all_pass = False

            for row in rows:
                title = row[0]
                counts = {
                    "categories": row[2],
                    "cinema_types": row[3],
                    "themes": row[4],
                    "atmospheres": row[5],
                    "motivations": row[6],
                    "messages": row[7],
                    "characters": row[8],
                    "time_periods": row[9],
                    "geographies": row[10],
                    "environments": row[11],
                    "crew_count": row[12],
                    "cast_count": row[13],
                    "awards_count": row[14],
                }

                issues = []
                for dim, min_val in MIN_COUNTS.items():
                    actual = counts.get(dim, 0)
                    if actual < min_val:
                        issues.append(f"{dim}={actual}<{min_val}")

                if issues:
                    print(f"  FAIL  {title}: {', '.join(issues)}")
                    all_pass = False
                else:
                    print(f"  PASS  {title}")

            if all_pass:
                print(f"\n  === ALL CHECKS PASSED ===")
            else:
                print(f"\n  === SOME CHECKS FAILED ===")

        except Exception as e:
            print(f"      Error in completeness check: {e}")

    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Verify film database data integrity")
    parser.add_argument("--tmdb-id", type=int, default=None,
                        help="Verify a specific film by tmdb_id")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_verification(args))


if __name__ == "__main__":
    main()
