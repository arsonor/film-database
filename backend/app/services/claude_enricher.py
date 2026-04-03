"""
Claude AI enrichment service for the Film Database project.

Uses the Anthropic Claude API to classify films into the full custom taxonomy
(atmosphere, message, motivations, characters, cultural movement, etc.)
based on TMDB metadata.
"""

import asyncio
import json
import logging
from datetime import date

import anthropic

from .taxonomy_config import (
    REFERENCE_EXAMPLES,
    TAXONOMY_DIMENSIONS,
    VALID_SOURCE_TYPES,
)

logger = logging.getLogger(__name__)


# =============================================================================
# System prompt for film classification
# =============================================================================

ENRICHMENT_SYSTEM_PROMPT = """You are a film classification expert. Given metadata about a film, you classify it into a precise custom taxonomy. You must be accurate, thorough, and use your deep knowledge of cinema.

Core principles:
- ONLY use values from the provided valid value lists unless no existing value fits, in which case prefix new suggestions with [NEW].
- Be comprehensive: assign ALL relevant values, not just the most obvious ones.
- A dimension can have ZERO values if nothing is truly pertinent. Do not force tags. An empty list is better than a wrong tag.
- Provide a confidence score (0.0-1.0) for each dimension. Use lower scores when you're uncertain or the film is obscure.
- Respond ONLY with the JSON structure specified. No preamble, no markdown backticks.

Tag selection philosophy — tags must characterize the film as a whole:
- Each tag should represent a DEFINING or SIGNIFICANT aspect of the film, not an incidental detail.
- Ask yourself: "Would someone who has seen this film agree this tag defines it?" If it's just a passing scene or minor element, do NOT include it.
Ex:For themes like "death": only tag if death is a CENTRAL theme or narrative thread, not merely because a character dies incidentally.
- For motivations: "fight" applies when there are significant action/combat scenes (physical confrontations, battle sequences), not just metaphorical struggles.
- For cinema_type: include "Collection" if the film is part of a major franchise with sequels/prequels.
- For characters: apply 'ordinary' only if the film's characters are intentionally mundane, relatable and it represents the film's core values, not just because they aren't superheroes or historical figures.
Apply 'ensemble cast' only if the film truly has multiple main characters with significant screen time and narrative importance, not just a large cast of minor characters.

Source rules:
- Identify if based on a novel, true story, play, original screenplay, etc.
- For adaptations, include the source title and author when known.

Awards rules:
- Only include awards you are confident about. Fewer correct entries are better than invented ones.
- Focus on: Academy Awards, Cannes, Venice, Berlin, César, BAFTA, Golden Globes."""


class ClaudeEnricher:
    """Enriches film metadata with full taxonomy classification via Claude API."""

    MAX_RETRIES = 3

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.valid_sets = {
            dim: set(values) for dim, values in TAXONOMY_DIMENSIONS.items()
        }
        self.valid_source_types = set(VALID_SOURCE_TYPES)

    # -------------------------------------------------------------------------
    # Core enrichment method
    # -------------------------------------------------------------------------

    async def enrich_film(self, tmdb_mapped_data: dict) -> dict:
        """
        Classify a film into the full taxonomy using Claude.

        Args:
            tmdb_mapped_data: Output from TMDBMapper.map_film_to_db()

        Returns:
            Enrichment dict with taxonomy classifications, confidence scores,
            and any new value suggestions.
        """
        film = tmdb_mapped_data.get("film", {})
        title = film.get("original_title", "Unknown")
        tmdb_id = film.get("tmdb_id")

        logger.info("Enriching film: %s (tmdb_id=%s)", title, tmdb_id)

        prompt = self._build_user_prompt(tmdb_mapped_data)

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    system=ENRICHMENT_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text content
                text = response.content[0].text.strip()

                # Parse JSON — strip markdown fences if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()

                enrichment = json.loads(text)
                enrichment = self._validate_enrichment(enrichment)

                logger.info("Successfully enriched: %s", title)
                return enrichment

            except json.JSONDecodeError as e:
                logger.warning(
                    "JSON parse error for '%s' (attempt %d/%d): %s",
                    title, attempt + 1, self.MAX_RETRIES, e,
                )
                if attempt < self.MAX_RETRIES:
                    # Retry with stricter prompt
                    prompt = (
                        self._build_user_prompt(tmdb_mapped_data)
                        + "\n\nIMPORTANT: Your previous response was not valid JSON. "
                        "Respond with ONLY the JSON object, no markdown, no backticks, no explanation."
                    )
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue

            except anthropic.RateLimitError:
                backoff = 5.0 * (2 ** attempt)
                logger.warning(
                    "Rate limited for '%s', retrying in %.1fs (attempt %d/%d)",
                    title, backoff, attempt + 1, self.MAX_RETRIES,
                )
                await asyncio.sleep(backoff)
                continue

            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    backoff = 2.0 * (2 ** attempt)
                    logger.warning(
                        "API server error %d for '%s', retrying in %.1fs",
                        e.status_code, title, backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                logger.error("API error for '%s': %s", title, e)
                raise

            except Exception as e:
                logger.error("Unexpected error enriching '%s': %s", title, e)
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(2.0 * (2 ** attempt))
                    continue
                raise

        # All retries exhausted — return partial result
        logger.error("All retries exhausted for '%s', returning empty enrichment", title)
        return self._empty_enrichment()

    # -------------------------------------------------------------------------
    # Batch processing
    # -------------------------------------------------------------------------

    async def enrich_batch(
        self, films: list[dict], batch_size: int = 10
    ) -> list[dict]:
        """
        Enrich multiple films with progress tracking and checkpointing.

        Args:
            films: List of TMDBMapper.map_film_to_db() outputs.
            batch_size: Save checkpoint interval.

        Returns:
            List of enrichment results (same order as input).
        """
        results: list[dict] = []

        for i, film in enumerate(films):
            title = film.get("film", {}).get("original_title", "Unknown")
            logger.info("Enriching %d/%d: %s", i + 1, len(films), title)

            enrichment = await self.enrich_film(film)
            results.append(enrichment)

            # Brief pause between requests
            if i < len(films) - 1:
                await asyncio.sleep(0.5)

        return results

    # -------------------------------------------------------------------------
    # Review filtering
    # -------------------------------------------------------------------------

    @staticmethod
    def get_low_confidence_films(
        enrichments: list[dict], threshold: float = 0.6
    ) -> list[dict]:
        """
        Filter enrichments where any dimension has confidence below threshold.

        Returns list of enrichments that need human review.
        """
        flagged = []
        for enrichment in enrichments:
            confidence = enrichment.get("confidence", {})
            if not confidence:
                flagged.append(enrichment)
                continue

            for dim, score in confidence.items():
                if isinstance(score, (int, float)) and score < threshold:
                    flagged.append(enrichment)
                    break

        return flagged

    # -------------------------------------------------------------------------
    # Prompt building
    # -------------------------------------------------------------------------

    def _build_user_prompt(self, tmdb_mapped_data: dict) -> str:
        """Build the complete user prompt for a film enrichment request."""
        film = tmdb_mapped_data.get("film", {})
        crew = tmdb_mapped_data.get("crew", [])
        cast = tmdb_mapped_data.get("cast", [])
        categories = tmdb_mapped_data.get("categories", [])
        keywords = tmdb_mapped_data.get("keywords", [])
        production_countries = tmdb_mapped_data.get("production_countries", [])
        languages = tmdb_mapped_data.get("languages", [])

        # Extract director(s)
        directors = [
            f"{c['firstname']} {c['lastname']}" for c in crew if c.get("role") == "Director"
        ]

        # Top cast with characters
        cast_lines = [
            f"{c['firstname']} {c['lastname']} as {c.get('character_name', '?')}"
            for c in cast[:10]
        ]

        # Format release date
        release_date = film.get("first_release_date", "")
        year = ""
        if isinstance(release_date, date):
            year = str(release_date.year)
        elif isinstance(release_date, str) and len(release_date) >= 4:
            year = release_date[:4]

        # Budget/revenue
        budget_str = f"${film['budget']:,}" if film.get("budget") else "Unknown"
        revenue_str = f"${film['revenue']:,}" if film.get("revenue") else "Unknown"

        # Build taxonomy section
        taxonomy_section = self._build_taxonomy_section()

        # Build reference examples
        examples_section = self._build_examples_section()

        prompt = f"""Classify this film into the taxonomy below.

## Film Metadata
- Title: {film.get('original_title', 'Unknown')}
- Year: {year}
- Overview: {film.get('summary', 'No overview available')}
- TMDB Genres: {', '.join(categories) if categories else 'N/A'}
- TMDB Keywords: {', '.join(keywords[:20]) if keywords else 'N/A'}
- Director: {', '.join(directors) if directors else 'Unknown'}
- Key Cast: {'; '.join(cast_lines) if cast_lines else 'N/A'}
- Production Countries: {', '.join(production_countries) if production_countries else 'N/A'}
- Budget: {budget_str} | Revenue: {revenue_str}
- Languages: {', '.join(lang.get('name', lang.get('code', '')) for lang in languages) if languages else 'N/A'}

{taxonomy_section}

{examples_section}

## Output Format
Respond with ONLY this JSON structure:
{{
  "categories": ["..."],
  "historic_subcategories": [],
  "cinema_type": ["..."],
  "time_context": ["..."],
  "geography": [
    {{"continent": "...", "country": "...", "state_city": "..." or null, "place_type": "diegetic|shooting|fictional"}}
  ],
  "place_environment": ["..."],
  "themes": ["..."],
  "character_context": ["..."],
  "atmosphere": ["..."],
  "motivations": ["..."],
  "message": ["..."],
  "source": {{
    "type": "...",
    "title": "..." or null,
    "author": "..." or null
  }},
  "awards": [
    {{"festival_name": "Academy Awards", "category": "Best Visual Effects", "year": 1969, "result": "won"}},
    {{"festival_name": "Academy Awards", "category": "Best Director", "year": 1969, "result": "nominated"}}
  ],
  "confidence": {{
    "categories": 0.0-1.0,
    "cinema_type": 0.0-1.0,
    "time_context": 0.0-1.0,
    "geography": 0.0-1.0,
    "place_environment": 0.0-1.0,
    "themes": 0.0-1.0,
    "character_context": 0.0-1.0,
    "atmosphere": 0.0-1.0,
    "motivations": 0.0-1.0,
    "message": 0.0-1.0,
    "source": 0.0-1.0,
    "awards": 0.0-1.0
  }},
  "new_values_suggested": []
}}"""

        return prompt

    def _build_taxonomy_section(self) -> str:
        """Build the taxonomy dimension section of the prompt."""
        dims = TAXONOMY_DIMENSIONS
        return f"""## Taxonomy Dimensions — Use ONLY these values (or prefix new ones with [NEW])

### Categories (pick all that apply)
Valid: {', '.join(dims['categories'])}
Historical sub-categories (only if "Historical" is selected): {', '.join(dims['historic_subcategories'])}

### Cinema Type (includes techniques, movements, and cultural eras)
Valid: {', '.join(dims['cinema_type'])}
Note: Use "Collection" for films that are part of a major franchise (sequels, prequels, shared universe).

### Time Context (when is the film set — can be multiple)
Valid: {', '.join(dims['time_context'])}
IMPORTANT: For films released after 2000 set in their present day, use ONLY "contemporary". Do NOT add "end 20th".

### Place Context — Geography
Provide as: continent > country > state/city
Specify place_type for each: diegetic (in-film), shooting (real location), or fictional

### Place Context — Environment (pick all that apply, but ONLY if they characterize the film's overall setting)
Valid: {', '.join(dims['place_environment'])}
IMPORTANT: "huis clos" = entire film confined to one space. "road movie" = journey structures the narrative. Other environments should be significant/recurring settings, not just briefly visited locations.

### Themes (pick all that apply — be thorough, but only CENTRAL themes)
Valid: {', '.join(dims['themes'])}
IMPORTANT: Each theme must be a defining aspect of the film. "death" = death is a central narrative thread, not just an incidental event.

### Characters (group structure, contexts, and archetypes — pick all that apply)
Valid: {', '.join(dims['character_context'])}
Note: "ordinary" only if the film's characters are intentionally mundane, relatable and it represents the film's core values, not just because they aren't superheroes or historical figures. "ensemble cast" only if the film truly has multiple main characters with significant screen time and narrative importance, not just a large cast of minor characters.

### Atmosphere (pick all that apply)
Valid: {', '.join(dims['atmosphere'])}

### Motivations & Relations (pick all that apply)
Valid: {', '.join(dims['motivations'])}
Note: "fight" = physical combat/action scenes are significant in the film.

### Message Conveyed (pick all that apply)
Valid: {', '.join(dims['message'])}

### Source / Origin
Type (one of): {', '.join(VALID_SOURCE_TYPES)}
Source title (if applicable):
Author (if applicable):

### Awards & Nominations
List the most significant awards and nominations for this film. Focus on:
- Academy Awards (Oscars)
- Cannes Film Festival (Palme d'Or, Grand Prix, Best Director, etc.)
- Venice Film Festival (Golden Lion, Grand Jury Prize, etc.)
- Berlin Film Festival (Golden Bear, Silver Bear, etc.)
- César Awards (for French films)
- BAFTA Awards
- Golden Globes
- Other major festivals or ceremonies if relevant

For each, provide: festival_name, category, year, result ("won" or "nominated").
Only include awards you are confident about. If unsure, include fewer rather than risk errors."""

    def _build_examples_section(self) -> str:
        """Build the few-shot reference examples section."""
        examples = []
        for key, ref in REFERENCE_EXAMPLES.items():
            enrichment = ref["enrichment"]
            examples.append(
                f"### Example: {ref['title']} ({ref['year']})\n"
                f"{json.dumps(enrichment, indent=2, default=str)}"
            )
        return "## Reference Examples\n\n" + "\n\n".join(examples)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _validate_enrichment(self, enrichment: dict) -> dict:
        """
        Validate enrichment output against known taxonomy values.

        - Removes invalid values (typos, hallucinations)
        - Collects [NEW] prefixed values into new_values_suggested
        - Ensures at least one value per required dimension
        """
        new_suggestions: list[str] = []

        # Validate list dimensions
        list_dims = [
            "categories", "cinema_type", "time_context",
            "place_environment", "themes", "character_context",
            "atmosphere", "motivations", "message",
        ]

        for dim in list_dims:
            values = enrichment.get(dim, [])
            if not isinstance(values, list):
                enrichment[dim] = []
                continue

            valid_set = self.valid_sets.get(dim, set())
            cleaned = []
            for v in values:
                if not isinstance(v, str):
                    continue
                if v.startswith("[NEW]"):
                    new_suggestions.append(f"{dim}: {v}")
                    cleaned.append(v)
                elif v in valid_set:
                    cleaned.append(v)
                else:
                    logger.warning("Invalid %s value removed: '%s'", dim, v)

            enrichment[dim] = cleaned

        # Validate historic_subcategories
        subcats = enrichment.get("historic_subcategories", [])
        if isinstance(subcats, list):
            valid_subcats = self.valid_sets.get("historic_subcategories", set())
            enrichment["historic_subcategories"] = [
                s for s in subcats if isinstance(s, str) and s in valid_subcats
            ]

        # Validate source
        source = enrichment.get("source", {})
        if isinstance(source, dict):
            src_type = source.get("type", "")
            if src_type and src_type not in self.valid_source_types:
                if src_type.startswith("[NEW]"):
                    new_suggestions.append(f"source_type: {src_type}")
                else:
                    logger.warning("Invalid source type removed: '%s'", src_type)
                    source["type"] = None
            enrichment["source"] = source
        else:
            enrichment["source"] = {"type": None, "title": None, "author": None}

        # Validate geography entries
        geography = enrichment.get("geography", [])
        if isinstance(geography, list):
            valid_place_types = {"diegetic", "shooting", "fictional"}
            cleaned_geo = []
            for g in geography:
                if isinstance(g, dict) and g.get("place_type") in valid_place_types:
                    cleaned_geo.append(g)
            enrichment["geography"] = cleaned_geo

        # Validate awards
        awards = enrichment.get("awards", [])
        if isinstance(awards, list):
            cleaned_awards = []
            for award in awards:
                if not isinstance(award, dict):
                    continue
                if not award.get("festival_name"):
                    continue
                if award.get("result") not in ("won", "nominated"):
                    continue
                if not isinstance(award.get("year"), (int, float)):
                    continue
                cleaned_awards.append({
                    "festival_name": award["festival_name"],
                    "category": award.get("category"),
                    "year": int(award["year"]),
                    "result": award["result"],
                })
            enrichment["awards"] = cleaned_awards
        else:
            enrichment["awards"] = []

        # Ensure confidence dict exists
        if "confidence" not in enrichment or not isinstance(enrichment.get("confidence"), dict):
            enrichment["confidence"] = {dim: 0.5 for dim in list_dims}
            enrichment["confidence"]["geography"] = 0.5
            enrichment["confidence"]["source"] = 0.5
            enrichment["confidence"]["awards"] = 0.5

        # Collect new value suggestions
        existing_suggestions = enrichment.get("new_values_suggested", [])
        if isinstance(existing_suggestions, list):
            new_suggestions.extend(existing_suggestions)
        enrichment["new_values_suggested"] = new_suggestions

        # Warn if required dimensions are empty
        required = ["categories", "themes", "atmosphere"]
        for dim in required:
            if not enrichment.get(dim):
                logger.warning("Required dimension '%s' is empty after validation", dim)

        return enrichment

    def _empty_enrichment(self) -> dict:
        """Return an empty enrichment with low confidence scores."""
        return {
            "categories": [],
            "historic_subcategories": [],
            "cinema_type": [],
            "time_context": [],
            "geography": [],
            "place_environment": [],
            "themes": [],
            "character_context": [],
            "atmosphere": [],
            "motivations": [],
            "message": [],
            "source": {"type": None, "title": None, "author": None},
            "awards": [],
            "confidence": {
                "categories": 0.0,
                "cinema_type": 0.0,
                "time_context": 0.0,
                "geography": 0.0,
                "place_environment": 0.0,
                "themes": 0.0,
                "character_context": 0.0,
                "atmosphere": 0.0,
                "motivations": 0.0,
                "message": 0.0,
                "source": 0.0,
                "awards": 0.0,
            },
            "new_values_suggested": [],
        }
