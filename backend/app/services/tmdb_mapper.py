"""
TMDB data mapper for the Film Database project.

Transforms raw TMDB API responses into structures matching
the database schema for direct insertion.
"""

import logging
from datetime import date

from .tmdb_service import TMDBService

logger = logging.getLogger(__name__)

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

# TMDB gender codes → our DB gender values
# TMDB: 0=not set, 1=female, 2=male, 3=non-binary
TMDB_GENDER_MAP = {1: "F", 2: "M"}


class TMDBMapper:
    """Maps raw TMDB data into database-ready structures."""

    def __init__(self, tmdb_service: TMDBService):
        self.tmdb = tmdb_service

    async def map_film_to_db(
        self, tmdb_data: dict, fr_data: dict | None = None
    ) -> dict:
        """
        Transform raw TMDB details into a structured dict ready for DB insertion.

        Args:
            tmdb_data: Result from TMDBService.get_film_details() (en-US locale).
            fr_data: Optional result from TMDBService.get_film_details_fr() for French data.

        Returns:
            Dict matching the database schema with keys:
            film, titles, categories, historic_subcategories, crew, cast,
            studios, languages, keywords, production_countries.
        """
        # --- Film core ---
        poster_url = await self.tmdb.build_poster_url(tmdb_data.get("poster_path"))
        backdrop_url = await self.tmdb.build_poster_url(
            tmdb_data.get("backdrop_path"), size="w780"
        )

        budget = tmdb_data.get("budget", 0)
        revenue = tmdb_data.get("revenue", 0)
        vote_average = tmdb_data.get("vote_average")
        vote_count = tmdb_data.get("vote_count")

        first_release_date = None
        release_str = tmdb_data.get("release_date", "")
        if release_str:
            try:
                first_release_date = date.fromisoformat(release_str)
            except ValueError:
                logger.warning("Invalid release date: %s", release_str)

        film = {
            "original_title": tmdb_data.get("original_title", ""),
            "duration": tmdb_data.get("runtime"),
            "color": True,  # default, can be overridden later
            "first_release_date": first_release_date,
            "summary": tmdb_data.get("overview", ""),
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "imdb_id": tmdb_data.get("imdb_id"),
            "tmdb_id": tmdb_data.get("tmdb_id"),
            "budget": budget if budget else None,   # 0 → None (unknown)
            "revenue": revenue if revenue else None,  # 0 → None (unknown)
            "tmdb_score": vote_average,
            "tmdb_vote_count": vote_count,
        }

        # --- Collection (franchise) ---
        collection = tmdb_data.get("belongs_to_collection")
        if collection and isinstance(collection, dict):
            film["tmdb_collection_id"] = collection.get("id")
        else:
            film["tmdb_collection_id"] = None

        # --- Titles ---
        titles = self._build_titles(tmdb_data, fr_data)

        # --- Categories ---
        categories, historic_subcategories = self._map_genres(tmdb_data)

        # --- Crew (deduplicated) ---
        crew = self._map_crew(tmdb_data)

        # --- Cast (top 15) ---
        cast = self._map_cast(tmdb_data)

        # --- Studios ---
        studios = [
            {
                "name": pc.get("name", ""),
                "country": pc.get("origin_country", ""),
            }
            for pc in tmdb_data.get("production_companies", [])
        ]

        # --- Languages ---
        languages = [
            {
                "code": sl.get("iso_639_1", ""),
                "name": sl.get("english_name") or sl.get("name", ""),
            }
            for sl in tmdb_data.get("spoken_languages", [])
        ]

        # --- Keywords ---
        keywords = [kw["name"] for kw in tmdb_data.get("keywords", [])]

        # --- Production countries ---
        production_countries = [
            pc["iso_3166_1"] for pc in tmdb_data.get("production_countries", [])
        ]

        return {
            "film": film,
            "titles": titles,
            "categories": categories,
            "historic_subcategories": historic_subcategories,
            "crew": crew,
            "cast": cast,
            "studios": studios,
            "languages": languages,
            "keywords": keywords,
            "production_countries": production_countries,
            # This field is populated separately via get_watch_providers()
            # It's included in the structure for completeness but defaults to empty
            "streaming_platforms": [],
        }

    def map_watch_providers(self, providers: list[dict]) -> list[str]:
        """
        Map TMDB watch provider names to our stream_platform names.
        Only returns "flatrate" (subscription streaming) providers that match our platforms.

        Returns list of platform names matching our stream_platform table.
        """
        platforms = []
        seen = set()
        for p in providers:
            if p.get("provider_type") != "flatrate":
                continue
            name = p.get("provider_name", "")
            mapped = PROVIDER_NAME_MAP.get(name)
            if mapped and mapped not in seen:
                seen.add(mapped)
                platforms.append(mapped)
        return platforms

    def _build_titles(self, tmdb_data: dict, fr_data: dict | None) -> list[dict]:
        """
        Build title list: original language + English + French.

        Avoids duplicates if original language is already English or French.
        """
        original_lang = tmdb_data.get("original_language", "")
        original_title = tmdb_data.get("original_title", "")
        en_title = tmdb_data.get("title", "")

        # French title: prefer fr_data.title, fallback to french_title from translations
        fr_title = None
        if fr_data:
            fr_title = fr_data.get("title")
        if not fr_title:
            fr_title = tmdb_data.get("french_title")

        titles: list[dict] = []
        seen: set[tuple[str, str]] = set()

        def _add(code: str, title: str, is_original: bool):
            key = (code, title)
            if title and key not in seen:
                seen.add(key)
                titles.append({
                    "language_code": code,
                    "title": title,
                    "is_original": is_original,
                })

        # Original language title
        _add(original_lang, original_title, True)

        # English title (not original unless original_language is "en")
        _add("en", en_title, original_lang == "en")

        # French title
        if fr_title:
            _add("fr", fr_title, original_lang == "fr")

        return titles

    def _map_genres(self, tmdb_data: dict) -> tuple[list[str], list[str]]:
        """
        Map TMDB genres to our categories and historic subcategories.

        Returns (categories, historic_subcategories).
        """
        categories: list[str] = []
        historic_subcategories: list[str] = []
        seen_categories: set[str] = set()

        for genre in tmdb_data.get("genres", []):
            mapping = TMDBService.map_tmdb_genre_to_category(genre["name"])
            cat = mapping["category"]
            if cat and cat not in seen_categories:
                seen_categories.add(cat)
                categories.append(cat)
            if mapping["subcategory"]:
                historic_subcategories.append(mapping["subcategory"])

        return categories, historic_subcategories

    def _map_crew(self, tmdb_data: dict) -> list[dict]:
        """
        Map TMDB crew to our schema, deduplicated by (tmdb_id, role).

        A person appearing multiple times with different TMDB jobs that map
        to the same role (e.g., Writer + Screenplay → both "Writer") is
        kept once per role.
        """
        crew: list[dict] = []
        seen: set[tuple[int, str]] = set()

        for member in tmdb_data.get("crew", []):
            role = TMDBService.map_tmdb_job_to_role(member.get("job", ""))
            if not role:
                continue

            tmdb_id = member["id"]
            key = (tmdb_id, role)
            if key in seen:
                continue
            seen.add(key)

            firstname, lastname = TMDBService.split_person_name(member.get("name", ""))
            photo_url = None
            if member.get("profile_path"):
                photo_url = f"https://image.tmdb.org/t/p/w185{member['profile_path']}"

            crew.append({
                "firstname": firstname,
                "lastname": lastname,
                "tmdb_id": tmdb_id,
                "role": role,
                "photo_url": photo_url,
                "gender": TMDB_GENDER_MAP.get(member.get("gender")),
            })

        return crew

    def _map_cast(self, tmdb_data: dict) -> list[dict]:
        """Map TMDB cast (already top 15) to our schema."""
        cast: list[dict] = []

        for member in tmdb_data.get("cast", []):
            firstname, lastname = TMDBService.split_person_name(member.get("name", ""))
            photo_url = None
            if member.get("profile_path"):
                photo_url = f"https://image.tmdb.org/t/p/w185{member['profile_path']}"

            cast.append({
                "firstname": firstname,
                "lastname": lastname,
                "tmdb_id": member["id"],
                "character_name": member.get("character", ""),
                "cast_order": member.get("order", 999),
                "photo_url": photo_url,
                "gender": TMDB_GENDER_MAP.get(member.get("gender")),
            })

        return cast
