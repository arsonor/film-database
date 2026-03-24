# Claude Code Prompts — Step-by-step

## Step 1 Prompt — PostgreSQL Schema Creation ✅ DONE

*(see git history for original prompt)*

---

## Step 2 Prompt — TMDB Integration Module ✅ DONE

*(see git history for original prompt)*

---

## Step 3 Prompt — Claude Enrichment Module ✅ DONE

*(see git history for original prompt)*

---

## Step 4 Prompt — Seed 3 Reference Films ✅ DONE

*(see git history for original prompt)*

---

## Step 4.5 Prompt — Fix: Awards + Streaming Platform Support

Read CLAUDE.md for full project context. Then read ALL of the following files to understand the current codebase:

- `database/schema.sql` — see the `award` and `stream_platform`/`film_exploitation` tables
- `database/seed_taxonomy.sql` — see the seeded streaming platforms
- `backend/app/services/tmdb_service.py` — current TMDB client
- `backend/app/services/tmdb_mapper.py` — current mapper output structure
- `backend/app/services/claude_enricher.py` — current enrichment prompt and output format
- `backend/app/services/taxonomy_config.py` — current taxonomy dimensions and reference examples
- `scripts/db_inserter.py` — current insertion logic (see what's missing)
- `scripts/data/reference_films_fallback.json` — current reference data structure
- `scripts/verify_db.py` — current verification queries

### Problem

The database schema has tables for **awards** (`award`) and **streaming availability** (`stream_platform` + `film_exploitation`), but NO code in the pipeline actually populates them:

1. **Awards** — not fetched from TMDB, not part of Claude enrichment, not in the data structures, not inserted, not verified.
2. **Streaming** — seed data exists for 11 platforms, but not fetched from TMDB, not in data structures, not inserted, not verified.

### Fix Plan

#### A. Awards — Add to Claude Enrichment

TMDB doesn't have good awards data, but Claude knows major awards for well-known films. Add awards to the Claude enrichment pipeline.

**A1. Update `backend/app/services/claude_enricher.py`:**

In the user prompt template (the `_build_user_prompt` method), add a new section after the Source/Origin section:

```
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
Only include awards you are confident about. If unsure, include fewer rather than risk errors.
```

In the expected JSON output format, add:

```json
{
  ...existing fields...,
  "awards": [
    {"festival_name": "Academy Awards", "category": "Best Visual Effects", "year": 1969, "result": "won"},
    {"festival_name": "Academy Awards", "category": "Best Director", "year": 1969, "result": "nominated"},
    {"festival_name": "Academy Awards", "category": "Best Picture", "year": 1969, "result": "nominated"}
  ],
  "confidence": {
    ...existing fields...,
    "awards": 0.8
  }
}
```

Also update the `_validate_enrichment` method to handle the `awards` field — validate that each entry has the required keys (festival_name, category, year, result) and that result is either "won" or "nominated". Remove malformed entries but don't reject the whole enrichment.

**A2. Update `backend/app/services/taxonomy_config.py`:**

Add the awards data to the 3 reference film examples:

**2001: A Space Odyssey (1968):**
```python
"awards": [
    {"festival_name": "Academy Awards", "category": "Best Visual Effects", "year": 1969, "result": "won"},
    {"festival_name": "Academy Awards", "category": "Best Director", "year": 1969, "result": "nominated"},
    {"festival_name": "Academy Awards", "category": "Best Picture", "year": 1969, "result": "nominated"},
    {"festival_name": "Academy Awards", "category": "Best Original Screenplay", "year": 1969, "result": "nominated"},
    {"festival_name": "Academy Awards", "category": "Best Art Direction", "year": 1969, "result": "nominated"},
]
```

**La Haine (1995):**
```python
"awards": [
    {"festival_name": "Cannes Film Festival", "category": "Best Director", "year": 1995, "result": "won"},
    {"festival_name": "César Awards", "category": "Best Film", "year": 1996, "result": "won"},
    {"festival_name": "César Awards", "category": "Best Editing", "year": 1996, "result": "won"},
    {"festival_name": "César Awards", "category": "Best Producer", "year": 1996, "result": "won"},
]
```

**Mulholland Drive (2001):**
```python
"awards": [
    {"festival_name": "Cannes Film Festival", "category": "Best Director", "year": 2001, "result": "won"},
    {"festival_name": "César Awards", "category": "Best Foreign Film", "year": 2002, "result": "nominated"},
]
```

Also add `"awards"` to the confidence dict in each reference example with value `0.95`.

#### B. Streaming — Add TMDB Watch Providers Fetch

TMDB has a `/movie/{id}/watch/providers` endpoint that returns per-country streaming availability. We'll add it as an optional, on-demand feature.

**B1. Update `backend/app/services/tmdb_service.py`:**

Add a new method:

```python
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
    data = await self._request(f"/movie/{tmdb_id}/watch/providers")
    
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
```

**B2. Update `backend/app/services/tmdb_mapper.py`:**

Add a new method to map provider names to our platform names:

```python
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
```

Add `streaming_platforms` to the output of `map_film_to_db()`: at the end before the return, add:

```python
# This field is populated separately via get_watch_providers()
# It's included in the structure for completeness but defaults to empty
"streaming_platforms": [],
```

#### C. Update db_inserter.py

**C1. Add awards insertion** in the `insert_film` method, after the source insertion (step 18). Add as step 19:

```python
# 19. Insert awards
await self._insert_awards(session, film_id, enrichment.get("awards", []))
```

**C2. Add the `_insert_awards` method:**

```python
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
```

**C3. Add streaming insertion** in the `insert_film` method as step 20:

```python
# 20. Insert streaming platforms
await self._insert_streaming(session, film_id, film_data.get("streaming_platforms", []))
```

**C4. Add the `_insert_streaming` method:**

```python
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
```

**C5. Update `_clear_junctions`:** Add `"film_exploitation"` and `"award"` to the `junction_tables` list (note: `award` is not technically a junction table but it is per-film data that should be cleared on re-insert).

#### D. Update reference_films_fallback.json

Add `"awards"` to the enrichment section of each of the 3 films, using the exact data from A2 above.

Add `"streaming_platforms": []` to the top level of each film (empty is fine — streaming availability changes and we won't hardcode it in fallback data).

#### E. Update verify_db.py

Add a new query **after query 14 (Cinema type & Cultural movement)** as query 15:

```python
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
}
```

Add a query 16 for streaming:

```python
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
}
```

Update the COMPLETENESS_QUERY to add:
```sql
(SELECT COUNT(*) FROM award aw WHERE aw.film_id = f.film_id) as awards_count,
```

Add `"awards_count"` to the headers list in the completeness check display.

Add to MIN_COUNTS:
```python
"awards_count": 1,  # at least 1 award/nomination for reference films
```

Renumber the completeness check to query 17 (it was 15 before).

**Important:** verify_db.py uses `run_query(engine, sql, tmdb_ids)` with `{ids}` placeholder — make sure the new queries follow this same pattern. Do NOT use `:tmdb_ids` parameter binding (that's what caused the original bug).

#### F. Update CLAUDE.md

Add a note in the Database Design section about:
- Awards: populated via Claude enrichment (major festivals and ceremonies)
- Streaming: populated via TMDB watch/providers endpoint (`/movie/{id}/watch/providers`), mapped to our platform names. Streaming data is volatile — consider refreshing periodically.

### Validation

After all changes:

1. Reset the database and re-seed:
```bash
# Drop and recreate (from project root):
psql -U postgres -d film_database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U postgres -d film_database -f database/schema.sql
psql -U postgres -d film_database -f database/seed_taxonomy.sql
```

BUT do NOT run these commands yourself — just ensure the code is correct. The user will run the reset manually.

2. Make sure `reference_films_fallback.json` has the new awards data so `seed_reference_films.py --offline` will populate the award table.

3. Make sure `verify_db.py` with the new queries 15-17 will pass after re-seeding.

---
