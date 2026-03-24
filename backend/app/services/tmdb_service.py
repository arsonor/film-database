"""
TMDB API client for the Film Database project.

Async client with rate limiting, retry logic, and mapping utilities
for resolving film titles and pulling complete metadata from TMDB.
"""

import asyncio
import logging
import time
from collections import deque

import httpx

logger = logging.getLogger(__name__)


class TMDBError(Exception):
    """Custom exception for TMDB API errors."""

    def __init__(self, message: str, status_code: int | None = None, tmdb_id: int | None = None):
        self.status_code = status_code
        self.tmdb_id = tmdb_id
        super().__init__(message)


class TMDBService:
    """Full-featured async TMDB API client with rate limiting."""

    # Rate limit: max 40 requests per 10 seconds
    RATE_LIMIT_REQUESTS = 40
    RATE_LIMIT_WINDOW = 10.0  # seconds
    MAX_RETRIES = 3

    # TMDB genre name → our category name
    GENRE_TO_CATEGORY: dict[str, str | None] = {
        "Action": "Action",
        "Adventure": "Adventure",
        "Comedy": "Comedy",
        "Drama": "Drama",
        "Romance": "Romance",
        "Thriller": "Thriller",
        "Horror": "Horror",
        "Science Fiction": "Science-Fiction",
        "Fantasy": "Fantasy",
        "Music": "Musical",
        "History": "Historical",
        "War": "Historical",  # also mapped to war theme
        "Crime": None,        # mapped to theme, not category
        "Mystery": None,      # mapped to theme
        "Documentary": None,  # not in our categories
        "Animation": None,    # mapped to cinema_type
        "Family": None,
        "Western": "Historical",  # with subcategory "western"
        "TV Movie": None,
    }

    # TMDB crew job → our person_job role_name
    JOB_TO_ROLE: dict[str, str] = {
        "Director": "Director",
        "Writer": "Writer",
        "Screenplay": "Writer",
        "Story": "Writer",
        "Director of Photography": "Cinematographer",
        "Original Music Composer": "Composer",
        "Music": "Composer",
        "Producer": "Producer",
        "Executive Producer": "Producer",
        "Editor": "Editor",
        "Production Design": "Art Director",
        "Costume Design": "Costume Designer",
        "Sound": "Sound Designer",
        "Sound Designer": "Sound Designer",
    }

    # Key crew jobs to extract from TMDB credits
    KEY_CREW_JOBS = set(JOB_TO_ROLE.keys())

    def __init__(self, api_key: str, base_url: str = "https://api.themoviedb.org/3"):
        self.api_key = api_key
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self._request_timestamps: deque[float] = deque()
        self._rate_lock = asyncio.Lock()

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # -------------------------------------------------------------------------
    # Rate limiting & HTTP
    # -------------------------------------------------------------------------

    async def _wait_for_rate_limit(self):
        """Enforce sliding window rate limit: max 40 requests per 10 seconds."""
        async with self._rate_lock:
            now = time.monotonic()
            # Remove timestamps outside the window
            while self._request_timestamps and self._request_timestamps[0] < now - self.RATE_LIMIT_WINDOW:
                self._request_timestamps.popleft()

            if len(self._request_timestamps) >= self.RATE_LIMIT_REQUESTS:
                # Must wait until the oldest request exits the window
                wait_time = self._request_timestamps[0] + self.RATE_LIMIT_WINDOW - now + 0.1
                logger.warning("Rate limit approaching, sleeping %.2f seconds", wait_time)
                await asyncio.sleep(wait_time)

            self._request_timestamps.append(time.monotonic())

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Make an HTTP request to TMDB with rate limiting and retry logic.

        Retries on 429 (rate limit) and 5xx errors with exponential backoff.
        Raises TMDBError on 404 and other client errors.
        """
        params = kwargs.pop("params", {})
        params["api_key"] = self.api_key

        for attempt in range(self.MAX_RETRIES + 1):
            await self._wait_for_rate_limit()
            try:
                response = await self._client.request(method, path, params=params, **kwargs)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    # Rate limited by TMDB — back off
                    retry_after = float(response.headers.get("Retry-After", 2))
                    backoff = retry_after * (2 ** attempt)
                    logger.warning("TMDB 429 rate limit hit, retrying in %.1fs (attempt %d/%d)",
                                   backoff, attempt + 1, self.MAX_RETRIES)
                    await asyncio.sleep(backoff)
                    continue

                if response.status_code >= 500:
                    backoff = (2 ** attempt) * 1.0
                    logger.warning("TMDB %d server error, retrying in %.1fs (attempt %d/%d)",
                                   response.status_code, backoff, attempt + 1, self.MAX_RETRIES)
                    await asyncio.sleep(backoff)
                    continue

                if response.status_code == 404:
                    raise TMDBError(
                        f"TMDB resource not found: {path}",
                        status_code=404,
                    )

                # Other client errors (400, 401, 403, etc.)
                raise TMDBError(
                    f"TMDB API error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            except httpx.RequestError as exc:
                if attempt < self.MAX_RETRIES:
                    backoff = (2 ** attempt) * 1.0
                    logger.warning("Request error: %s, retrying in %.1fs", exc, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise TMDBError(f"Request failed after {self.MAX_RETRIES} retries: {exc}")

        raise TMDBError(f"Max retries ({self.MAX_RETRIES}) exceeded for {path}")

    # -------------------------------------------------------------------------
    # Core API methods
    # -------------------------------------------------------------------------

    async def search_film(
        self, title: str, year: int | None = None, language: str = "en-US"
    ) -> list[dict]:
        """
        Search TMDB by title, optionally filtered by year.

        Tries the given language first; if no results, retries with the other
        locale (fr-FR or en-US) to handle French-titled films.
        """
        async def _do_search(lang: str) -> list[dict]:
            params: dict = {"query": title, "language": lang}
            if year:
                params["year"] = year
            data = await self._request("GET", "/search/movie", params=params)
            return data.get("results", [])

        # Try primary language
        results = await _do_search(language)

        # Fallback to the other language if no results
        if not results:
            fallback = "fr-FR" if language == "en-US" else "en-US"
            results = await _do_search(fallback)

        # Format results
        return [
            {
                "tmdb_id": r["id"],
                "title": r.get("title", ""),
                "original_title": r.get("original_title", ""),
                "release_date": r.get("release_date", ""),
                "overview": r.get("overview", ""),
                "poster_path": r.get("poster_path"),
                "popularity": r.get("popularity", 0),
            }
            for r in results
        ]

    async def get_film_details(self, tmdb_id: int, language: str = "en-US") -> dict:
        """
        Get comprehensive film details from TMDB.

        Appends credits, keywords, releases, and translations in a single call.
        """
        data = await self._request(
            "GET",
            f"/movie/{tmdb_id}",
            params={
                "language": language,
                "append_to_response": "credits,keywords,releases,translations",
            },
        )

        # Extract French title from translations
        french_title = None
        translations = data.get("translations", {}).get("translations", [])
        for t in translations:
            if t.get("iso_639_1") == "fr":
                french_title = t.get("data", {}).get("title")
                break

        # Filter crew to key roles only
        all_crew = data.get("credits", {}).get("crew", [])
        filtered_crew = [
            {
                "id": c["id"],
                "name": c.get("name", ""),
                "job": c.get("job", ""),
                "department": c.get("department", ""),
                "profile_path": c.get("profile_path"),
                "gender": c.get("gender"),
            }
            for c in all_crew
            if c.get("job") in self.KEY_CREW_JOBS
        ]

        # Top 15 cast
        all_cast = data.get("credits", {}).get("cast", [])
        top_cast = [
            {
                "id": c["id"],
                "name": c.get("name", ""),
                "character": c.get("character", ""),
                "order": c.get("order", 999),
                "profile_path": c.get("profile_path"),
                "gender": c.get("gender"),
            }
            for c in sorted(all_cast, key=lambda x: x.get("order", 999))[:15]
        ]

        return {
            # Core
            "tmdb_id": data["id"],
            "imdb_id": data.get("imdb_id"),
            "original_title": data.get("original_title", ""),
            "title": data.get("title", ""),
            "overview": data.get("overview", ""),
            "runtime": data.get("runtime"),
            "release_date": data.get("release_date", ""),
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "budget": data.get("budget", 0),
            "revenue": data.get("revenue", 0),
            "status": data.get("status", ""),
            "original_language": data.get("original_language", ""),
            # Genres
            "genres": [{"id": g["id"], "name": g["name"]} for g in data.get("genres", [])],
            # Production
            "production_companies": [
                {"id": pc["id"], "name": pc["name"], "origin_country": pc.get("origin_country", "")}
                for pc in data.get("production_companies", [])
            ],
            "production_countries": [
                {"iso_3166_1": pc["iso_3166_1"], "name": pc["name"]}
                for pc in data.get("production_countries", [])
            ],
            # Languages
            "spoken_languages": [
                {
                    "iso_639_1": sl.get("iso_639_1", ""),
                    "name": sl.get("name", ""),
                    "english_name": sl.get("english_name", ""),
                }
                for sl in data.get("spoken_languages", [])
            ],
            # Credits
            "cast": top_cast,
            "crew": filtered_crew,
            # Keywords
            "keywords": [
                {"id": kw["id"], "name": kw["name"]}
                for kw in data.get("keywords", {}).get("keywords", [])
            ],
            # French title
            "french_title": french_title,
        }

    async def get_watch_providers(self, tmdb_id: int, country: str = "FR") -> list[dict]:
        """
        Get streaming/watch providers for a film in a specific country.

        Uses TMDB's /movie/{id}/watch/providers endpoint.

        Args:
            tmdb_id: TMDB film ID
            country: ISO 3166-1 country code (default "FR" for France)

        Returns:
            List of dicts with keys: provider_name, provider_type ("flatrate", "rent", "buy")
            "flatrate" = subscription streaming (Netflix, etc.)
            "rent" = digital rental
            "buy" = digital purchase

            We primarily care about "flatrate" (streaming subscriptions).
        """
        data = await self._request("GET", f"/movie/{tmdb_id}/watch/providers")

        results = data.get("results", {})
        country_data = results.get(country, {})

        providers = []
        for provider_type in ["flatrate", "rent", "buy"]:
            for p in country_data.get(provider_type, []):
                providers.append({
                    "provider_name": p.get("provider_name", ""),
                    "provider_type": provider_type,
                    "logo_path": p.get("logo_path"),
                })

        return providers

    async def get_film_details_fr(self, tmdb_id: int) -> dict:
        """Convenience: get film details with French locale."""
        return await self.get_film_details(tmdb_id, language="fr-FR")

    async def get_person_details(self, person_tmdb_id: int) -> dict:
        """
        Get person details from TMDB.

        Returns structured data with name split into firstname/lastname.
        """
        data = await self._request("GET", f"/person/{person_tmdb_id}")
        firstname, lastname = self.split_person_name(data.get("name", ""))
        return {
            "tmdb_id": data["id"],
            "firstname": firstname,
            "lastname": lastname,
            "gender": data.get("gender"),
            "birthday": data.get("birthday"),
            "deathday": data.get("deathday"),
            "place_of_birth": data.get("place_of_birth"),
            "profile_path": data.get("profile_path"),
            "imdb_id": data.get("imdb_id"),
            "known_for_department": data.get("known_for_department"),
        }

    async def build_poster_url(self, poster_path: str | None, size: str = "w500") -> str | None:
        """
        Build full poster URL from TMDB path.

        Sizes: w92, w154, w185, w342, w500, w780, original
        """
        if not poster_path:
            return None
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"

    async def resolve_title(
        self, title: str, year: int | None = None
    ) -> dict | None:
        """
        High-level title resolution: search TMDB in both locales,
        filter by year (±1 tolerance), pick best match by popularity,
        and return full details.

        Returns full details dict or None if no unambiguous match.
        """
        # Search in both locales
        candidates_fr = await self.search_film(title, year=year, language="fr-FR")
        candidates_en = await self.search_film(title, year=year, language="en-US")

        # Merge and deduplicate by tmdb_id
        seen_ids: set[int] = set()
        candidates: list[dict] = []
        for c in candidates_fr + candidates_en:
            if c["tmdb_id"] not in seen_ids:
                seen_ids.add(c["tmdb_id"])
                candidates.append(c)

        if not candidates:
            logger.info("No TMDB candidates found for '%s' (year=%s)", title, year)
            return None

        # Filter by year if provided (±1 year tolerance)
        if year:
            year_filtered = []
            for c in candidates:
                release = c.get("release_date", "")
                if release and len(release) >= 4:
                    try:
                        release_year = int(release[:4])
                        if abs(release_year - year) <= 1:
                            year_filtered.append(c)
                    except ValueError:
                        pass
            if year_filtered:
                candidates = year_filtered

        if not candidates:
            logger.info("No TMDB matches within year tolerance for '%s' (year=%s)", title, year)
            return None

        # Pick by highest popularity
        best = max(candidates, key=lambda c: c.get("popularity", 0))

        # Get full details
        try:
            details = await self.get_film_details(best["tmdb_id"])
            return details
        except TMDBError as e:
            logger.error("Failed to get details for tmdb_id=%d: %s", best["tmdb_id"], e)
            return None

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------

    @staticmethod
    def split_person_name(full_name: str) -> tuple[str, str]:
        """
        Split a full name into (firstname, lastname).

        Handles edge cases:
        - Single name → ("", name)
        - Multiple parts → last word is lastname, rest is firstname
        """
        parts = full_name.strip().split()
        if not parts:
            return ("", "")
        if len(parts) == 1:
            return ("", parts[0])
        return (" ".join(parts[:-1]), parts[-1])

    @classmethod
    def map_tmdb_genre_to_category(cls, tmdb_genre: str) -> dict[str, str | None]:
        """
        Map a TMDB genre name to our category system.

        Returns dict with:
        - "category": our category name or None
        - "subcategory": historic subcategory if applicable
        - "note": additional info (e.g., "war" for War genre, "animation" for Animation)
        """
        category = cls.GENRE_TO_CATEGORY.get(tmdb_genre)
        result: dict[str, str | None] = {
            "category": category,
            "subcategory": None,
            "note": None,
        }
        if tmdb_genre == "Western":
            result["subcategory"] = "western"
        if tmdb_genre == "War":
            result["note"] = "war"
        if tmdb_genre == "Crime":
            result["note"] = "crime"
        if tmdb_genre == "Mystery":
            result["note"] = "investigation"
        if tmdb_genre == "Animation":
            result["note"] = "animation"
        if tmdb_genre == "Documentary":
            result["note"] = "documentary"
        return result

    @classmethod
    def map_tmdb_job_to_role(cls, tmdb_job: str) -> str | None:
        """Map a TMDB crew job title to our person_job role_name."""
        return cls.JOB_TO_ROLE.get(tmdb_job)
