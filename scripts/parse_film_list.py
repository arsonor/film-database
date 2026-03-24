"""
Parse Films_list.docx into structured JSON data for batch TMDB resolution.

Input:  scripts/data/Films_list.docx
Output: scripts/data/parsed_films.json

The document is organized by year with bold year headers, and within each year
films are grouped by region (Francophone, Anglo-saxon, Asiat, Autres, Franchise,
Animation, Docu). Older years (pre-1973) may not have explicit region headers.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("Error: python-docx is required. Install with: pip install python-docx")
    sys.exit(1)


# Known region headers (case-insensitive matching)
REGION_HEADERS = {
    "francophone": "Francophone",
    "anglo-saxon": "Anglo-saxon",
    "anglo-saxons": "Anglo-saxon",
    "asiat": "Asiat",
    "asiatique": "Asiat",
    "autres": "Autres",
    "franchise": "Franchise",
    "animation": "Animation",
    "docu": "Docu",
    "documentaire": "Docu",
}


def is_year_header(text: str) -> int | None:
    """
    Check if text is a year header like '1968:' or '1968 :'.
    Returns the year as int, or None.
    """
    match = re.match(r"^\s*(\d{4})\s*:?\s*$", text.strip())
    if match:
        year = int(match.group(1))
        if 1880 <= year <= 2030:
            return year
    return None


def is_region_header(text: str) -> str | None:
    """
    Check if text is a region header like 'Francophone:' or 'Anglo-saxon :'.
    Returns the normalized region name, or None.
    """
    cleaned = text.strip().rstrip(":").strip().lower()
    return REGION_HEADERS.get(cleaned)


def extract_notes(title: str) -> tuple[str, str | None, str]:
    """
    Extract parenthetical notes from a title.

    Returns (clean_title, original_title_hint, notes).
    Examples:
        'Le mépris (Godard)' → ('Le mépris', None, 'Godard')
        'Rashomon (Kurosawa)' → ('Rashomon', None, 'Kurosawa')
        'Les temps modernes (Modern Times)' → ('Les temps modernes', 'Modern Times', 'Modern Times')
    """
    match = re.match(r"^(.+?)\s*\((.+?)\)\s*$", title.strip())
    if not match:
        return title.strip(), None, ""

    clean_title = match.group(1).strip()
    note_content = match.group(2).strip()

    # Heuristic: if the note looks like an English/alternative title
    # (starts with capital, contains spaces, no digits) it's a title hint
    original_title_hint = None
    words = note_content.split()
    is_likely_title = (
        len(words) >= 2
        and not re.match(r"^\d{4}$", note_content)
        and note_content[0].isupper()
        and not any(
            note_content.lower().startswith(prefix)
            for prefix in ["réal", "dir", "avec", "aka", "cf"]
        )
    )
    if is_likely_title:
        original_title_hint = note_content

    return clean_title, original_title_hint, note_content


def split_film_titles(text: str) -> list[str]:
    """
    Split a line of comma-separated film titles.
    Handles titles that may contain commas inside parentheses.
    """
    titles: list[str] = []
    current = ""
    paren_depth = 0

    for char in text:
        if char == "(":
            paren_depth += 1
            current += char
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
            current += char
        elif char == "," and paren_depth == 0:
            stripped = current.strip()
            if stripped:
                titles.append(stripped)
            current = ""
        else:
            current += char

    stripped = current.strip()
    if stripped:
        titles.append(stripped)

    return titles


def parse_paragraph_text(paragraph) -> tuple[str, bool]:
    """
    Extract text from a paragraph and detect if it's bold (header).
    A paragraph is considered bold if all non-empty runs are bold.
    """
    text = paragraph.text.strip()
    if not text:
        return "", False

    # Check if all non-whitespace runs are bold
    runs = paragraph.runs
    if not runs:
        return text, False

    non_empty_runs = [r for r in runs if r.text.strip()]
    if not non_empty_runs:
        return text, False

    all_bold = all(r.bold for r in non_empty_runs)
    return text, all_bold


def parse_docx(filepath: str | Path) -> list[dict]:
    """
    Parse Films_list.docx into a list of structured film entries.

    Returns list of dicts with: year, title, original_title_hint, region, notes, raw_line
    """
    doc = Document(str(filepath))
    films: list[dict] = []
    unparsed: list[str] = []

    current_year: int | None = None
    current_region: str = "general"

    for paragraph in doc.paragraphs:
        text, is_bold = parse_paragraph_text(paragraph)

        if not text:
            continue

        # Check for year header (bold text like "1968:" or standalone year)
        year = is_year_header(text)
        if year is not None:
            current_year = year
            current_region = "general"  # reset region for new year
            continue

        # Check for region header (bold text like "Francophone:")
        if is_bold:
            region = is_region_header(text)
            if region:
                current_region = region
                continue
            # Could be a year header embedded with region info
            # e.g., "1968: Anglo-saxon:" — try to parse
            year_match = re.match(r"^(\d{4})\s*:\s*(.+)$", text)
            if year_match:
                yr = int(year_match.group(1))
                if 1880 <= yr <= 2030:
                    current_year = yr
                    rest = year_match.group(2).strip().rstrip(":").strip()
                    region = is_region_header(rest + ":")
                    current_region = region if region else "general"
                    continue

        # Also check for inline region headers (non-bold but matches pattern)
        region = is_region_header(text)
        if region:
            current_region = region
            continue

        # If no current year, skip
        if current_year is None:
            unparsed.append(text)
            continue

        # Split and process film titles
        titles = split_film_titles(text)
        for raw_title in titles:
            # Skip empty or very short entries
            if len(raw_title) < 2:
                continue

            clean_title, original_title_hint, notes = extract_notes(raw_title)

            # Skip if it looks like a section header we missed
            if is_year_header(clean_title) is not None:
                continue

            films.append({
                "year": current_year,
                "title": clean_title,
                "original_title_hint": original_title_hint,
                "region": current_region,
                "notes": notes,
                "raw_line": raw_title,
            })

    return films, unparsed


def print_statistics(films: list[dict], unparsed: list[str]):
    """Print summary statistics after parsing."""
    print("\n" + "=" * 60)
    print("PARSING SUMMARY")
    print("=" * 60)

    print(f"\nTotal films parsed: {len(films)}")

    # Per decade
    decades = defaultdict(int)
    for f in films:
        decade = (f["year"] // 10) * 10
        decades[decade] += 1

    print("\nFilms per decade:")
    for decade in sorted(decades):
        print(f"  {decade}s: {decades[decade]}")

    # Per region
    regions = defaultdict(int)
    for f in films:
        regions[f["region"]] += 1

    print("\nFilms per region:")
    for region in sorted(regions, key=lambda r: regions[r], reverse=True):
        print(f"  {region}: {regions[region]}")

    # Unparsed lines
    if unparsed:
        print(f"\nUnparsed lines ({len(unparsed)}):")
        for line in unparsed[:20]:
            print(f"  - {line}")
        if len(unparsed) > 20:
            print(f"  ... and {len(unparsed) - 20} more")

    print("=" * 60)


def main():
    """Main entry point: parse the docx and output JSON."""
    script_dir = Path(__file__).parent
    input_path = script_dir / "data" / "Films_list.docx"
    output_path = script_dir / "data" / "parsed_films.json"

    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        print("Place Films_list.docx in scripts/data/ and re-run.")
        sys.exit(1)

    print(f"Parsing {input_path}...")
    films, unparsed = parse_docx(input_path)

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(films)} films to {output_path}")
    print_statistics(films, unparsed)


if __name__ == "__main__":
    main()
