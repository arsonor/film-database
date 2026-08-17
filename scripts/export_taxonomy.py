"""
Export current taxonomy state from the database into source files.

Regenerates:
  - database/seed_taxonomy.sql
  - backend/app/services/taxonomy_config.py

Usage:
    python scripts/export_taxonomy.py           # overwrite files
    python scripts/export_taxonomy.py --dry-run  # print to stdout
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = PROJECT_ROOT / "database" / "seed_taxonomy.sql"
CONFIG_PATH = PROJECT_ROOT / "backend" / "app" / "services" / "taxonomy_config.py"

# All sorted dimensions fetch (name, sort_order) — Taxonomy v2: 7 dimensions
SORTED_TABLES = {
    "categories": ("category", "category_name, historic_subcategory_name, sort_order", "sort_order, category_name"),
    "cinema_types": ("cinema_type", "technique_name, sort_order", "sort_order, technique_name"),
    "themes": ("theme_context", "theme_name, sort_order", "sort_order, theme_name"),
    "characters": ("character_context", "context_name, sort_order", "sort_order, context_name"),
    "atmospheres": ("atmosphere", "atmosphere_name, sort_order", "sort_order, atmosphere_name"),
    "time_contexts": ("time_context", "time_period, sort_order", "sort_order, time_period"),
    "place_contexts": ("place_context", "environment, sort_order", "sort_order, environment"),
}

# Sub-dimension labels, keyed by sort_order block (sort_order // 100).
# Emitted as comments in both seed_taxonomy.sql and taxonomy_config.py so the
# generated files stay as readable as the hand-written ones. Mirrors
# frontend/src/lib/taxonomyGroups.ts.
GROUP_LABELS: dict[str, dict[int, str]] = {
    "categories": {
        1: "Main", 2: "Sub-genres: Drama / Romance", 3: "Sub-genres: Comedy",
        4: "Sub-genres: Thriller / Adventure", 5: "Sub-genres: Historical / Justice",
        6: "Sub-genres: Sci-fi / Fantasy", 7: "Sub-genres: Horror",
        8: "Sub-genres: Miscellaneous",
    },
    "themes": {
        1: "Society & World", 2: "Values & Reflection",
        3: "Human Relations > Bonds & attachments",
        4: "Human Relations > Desire & transgression",
        5: "Human Relations > Interpersonal conflict",
        6: "Human Relations > Crime & abuse of power",
        7: "Personal / Inner conflict > Wounds & burdens",
        8: "Personal / Inner conflict > Drives & arcs",
        9: "Art, Sport & Entertainment > Art",
        10: "Art, Sport & Entertainment > Sport",
        11: "Art, Sport & Entertainment > Entertainment",
        12: "Face to the unknown",
    },
    "time_contexts": {0: "Years & eras", 1: "Time span", 2: "Seasons"},
    "place_contexts": {
        1: "Environments", 2: "Buildings & institutions", 3: "Narrative settings",
        4: "Vehicles", 5: "None",
    },
    "atmospheres": {
        1: "Light / Joyful", 2: "Dark / Extreme", 3: "Pace, Tension & Scale",
        4: "Artistic Directing",
    },
    "characters": {
        1: "Group structure", 2: "Age & identity", 3: "Social status",
        4: "Traits & conditions", 5: "Narrative devices",
        6: "Archetypes - human > Figures & roles",
        7: "Archetypes - human > Law & crime",
        8: "Archetypes - human > Fighters",
        9: "Non-human & creatures",
    },
    "cinema_types": {
        1: "Visual techniques", 2: "Industry & culture",
        3: "Narrative techniques > Sequencing", 4: "Narrative techniques > Voice & Dialogue",
        5: "Movements & eras",
    },
}


async def fetch_all(engine):
    """Fetch all taxonomy data from the database."""
    data = {}
    async with engine.connect() as conn:
        # Categories (special: has subcategories)
        r = await conn.execute(text(
            "SELECT category_name, historic_subcategory_name, sort_order FROM category "
            "ORDER BY sort_order, category_name, historic_subcategory_name NULLS FIRST"
        ))
        data["categories"] = [(row[0], row[1], row[2]) for row in r.fetchall()]

        # All sorted single-column tables
        for key, (table, cols, order) in SORTED_TABLES.items():
            if key == "categories":
                continue
            r = await conn.execute(text(f"SELECT {cols} FROM {table} ORDER BY {order}"))
            data[key] = [(row[0], row[1]) for row in r.fetchall()]

        # Person jobs
        r = await conn.execute(text("SELECT role_name FROM person_job ORDER BY role_name"))
        data["person_jobs"] = [row[0] for row in r.fetchall()]

        # Streaming platforms
        r = await conn.execute(text("SELECT platform_name FROM stream_platform ORDER BY platform_name"))
        data["streaming_platforms"] = [row[0] for row in r.fetchall()]

        # Languages
        r = await conn.execute(text("SELECT language_code, language_name FROM language ORDER BY language_code"))
        data["languages"] = [(row[0], row[1]) for row in r.fetchall()]

    return data


def _sql_values(values: list[str], indent: str = "    ") -> str:
    """Format a list of strings as SQL VALUES."""
    lines = []
    for i, v in enumerate(values):
        escaped = v.replace("'", "''")
        comma = "," if i < len(values) - 1 else ""
        lines.append(f"{indent}('{escaped}'){comma}")
    return "\n".join(lines)


def _sql_sorted_values(
    items: list[tuple[str, int]], dim: str | None = None, indent: str = "    "
) -> str:
    """Format (name, sort_order) tuples as SQL VALUES, with group comments."""
    labels = GROUP_LABELS.get(dim or "", {})
    lines = []
    prev_block = None
    for i, (name, sort_order) in enumerate(items):
        block = (sort_order or 0) // 100
        if block != prev_block:
            label = labels.get(block)
            if label:
                lines.append(f"{indent}-- {label} ({block}00s)")
            prev_block = block
        escaped = name.replace("'", "''")
        comma = "," if i < len(items) - 1 else ""
        lines.append(f"{indent}('{escaped}', {sort_order}){comma}")
    return "\n".join(lines)


def generate_seed_sql(data: dict) -> str:
    """Generate the full seed_taxonomy.sql content."""
    sections = []

    sections.append("-- Film Database Seed Data")
    sections.append("-- Pre-populate all taxonomy/lookup tables with reference values")
    sections.append("-- Uses ON CONFLICT DO NOTHING for idempotent execution")
    sections.append("-- Auto-generated by scripts/export_taxonomy.py")

    # Person jobs
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append("-- PERSON_JOB - Crew roles")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_values(data["person_jobs"])
    sections.append(f"INSERT INTO person_job (role_name) VALUES\n{vals}\nON CONFLICT (role_name) DO NOTHING;")

    # Categories (Genre) — all rows flat, main genres are sort_order < 200
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- CATEGORY (Genre) - {len(data['categories'])} tags")
    sections.append("-- Main genres occupy the 100s block; everything from 200 up is a sub-genre.")
    sections.append('-- "Is a main genre" == sort_order < 200. All rows are flat')
    sections.append("-- (historic_subcategory_name IS NULL); the composite mechanism is inert.")
    sections.append("-- =============================================================================")
    sections.append("")
    cat_labels = GROUP_LABELS["categories"]
    cat_lines = []
    prev_block = None
    for i, (cat_name, sub_name, sort_order) in enumerate(data["categories"]):
        block = (sort_order or 0) // 100
        if block != prev_block:
            label = cat_labels.get(block)
            if label:
                cat_lines.append(f"    -- {label} ({block}00s)")
            prev_block = block
        comma = "," if i < len(data["categories"]) - 1 else ""
        cn = cat_name.replace("'", "''")
        if sub_name:
            sn = sub_name.replace("'", "''")
            cat_lines.append(f"    ('{cn}', '{sn}', {sort_order}){comma}")
        else:
            cat_lines.append(f"    ('{cn}', NULL, {sort_order}){comma}")
    # Partial unique index (migration 026) — the conflict target for flat rows.
    sections.append("INSERT INTO category (category_name, historic_subcategory_name, sort_order) VALUES\n" +
                    "\n".join(cat_lines) +
                    "\nON CONFLICT (category_name) WHERE historic_subcategory_name IS NULL DO NOTHING;")

    # Cinema types
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- CINEMA_TYPE (Cinema Type) - {len(data['cinema_types'])} tags")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["cinema_types"], "cinema_types")
    sections.append(f"INSERT INTO cinema_type (technique_name, sort_order) VALUES\n{vals}\nON CONFLICT (technique_name) DO NOTHING;")

    # Place contexts
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- PLACE_CONTEXT (Place) - {len(data['place_contexts'])} tags")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["place_contexts"], "place_contexts")
    sections.append(f"INSERT INTO place_context (environment, sort_order) VALUES\n{vals}\nON CONFLICT (environment) DO NOTHING;")

    # Time contexts
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- TIME_CONTEXT (Time Period) - {len(data['time_contexts'])} tags")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["time_contexts"], "time_contexts")
    sections.append(f"INSERT INTO time_context (time_period, sort_order) VALUES\n{vals}\nON CONFLICT (time_period) DO NOTHING;")

    # Themes
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- THEME_CONTEXT (Theme) - {len(data['themes'])} tags")
    sections.append('-- Hierarchical themes use the "parent: sub" convention (e.g. "art: cinema")')
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["themes"], "themes")
    sections.append(f"INSERT INTO theme_context (theme_name, sort_order) VALUES\n{vals}\nON CONFLICT (theme_name) DO NOTHING;")

    # Characters
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- CHARACTER_CONTEXT (Character) - {len(data['characters'])} tags")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["characters"], "characters")
    sections.append(f"INSERT INTO character_context (context_name, sort_order) VALUES\n{vals}\nON CONFLICT (context_name) DO NOTHING;")

    # Atmospheres
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append(f"-- ATMOSPHERE (Atmosphere) - {len(data['atmospheres'])} tags")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_sorted_values(data["atmospheres"], "atmospheres")
    sections.append(f"INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES\n{vals}\nON CONFLICT (atmosphere_name) DO NOTHING;")

    # Streaming platforms
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append("-- STREAM_PLATFORM - Streaming platforms")
    sections.append("-- =============================================================================")
    sections.append("")
    vals = _sql_values(data["streaming_platforms"])
    sections.append(f"INSERT INTO stream_platform (platform_name) VALUES\n{vals}\nON CONFLICT (platform_name) DO NOTHING;")

    # Languages
    sections.append("")
    sections.append("-- =============================================================================")
    sections.append("-- LANGUAGE - Languages")
    sections.append("-- =============================================================================")
    sections.append("")
    lang_lines = []
    for i, (code, name) in enumerate(data["languages"]):
        comma = "," if i < len(data["languages"]) - 1 else ""
        c = code.replace("'", "''")
        n = name.replace("'", "''")
        lang_lines.append(f"    ('{c}', '{n}'){comma}")
    sections.append(f"INSERT INTO language (language_code, language_name) VALUES\n" +
                    "\n".join(lang_lines) +
                    "\nON CONFLICT (language_code) DO NOTHING;")

    sections.append("")
    sections.append("-- =============================================================================")
    sections.append("-- END OF SEED DATA")
    sections.append("-- =============================================================================")
    sections.append("")

    return "\n".join(sections)


def _preserved_block(start_marker: str, end_marker: str = "]") -> str:
    """Copy a hand-written block verbatim from the existing taxonomy_config.py.

    Used for constants the database cannot produce (e.g. the Time Period year
    ranges). Returns an empty string if the file or the block is missing.
    """
    try:
        existing = CONFIG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

    idx = existing.find(start_marker)
    if idx < 0:
        print(f"WARNING: '{start_marker.strip()}' not found — block dropped from output",
              file=sys.stderr)
        return ""

    # Include the comment lines immediately above the marker.
    lines_before = existing[:idx].rstrip("\n").split("\n")
    preamble: list[str] = []
    for line in reversed(lines_before):
        if line.startswith("#"):
            preamble.insert(0, line)
        else:
            break

    rest = existing[idx:].split("\n")
    block = []
    for line in rest:
        block.append(line)
        if line == end_marker:
            break
    return "\n".join(preamble + block)


def _py_list(
    name: str,
    values: list[str] | list[tuple[str, int]],
    dim: str | None = None,
    indent: str = "    ",
) -> str:
    """Format a Python list constant, with a comment per sub-dimension group.

    `values` is either a plain list of names or (name, sort_order) tuples; the
    latter enables the group comments.
    """
    labels = GROUP_LABELS.get(dim or "", {})
    lines = [f"{name} = ["]
    prev_block = None
    for v in values:
        if isinstance(v, tuple):
            name_str, sort_order = v
            block = (sort_order or 0) // 100
            if block != prev_block:
                label = labels.get(block)
                if label:
                    lines.append(f"{indent}# {label} ({block}00s)")
                prev_block = block
        else:
            name_str = v
        escaped = name_str.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'{indent}"{escaped}",')
    lines.append("]")
    return "\n".join(lines)


def generate_taxonomy_config(data: dict) -> str:
    """Generate taxonomy_config.py content, preserving REFERENCE_EXAMPLES."""
    lines = []
    lines.append('"""')
    lines.append("Taxonomy configuration for the Film Database project.")
    lines.append("")
    lines.append("All valid taxonomy values extracted from database (Taxonomy v2: 7 dimensions —")
    lines.append("Genre, Theme, Time Period, Place, Atmosphere, Character, Cinema Type).")
    lines.append("Auto-generated by scripts/export_taxonomy.py — do not edit manually,")
    lines.append("except TIME_PERIOD_YEAR_RANGES and REFERENCE_EXAMPLES (both preserved on export).")
    lines.append("Used by ClaudeEnricher to build prompts and validate outputs.")
    lines.append('"""')
    lines.append("")

    # Genre — all rows are flat; main genres are sort_order < 200.
    lines.append("# Main genres occupy sort_order block 100-199; everything from 200 up is a")
    lines.append("# sub-genre. Every film must get at least one MAIN genre.")
    main_cats = [(cat, so) for cat, sub, so in data["categories"] if sub is None and (so or 0) < 200]
    sub_cats = [(cat, so) for cat, sub, so in data["categories"] if sub is None and (so or 0) >= 200]
    lines.append(_py_list("VALID_GENRES_MAIN", main_cats))
    lines.append("")
    lines.append(_py_list("VALID_GENRES_SUB", sub_cats, "categories"))
    lines.append("")
    lines.append("VALID_CATEGORIES = VALID_GENRES_MAIN + VALID_GENRES_SUB")
    lines.append("")

    # Legacy composite rows (historic_subcategory_name IS NOT NULL) should no
    # longer exist after migration 026 — warn instead of emitting a dead constant.
    hist_subs = [sub for _cat, sub, _so in data["categories"] if sub is not None]
    if hist_subs:
        print(f"WARNING: {len(hist_subs)} composite category row(s) still in the DB: {hist_subs}",
              file=sys.stderr)

    lines.append(_py_list("VALID_CINEMA_TYPES", data["cinema_types"], "cinema_types"))
    lines.append("")
    lines.append(_py_list("VALID_PLACE_ENVIRONMENTS", data["place_contexts"], "place_contexts"))
    lines.append("")
    lines.append(_py_list("VALID_TIME_CONTEXTS", data["time_contexts"], "time_contexts"))
    lines.append("")
    lines.append(_preserved_block("TIME_PERIOD_YEAR_RANGES = ["))
    lines.append("")
    lines.append(_py_list("VALID_THEMES", data["themes"], "themes"))
    lines.append("")
    lines.append(_py_list("VALID_CHARACTERS", data["characters"], "characters"))
    lines.append("")
    lines.append(_py_list("VALID_ATMOSPHERES", data["atmospheres"], "atmospheres"))
    lines.append("")
    lines.append(_py_list("VALID_SOURCE_TYPES", [
        "original screenplay", "novel", "comic", "TV series", "true story",
        "play", "video game", "poem", "short story", "remake",
    ]))
    lines.append("")

    # TAXONOMY_DIMENSIONS dict — the 7 live dimensions
    lines.append("TAXONOMY_DIMENSIONS = {")
    lines.append('    "categories": VALID_CATEGORIES,')
    lines.append('    "cinema_type": VALID_CINEMA_TYPES,')
    lines.append('    "time_context": VALID_TIME_CONTEXTS,')
    lines.append('    "place_environment": VALID_PLACE_ENVIRONMENTS,')
    lines.append('    "themes": VALID_THEMES,')
    lines.append('    "character_context": VALID_CHARACTERS,')
    lines.append('    "atmosphere": VALID_ATMOSPHERES,')
    lines.append("}")
    lines.append("")

    # Preserve REFERENCE_EXAMPLES from existing file
    try:
        existing = CONFIG_PATH.read_text(encoding="utf-8")
        marker = "REFERENCE_EXAMPLES = {"
        idx = existing.find(marker)
        if idx >= 0:
            # Find the comment block before REFERENCE_EXAMPLES
            block_start = existing.rfind("# ===", 0, idx)
            if block_start >= 0:
                lines.append(existing[block_start:].rstrip())
            else:
                lines.append(existing[idx:].rstrip())
        lines.append("")
    except FileNotFoundError:
        lines.append("REFERENCE_EXAMPLES = {}")
        lines.append("")

    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="Export taxonomy from DB to source files")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing files")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set in .env", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    try:
        data = await fetch_all(engine)
    finally:
        await engine.dispose()

    seed_sql = generate_seed_sql(data)
    config_py = generate_taxonomy_config(data)

    if args.dry_run:
        print("=" * 60)
        print("seed_taxonomy.sql")
        print("=" * 60)
        print(seed_sql)
        print()
        print("=" * 60)
        print("taxonomy_config.py")
        print("=" * 60)
        print(config_py)
    else:
        SEED_PATH.write_text(seed_sql, encoding="utf-8")
        print(f"Written: {SEED_PATH}")
        CONFIG_PATH.write_text(config_py, encoding="utf-8")
        print(f"Written: {CONFIG_PATH}")
        print()
        print("Remember to restart the backend if it's running (taxonomy_config.py is loaded at import time).")


if __name__ == "__main__":
    asyncio.run(main())
