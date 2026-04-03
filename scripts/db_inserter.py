"""
Database insertion script for the Film Database project.

Takes enriched film data (TMDB + Claude taxonomy) and inserts everything
into the PostgreSQL database with full transactional integrity.

Usage:
    python scripts/db_inserter.py --input scripts/data/enriched_films.json --batch-size 20
    python scripts/db_inserter.py --dry-run
    python scripts/db_inserter.py --film-id 5
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        total = kwargs.get("total", None)
        desc = kwargs.get("desc", "")
        for i, item in enumerate(iterable):
            if total:
                print(f"\r{desc} {i + 1}/{total}", end="", flush=True)
            yield item
        print()

logger = logging.getLogger(__name__)


def load_json(path: Path) -> list:
    """Load a JSON file."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class DBInserter:
    """Inserts enriched film data into the PostgreSQL database."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.stats = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": [],
        }

    async def close(self):
        await self.engine.dispose()

    # -------------------------------------------------------------------------
    # Main insertion method — one film per transaction
    # -------------------------------------------------------------------------

    async def insert_film(self, film_data: dict, dry_run: bool = False) -> bool:
        """
        Insert a single film with all its relations into the database.

        Everything is wrapped in a single transaction — all or nothing.
        Returns True if successful, False otherwise.
        """
        film = film_data.get("film", {})
        enrichment = film_data.get("enrichment", {})
        tmdb_id = film.get("tmdb_id")
        title = film.get("original_title", "Unknown")

        if not tmdb_id:
            logger.warning("Skipping film without tmdb_id: %s", title)
            self.stats["skipped"] += 1
            return False

        if dry_run:
            warnings = self._validate_film_data(film_data)
            if warnings:
                for w in warnings:
                    logger.warning("[DRY-RUN] %s: %s", title, w)
                    self.stats["warnings"].append(f"{title}: {w}")
            else:
                logger.info("[DRY-RUN] %s — OK", title)
            return True

        async with self.session_factory() as session:
            async with session.begin():
                try:
                    # 1. Upsert film
                    film_id = await self._upsert_film(session, film)

                    # 2. Insert/find persons + crew junctions
                    await self._insert_crew(session, film_id, film_data.get("crew", []))

                    # 3. Insert casting
                    await self._insert_cast(session, film_id, film_data.get("cast", []))

                    # 4. Insert studios + production junctions
                    await self._insert_studios(session, film_id, film_data.get("studios", []))

                    # 5. Insert film_language records
                    await self._insert_titles(session, film_id, film_data.get("titles", []))

                    # 6. Insert film_genre junctions
                    categories = enrichment.get("categories") or film_data.get("categories", [])
                    historic_subs = enrichment.get("historic_subcategories") or film_data.get("historic_subcategories", [])
                    await self._insert_genres(session, film_id, categories, historic_subs)

                    # 7. Insert film_technique junctions (cinema types + movements merged)
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("cinema_type", []),
                        "cinema_type", "technique_name", "cinema_type_id",
                        "film_technique", "cinema_type_id",
                    )

                    # 9. Insert geography + film_set_place
                    await self._insert_geography(session, film_id, enrichment.get("geography", []))

                    # 10. Insert film_place (environments)
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("place_environment", []),
                        "place_context", "environment", "place_context_id",
                        "film_place", "place_context_id",
                    )

                    # 11. Insert film_period (time contexts)
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("time_context", []),
                        "time_context", "time_period", "time_context_id",
                        "film_period", "time_context_id",
                    )

                    # 12. Insert film_theme
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("themes", []),
                        "theme_context", "theme_name", "theme_context_id",
                        "film_theme", "theme_context_id",
                    )

                    # 13. Insert film_character_context (characters merged)
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("character_context", []),
                        "character_context", "context_name", "character_context_id",
                        "film_character_context", "character_context_id",
                    )

                    # 15. Insert film_atmosphere
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("atmosphere", []),
                        "atmosphere", "atmosphere_name", "atmosphere_id",
                        "film_atmosphere", "atmosphere_id",
                    )

                    # 16. Insert film_motivation
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("motivations", []),
                        "motivation_relation", "motivation_name", "motivation_id",
                        "film_motivation", "motivation_id",
                    )

                    # 17. Insert film_message
                    await self._insert_junction_by_name(
                        session, film_id,
                        enrichment.get("message", []),
                        "message_conveyed", "message_name", "message_id",
                        "film_message", "message_id",
                    )

                    # 18. Insert source + film_origin
                    await self._insert_source(session, film_id, enrichment.get("source"))

                    # 19. Insert awards
                    await self._insert_awards(session, film_id, enrichment.get("awards", []))

                    # 20. Insert streaming platforms
                    await self._insert_streaming(session, film_id, film_data.get("streaming_platforms", []))

                    # 21. Auto-link franchise sequels via tmdb_collection_id
                    await self._link_collection_siblings(session, film_id, film)

                    self.stats["inserted"] += 1
                    logger.info("Inserted: %s (film_id=%d)", title, film_id)
                    return True

                except Exception as e:
                    logger.error("Failed to insert '%s': %s", title, e)
                    self.stats["errors"] += 1
                    raise  # transaction will rollback

    # -------------------------------------------------------------------------
    # Upsert film core record
    # -------------------------------------------------------------------------

    async def _upsert_film(self, session: AsyncSession, film: dict) -> int:
        """Insert or update the film record. Returns film_id."""
        release_date = film.get("first_release_date")
        if isinstance(release_date, str) and release_date:
            try:
                release_date = date.fromisoformat(release_date)
            except ValueError:
                release_date = None

        # Check if film already exists
        result = await session.execute(
            text("SELECT film_id FROM film WHERE tmdb_id = :tmdb_id"),
            {"tmdb_id": film["tmdb_id"]},
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing film
            await session.execute(
                text("""
                    UPDATE film SET
                        original_title = :original_title,
                        duration = :duration,
                        color = :color,
                        first_release_date = :first_release_date,
                        summary = :summary,
                        poster_url = :poster_url,
                        backdrop_url = :backdrop_url,
                        imdb_id = :imdb_id,
                        budget = :budget,
                        revenue = :revenue,
                        tmdb_collection_id = :tmdb_collection_id
                    WHERE tmdb_id = :tmdb_id
                """),
                {
                    "original_title": film.get("original_title"),
                    "duration": film.get("duration"),
                    "color": film.get("color", True),
                    "first_release_date": release_date,
                    "summary": film.get("summary"),
                    "poster_url": film.get("poster_url"),
                    "backdrop_url": film.get("backdrop_url"),
                    "imdb_id": film.get("imdb_id"),
                    "budget": film.get("budget"),
                    "revenue": film.get("revenue"),
                    "tmdb_collection_id": film.get("tmdb_collection_id"),
                    "tmdb_id": film["tmdb_id"],
                },
            )
            self.stats["updated"] += 1
            # Delete existing junctions for clean re-insert
            await self._clear_junctions(session, existing)
            return existing

        # Insert new film
        result = await session.execute(
            text("""
                INSERT INTO film (
                    original_title, duration, color, first_release_date, summary,
                    poster_url, backdrop_url, imdb_id, tmdb_id, budget, revenue,
                    tmdb_collection_id
                ) VALUES (
                    :original_title, :duration, :color, :first_release_date, :summary,
                    :poster_url, :backdrop_url, :imdb_id, :tmdb_id, :budget, :revenue,
                    :tmdb_collection_id
                ) RETURNING film_id
            """),
            {
                "original_title": film.get("original_title"),
                "duration": film.get("duration"),
                "color": film.get("color", True),
                "first_release_date": release_date,
                "summary": film.get("summary"),
                "poster_url": film.get("poster_url"),
                "backdrop_url": film.get("backdrop_url"),
                "imdb_id": film.get("imdb_id"),
                "tmdb_id": film["tmdb_id"],
                "budget": film.get("budget"),
                "revenue": film.get("revenue"),
                "tmdb_collection_id": film.get("tmdb_collection_id"),
            },
        )
        return result.scalar_one()

    async def _clear_junctions(self, session: AsyncSession, film_id: int):
        """Clear all junction table entries for a film (for clean re-insert on update)."""
        junction_tables = [
            "crew", "casting", "production", "film_language",
            "film_genre", "film_technique", "film_set_place",
            "film_place", "film_period", "film_theme",
            "film_character_context", "film_atmosphere", "film_motivation",
            "film_message", "film_origin", "film_exploitation", "award",
        ]
        for table in junction_tables:
            await session.execute(
                text(f"DELETE FROM {table} WHERE film_id = :film_id"),
                {"film_id": film_id},
            )
        # film_sequel references film_id in both columns
        await session.execute(
            text("DELETE FROM film_sequel WHERE film_id = :fid OR related_film_id = :fid"),
            {"fid": film_id},
        )

    # -------------------------------------------------------------------------
    # Person find-or-create
    # -------------------------------------------------------------------------

    async def _find_or_create_person(
        self, session: AsyncSession, person: dict
    ) -> int:
        """Find or create a person by tmdb_id. Returns person_id."""
        tmdb_id = person.get("tmdb_id")
        if tmdb_id:
            result = await session.execute(
                text("SELECT person_id FROM person WHERE tmdb_id = :tmdb_id"),
                {"tmdb_id": tmdb_id},
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        # Insert new person
        result = await session.execute(
            text("""
                INSERT INTO person (firstname, lastname, tmdb_id, photo_url, gender)
                VALUES (:firstname, :lastname, :tmdb_id, :photo_url, :gender)
                ON CONFLICT (tmdb_id) DO UPDATE SET
                    firstname = EXCLUDED.firstname,
                    lastname = EXCLUDED.lastname,
                    photo_url = COALESCE(EXCLUDED.photo_url, person.photo_url),
                    gender = COALESCE(EXCLUDED.gender, person.gender)
                RETURNING person_id
            """),
            {
                "firstname": person.get("firstname", ""),
                "lastname": person.get("lastname", ""),
                "tmdb_id": tmdb_id,
                "photo_url": person.get("photo_url"),
                "gender": person.get("gender"),
            },
        )
        return result.scalar_one()

    # -------------------------------------------------------------------------
    # Crew insertion
    # -------------------------------------------------------------------------

    async def _insert_crew(
        self, session: AsyncSession, film_id: int, crew: list[dict]
    ):
        """Insert crew members and their junction records."""
        for member in crew:
            person_id = await self._find_or_create_person(session, member)

            # Look up job_id
            role = member.get("role")
            if not role:
                continue

            result = await session.execute(
                text("SELECT job_id FROM person_job WHERE role_name = :role"),
                {"role": role},
            )
            job_id = result.scalar_one_or_none()
            if not job_id:
                logger.warning("Unknown crew role: '%s'", role)
                continue

            await session.execute(
                text("""
                    INSERT INTO crew (film_id, person_id, job_id)
                    VALUES (:film_id, :person_id, :job_id)
                    ON CONFLICT DO NOTHING
                """),
                {"film_id": film_id, "person_id": person_id, "job_id": job_id},
            )

    # -------------------------------------------------------------------------
    # Cast insertion
    # -------------------------------------------------------------------------

    async def _insert_cast(
        self, session: AsyncSession, film_id: int, cast: list[dict]
    ):
        """Insert cast members and their casting records."""
        for member in cast:
            person_id = await self._find_or_create_person(session, member)

            await session.execute(
                text("""
                    INSERT INTO casting (film_id, person_id, character_name, cast_order)
                    VALUES (:film_id, :person_id, :character_name, :cast_order)
                """),
                {
                    "film_id": film_id,
                    "person_id": person_id,
                    "character_name": member.get("character_name", ""),
                    "cast_order": member.get("cast_order"),
                },
            )

    # -------------------------------------------------------------------------
    # Studios insertion
    # -------------------------------------------------------------------------

    async def _insert_studios(
        self, session: AsyncSession, film_id: int, studios: list[dict]
    ):
        """Insert studios and production junctions."""
        for studio in studios:
            name = studio.get("name")
            if not name:
                continue

            # Find or create studio
            result = await session.execute(
                text("SELECT studio_id FROM studio WHERE studio_name = :name"),
                {"name": name},
            )
            studio_id = result.scalar_one_or_none()

            if not studio_id:
                result = await session.execute(
                    text("""
                        INSERT INTO studio (studio_name, country_name)
                        VALUES (:name, :country)
                        RETURNING studio_id
                    """),
                    {"name": name, "country": studio.get("country", "")},
                )
                studio_id = result.scalar_one()

            await session.execute(
                text("""
                    INSERT INTO production (film_id, studio_id)
                    VALUES (:film_id, :studio_id)
                    ON CONFLICT DO NOTHING
                """),
                {"film_id": film_id, "studio_id": studio_id},
            )

    # -------------------------------------------------------------------------
    # Titles / Languages insertion
    # -------------------------------------------------------------------------

    async def _insert_titles(
        self, session: AsyncSession, film_id: int, titles: list[dict]
    ):
        """Insert film titles in various languages."""
        for title_entry in titles:
            code = title_entry.get("language_code", "")
            title_text = title_entry.get("title", "")
            if not code or not title_text:
                continue

            # Find or create language
            result = await session.execute(
                text("SELECT language_id FROM language WHERE language_code = :code"),
                {"code": code},
            )
            lang_id = result.scalar_one_or_none()

            if not lang_id:
                result = await session.execute(
                    text("""
                        INSERT INTO language (language_code, language_name)
                        VALUES (:code, :name)
                        ON CONFLICT (language_code) DO UPDATE SET language_name = EXCLUDED.language_name
                        RETURNING language_id
                    """),
                    {"code": code, "name": code},
                )
                lang_id = result.scalar_one()

            await session.execute(
                text("""
                    INSERT INTO film_language (film_id, language_id, film_title, is_original, has_dubbing)
                    VALUES (:film_id, :lang_id, :title, :is_original, FALSE)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "film_id": film_id,
                    "lang_id": lang_id,
                    "title": title_text,
                    "is_original": title_entry.get("is_original", False),
                },
            )

    # -------------------------------------------------------------------------
    # Genre insertion (special: handles subcategories)
    # -------------------------------------------------------------------------

    async def _insert_genres(
        self,
        session: AsyncSession,
        film_id: int,
        categories: list[str],
        historic_subcategories: list[str],
    ):
        """Insert film_genre junctions, handling historic subcategories."""
        for cat_name in categories:
            # For "Historical" with subcategories, insert each subcategory row
            if cat_name == "Historical" and historic_subcategories:
                for sub in historic_subcategories:
                    result = await session.execute(
                        text("""
                            SELECT category_id FROM category
                            WHERE category_name = :cat AND historic_subcategory_name = :sub
                        """),
                        {"cat": cat_name, "sub": sub},
                    )
                    cat_id = result.scalar_one_or_none()
                    if cat_id:
                        await session.execute(
                            text("""
                                INSERT INTO film_genre (film_id, category_id)
                                VALUES (:film_id, :cat_id)
                                ON CONFLICT DO NOTHING
                            """),
                            {"film_id": film_id, "cat_id": cat_id},
                        )
                    else:
                        logger.warning("Historic subcategory not found: %s/%s", cat_name, sub)

            # Always insert the base category too
            result = await session.execute(
                text("""
                    SELECT category_id FROM category
                    WHERE category_name = :cat AND historic_subcategory_name IS NULL
                """),
                {"cat": cat_name},
            )
            cat_id = result.scalar_one_or_none()
            if cat_id:
                await session.execute(
                    text("""
                        INSERT INTO film_genre (film_id, category_id)
                        VALUES (:film_id, :cat_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"film_id": film_id, "cat_id": cat_id},
                )
            else:
                logger.warning("Category not found in DB: '%s'", cat_name)

    # -------------------------------------------------------------------------
    # Geography insertion
    # -------------------------------------------------------------------------

    async def _insert_geography(
        self, session: AsyncSession, film_id: int, geography: list[dict]
    ):
        """Insert geography records and film_set_place junctions."""
        for geo in geography:
            if not isinstance(geo, dict):
                continue

            continent = geo.get("continent")
            country = geo.get("country")
            state_city = geo.get("state_city")
            place_type = geo.get("place_type", "diegetic")

            if place_type not in ("diegetic", "shooting", "fictional"):
                place_type = "diegetic"

            # Find or create geography entry
            result = await session.execute(
                text("""
                    SELECT geography_id FROM geography
                    WHERE continent IS NOT DISTINCT FROM :continent
                      AND country IS NOT DISTINCT FROM :country
                      AND state_city IS NOT DISTINCT FROM :state_city
                """),
                {"continent": continent, "country": country, "state_city": state_city},
            )
            geo_id = result.scalar_one_or_none()

            if not geo_id:
                result = await session.execute(
                    text("""
                        INSERT INTO geography (continent, country, state_city)
                        VALUES (:continent, :country, :state_city)
                        ON CONFLICT (continent, country, state_city) DO UPDATE
                            SET continent = EXCLUDED.continent
                        RETURNING geography_id
                    """),
                    {"continent": continent, "country": country, "state_city": state_city},
                )
                geo_id = result.scalar_one()

            await session.execute(
                text("""
                    INSERT INTO film_set_place (film_id, geography_id, place_type)
                    VALUES (:film_id, :geo_id, :place_type)
                    ON CONFLICT DO NOTHING
                """),
                {"film_id": film_id, "geo_id": geo_id, "place_type": place_type},
            )

    # -------------------------------------------------------------------------
    # Generic junction insertion by name lookup
    # -------------------------------------------------------------------------

    async def _insert_junction_by_name(
        self,
        session: AsyncSession,
        film_id: int,
        values: list[str],
        lookup_table: str,
        name_column: str,
        id_column: str,
        junction_table: str,
        junction_fk_column: str,
    ):
        """
        Generic method: for each value, look up its ID in the lookup table
        by name, then insert the junction record.
        """
        for value in values:
            if not isinstance(value, str) or not value:
                continue
            # Skip [NEW] suggestions
            if value.startswith("[NEW]"):
                continue

            result = await session.execute(
                text(f"SELECT {id_column} FROM {lookup_table} WHERE {name_column} = :name"),
                {"name": value},
            )
            lookup_id = result.scalar_one_or_none()

            if not lookup_id:
                logger.warning(
                    "Taxonomy value not found in %s.%s: '%s'",
                    lookup_table, name_column, value,
                )
                continue

            await session.execute(
                text(f"""
                    INSERT INTO {junction_table} (film_id, {junction_fk_column})
                    VALUES (:film_id, :lookup_id)
                    ON CONFLICT DO NOTHING
                """),
                {"film_id": film_id, "lookup_id": lookup_id},
            )

    # -------------------------------------------------------------------------
    # Source insertion
    # -------------------------------------------------------------------------

    async def _insert_source(
        self, session: AsyncSession, film_id: int, source: dict | None
    ):
        """Insert source and film_origin junction."""
        if not source or not isinstance(source, dict):
            return
        source_type = source.get("type")
        if not source_type:
            return

        # Insert source record
        result = await session.execute(
            text("""
                INSERT INTO source (source_type, source_title, author)
                VALUES (:type, :title, :author)
                RETURNING source_id
            """),
            {
                "type": source_type,
                "title": source.get("title"),
                "author": source.get("author"),
            },
        )
        source_id = result.scalar_one()

        await session.execute(
            text("""
                INSERT INTO film_origin (film_id, source_id)
                VALUES (:film_id, :source_id)
                ON CONFLICT DO NOTHING
            """),
            {"film_id": film_id, "source_id": source_id},
        )

    # -------------------------------------------------------------------------
    # Awards insertion
    # -------------------------------------------------------------------------

    async def _insert_awards(
        self, session: AsyncSession, film_id: int, awards: list[dict]
    ):
        """Insert award records for a film."""
        for award in awards:
            if not isinstance(award, dict):
                continue
            festival = award.get("festival_name")
            if not festival:
                continue

            result_val = award.get("result", "")
            if result_val not in ("won", "nominated"):
                continue

            await session.execute(
                text("""
                    INSERT INTO award (film_id, festival_name, category, award_year, result)
                    VALUES (:film_id, :festival, :category, :year, :result)
                """),
                {
                    "film_id": film_id,
                    "festival": festival,
                    "category": award.get("category"),
                    "year": award.get("year"),
                    "result": result_val,
                },
            )

    # -------------------------------------------------------------------------
    # Streaming insertion
    # -------------------------------------------------------------------------

    async def _insert_streaming(
        self, session: AsyncSession, film_id: int, platforms: list[str]
    ):
        """Insert streaming platform junctions for a film."""
        for platform_name in platforms:
            if not platform_name:
                continue
            result = await session.execute(
                text("SELECT platform_id FROM stream_platform WHERE platform_name = :name"),
                {"name": platform_name},
            )
            platform_id = result.scalar_one_or_none()
            if not platform_id:
                logger.warning("Unknown streaming platform: '%s'", platform_name)
                continue
            await session.execute(
                text("""
                    INSERT INTO film_exploitation (film_id, platform_id)
                    VALUES (:film_id, :platform_id)
                    ON CONFLICT DO NOTHING
                """),
                {"film_id": film_id, "platform_id": platform_id},
            )

    # -------------------------------------------------------------------------
    # Franchise sequel auto-linking
    # -------------------------------------------------------------------------

    async def _link_collection_siblings(
        self, session: AsyncSession, film_id: int, film: dict
    ):
        """Auto-link films in the same TMDB collection via film_sequel."""
        collection_id = film.get("tmdb_collection_id")
        if not collection_id:
            return

        result = await session.execute(
            text("SELECT film_id FROM film WHERE tmdb_collection_id = :cid AND film_id != :fid"),
            {"cid": collection_id, "fid": film_id},
        )
        sibling_ids = [row[0] for row in result.fetchall()]

        for sibling_id in sibling_ids:
            await session.execute(
                text("""
                    INSERT INTO film_sequel (film_id, related_film_id, relation_type)
                    VALUES (:fid, :rid, 'sequel')
                    ON CONFLICT DO NOTHING
                """),
                {"fid": min(sibling_id, film_id), "rid": max(sibling_id, film_id)},
            )

        if sibling_ids:
            logger.info("Linked %d franchise siblings for film_id=%d (collection=%d)",
                        len(sibling_ids), film_id, collection_id)

    # -------------------------------------------------------------------------
    # Dry-run validation
    # -------------------------------------------------------------------------

    def _validate_film_data(self, film_data: dict) -> list[str]:
        """Validate film data without inserting. Returns list of warnings."""
        warnings = []
        film = film_data.get("film", {})
        enrichment = film_data.get("enrichment", {})

        if not film.get("tmdb_id"):
            warnings.append("Missing tmdb_id")
        if not film.get("original_title"):
            warnings.append("Missing original_title")

        # Check taxonomy values against known lists
        from app.services.taxonomy_config import TAXONOMY_DIMENSIONS

        dim_to_enrichment_key = {
            "categories": "categories",
            "cinema_type": "cinema_type",
            "time_context": "time_context",
            "place_environment": "place_environment",
            "themes": "themes",
            "character_context": "character_context",
            "atmosphere": "atmosphere",
            "motivations": "motivations",
            "message": "message",
        }

        for dim, enr_key in dim_to_enrichment_key.items():
            valid_set = set(TAXONOMY_DIMENSIONS.get(dim, []))
            values = enrichment.get(enr_key, [])
            if isinstance(values, list):
                for v in values:
                    if isinstance(v, str) and not v.startswith("[NEW]") and v not in valid_set:
                        warnings.append(f"Unknown {dim} value: '{v}'")

        return warnings


# =============================================================================
# CLI
# =============================================================================

async def run_inserter(args):
    """Main insertion logic."""
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not set in .env")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    all_films = load_json(input_path)
    print(f"Loaded {len(all_films)} films from {input_path}")

    # Single film mode
    if args.film_id is not None:
        if args.film_id >= len(all_films):
            print(f"Error: film-id {args.film_id} out of range (max {len(all_films) - 1})")
            sys.exit(1)
        all_films = [all_films[args.film_id]]
        print(f"Processing single film at index {args.film_id}")

    inserter = DBInserter(database_url)

    try:
        if args.dry_run:
            print("DRY RUN — validating data without inserting")

        # Check which films already exist (for resume)
        existing_tmdb_ids = set()
        if not args.dry_run:
            async with inserter.session_factory() as session:
                result = await session.execute(text("SELECT tmdb_id FROM film WHERE tmdb_id IS NOT NULL"))
                existing_tmdb_ids = {row[0] for row in result.fetchall()}
            print(f"Films already in DB: {len(existing_tmdb_ids)}")

        processed = 0
        for i, film_data in enumerate(tqdm(all_films, total=len(all_films), desc="Inserting")):
            tmdb_id = film_data.get("film", {}).get("tmdb_id")

            # Skip already-inserted films (resume)
            if not args.dry_run and tmdb_id in existing_tmdb_ids:
                inserter.stats["skipped"] += 1
                continue

            try:
                await inserter.insert_film(film_data, dry_run=args.dry_run)
            except Exception as e:
                title = film_data.get("film", {}).get("original_title", "Unknown")
                logger.error("Error inserting '%s': %s", title, e)
                inserter.stats["errors"] += 1

            processed += 1

            # Checkpoint logging
            if processed % args.batch_size == 0:
                logger.info(
                    "Progress: %d processed, %d inserted, %d errors",
                    processed, inserter.stats["inserted"], inserter.stats["errors"],
                )

        # Print summary
        print("\n" + "=" * 60)
        print("INSERTION SUMMARY")
        print("=" * 60)
        print(f"Inserted:  {inserter.stats['inserted']}")
        print(f"Updated:   {inserter.stats['updated']}")
        print(f"Skipped:   {inserter.stats['skipped']}")
        print(f"Errors:    {inserter.stats['errors']}")

        if inserter.stats["warnings"]:
            print(f"\nWarnings ({len(inserter.stats['warnings'])}):")
            for w in inserter.stats["warnings"][:20]:
                print(f"  - {w}")
            if len(inserter.stats["warnings"]) > 20:
                print(f"  ... and {len(inserter.stats['warnings']) - 20} more")

        print("=" * 60)

    finally:
        await inserter.close()


def main():
    parser = argparse.ArgumentParser(description="Insert enriched films into PostgreSQL")
    parser.add_argument(
        "--input",
        default="scripts/data/enriched_films.json",
        help="Path to enriched_films.json (default: scripts/data/enriched_films.json)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Log progress every N films (default: 20)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without inserting into DB",
    )
    parser.add_argument(
        "--film-id",
        type=int,
        default=None,
        help="Insert a single film by its index in the JSON array",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_inserter(args))


if __name__ == "__main__":
    main()
