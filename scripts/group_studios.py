"""
Populate studio.studio_group with canonical parent-studio names.

TMDB hands back dozens of regional / sub-label variants for the same studio
family ("Warner Bros. Pictures", "Warner Bros. Animation", "Warner Bros.-
Seven Arts", "Warner Bros Pictures Italia"...). This script collapses them
into a single group name so the filter sidebar and stats dashboard can
aggregate them.

The mapping is a curated list of (regex, group_name) pairs evaluated in
order — first match wins. Studios that match no pattern are left with
studio_group = NULL and fall through to their raw studio_name in queries
that COALESCE(studio_group, studio_name).

Run on a live DB:

    python scripts/group_studios.py --dry-run     # preview only
    python scripts/group_studios.py               # apply
    python scripts/group_studios.py --reset       # NULL all studio_group
    python scripts/group_studios.py --top 30      # show top groups by film count

Requires: DATABASE_URL in .env. Run migration 021 first.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from collections import defaultdict

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# ---------------------------------------------------------------------------
# Mapping rules — order matters. More specific patterns MUST come before
# more generic ones (e.g. "Fox Searchlight" before plain "Fox").
#
# Patterns are matched case-insensitively against the full studio_name with
# re.search, so they don't need to anchor at the start of the string.
# ---------------------------------------------------------------------------

GROUP_RULES: list[tuple[str, str]] = [
    # --- US majors -----------------------------------------------------------
    (r"\bwarner\s*bros\b",                          "Warner Bros."),
    (r"\bwarner\s*(animation|independent|home\s*video|music|premiere|specialty|television)\b", "Warner Bros."),
    (r"\bnew\s*line\b",                             "New Line Cinema"),
    (r"\bhbo\b",                                    "HBO"),

    (r"\bwalt\s*disney\b",                          "Walt Disney"),
    (r"\bdisney\b",                                 "Walt Disney"),
    (r"\bpixar\b",                                  "Pixar"),
    (r"\bmarvel\s*(studios|entertainment|enterprises|films?|comics)\b", "Marvel Studios"),
    (r"\blucasfilm\b",                              "Lucasfilm"),
    (r"\btouchstone\b",                             "Touchstone Pictures"),
    (r"\bhollywood\s*pictures\b",                   "Hollywood Pictures"),
    (r"\bbuena\s*vista\b",                          "Buena Vista"),

    # DC family — kept separate from Warner. Bare "DC" matches too; suffixes
    # (Studios / Films / Entertainment / Comics / Vertigo) are optional.
    # "Vertigo" alone excluded because it matches unrelated production
    # credits (Hitchcock films etc.).
    (r"\bDC\b(\s*(studios|films?|entertainment|comics|vertigo))?", "DC Studios"),

    (r"\bfox\s*searchlight\b",                      "Searchlight Pictures"),
    (r"\bsearchlight\b",                            "Searchlight Pictures"),
    (r"\b20th\s*century\b",                         "20th Century"),
    (r"\btwentieth\s*century\b",                    "20th Century"),
    (r"\bfox\s*2000\b",                             "20th Century"),
    (r"^fox\b",                                     "20th Century"),
    (r"\b(?<!searchlight\s)fox\s+(film|pictures|television|family|atomic|international|animation|studios)\b", "20th Century"),

    (r"\buniversal\s*(pictures|studios|television|animation)?\b", "Universal Pictures"),
    (r"\bfocus\s*features\b",                       "Focus Features"),
    (r"\bworking\s*title\b",                        "Working Title Films"),
    (r"\bdreamworks\b",                             "DreamWorks"),
    (r"\bblumhouse\b",                              "Blumhouse"),
    (r"\billumination\b",                           "Illumination"),
    (r"\bamblin\b",                                 "Amblin Entertainment"),

    (r"\bparamount\b",                              "Paramount"),

    (r"\bcolumbia\s*pictures\b",                    "Columbia Pictures"),
    (r"\btristar\b",                                "TriStar Pictures"),
    # Sony Pictures Classics folded into Sony Pictures per request.
    (r"\bsony\s*pictures\b",                        "Sony Pictures"),
    (r"\bscreen\s*gems\b",                          "Sony Pictures"),

    (r"\b(metro-goldwyn-mayer|m\.?g\.?m\.?)\b",     "Metro-Goldwyn-Mayer"),
    (r"^mgm\b",                                     "Metro-Goldwyn-Mayer"),
    (r"\borion\s*(pictures|filmproduktion|productions)\b", "Orion Pictures"),
    (r"\borion[\s-]nova\b",                         "Orion Pictures"),
    (r"\bparamount[\s-]orion\b",                    "Orion Pictures"),
    (r"\bunited\s*artists\b",                       "United Artists"),
    (r"\brko\b",                                    "RKO"),

    (r"\blion[s]?\s*gate\b",                        "Lionsgate"),
    (r"\bsumm?it\s*entertainment\b",                "Lionsgate"),

    (r"\bmiramax\b",                                "Miramax"),
    (r"\bweinstein\b",                              "The Weinstein Company"),
    (r"\ba24\b",                                    "A24"),
    (r"\bneon\b",                                   "Neon"),
    (r"\bannapurna\b",                              "Annapurna Pictures"),
    (r"\bplan\s*b\s*entertainment\b",               "Plan B Entertainment"),

    # --- Streamers -----------------------------------------------------------
    (r"\bnetflix\b",                                "Netflix"),
    (r"\bamazon\s*(studios|mgm|prime)\b",           "Amazon"),
    (r"\bapple\s*(original|studios|tv)\b",          "Apple"),
    (r"^apple\b",                                   "Apple"),

    # --- France --------------------------------------------------------------
    (r"\bgaumont\b",                                "Gaumont"),
    (r"\bpath[ée]\b",                               "Pathé"),
    # StudioCanal absorbs the whole Canal+ / Ciné+ family (incl. regional
    # Polska, España, Brasil variants). The earlier TVP catch-all rule was
    # buggy (it ate Canal+ Polska) and has been removed.
    (r"\bstudio[\s-]?canal\b",                      "StudioCanal"),
    (r"\bcanal\s*\+",                               "StudioCanal"),
    (r"\bcin[ée]\s*\+",                             "StudioCanal"),
    (r"\bcanal\s+(brasil|diffusion)\b",             "StudioCanal"),
    (r"\bfrance\s*(2|3|t[ée]l[ée]visions?)\b",      "France Télévisions"),
    (r"\barte\b",                                   "Arte"),
    (r"\btf1\b",                                    "TF1"),
    (r"\bm6\b",                                     "M6 Films"),
    (r"\bmars\s*films?\b",                          "Mars Films"),
    (r"\bwild\s*bunch\b",                           "Wild Bunch"),
    (r"\bhaut\s*et\s*court\b",                      "Haut et Court"),
    (r"\bles\s*films\s*du\s*losange\b",             "Les Films du Losange"),
    (r"\bm[ée]tropole\s*films?\b",                  "Métropole Films"),
    (r"\bUGCF?\b",                                  "UGC"),

    # --- UK ------------------------------------------------------------------
    (r"\bbbc\s*(films|studios|productions|two)\b",  "BBC Films"),
    (r"\bfilm\s*4\b",                               "Film4"),
    (r"\bchannel\s*four\b",                         "Film4"),
    (r"\bbritish\s*film\s*institute|^bfi\b",        "BFI"),
    (r"\bhammer\s*film\b",                          "Hammer Film Productions"),
    (r"\bealing\s*studios\b",                       "Ealing Studios"),

    # --- Italy / Germany / Spain --------------------------------------------
    (r"\brai\s*(cinema|fiction|uno|2|3)?\b",        "RAI"),
    (r"\bmedusa\s*(film)?\b",                       "Medusa Film"),
    (r"\bmediaset\b",                               "Mediaset"),
    (r"\b01\s*distribution\b",                      "RAI"),
    (r"\bcinecitt[àa]\b",                           "Cinecittà"),
    (r"\bconstantin\s*film\b",                      "Constantin Film"),
    (r"\bbavaria\s*film\b",                         "Bavaria Film"),
    (r"\bUFA\b",                                    "UFA"),
    (r"\bel\s*deseo\b",                             "El Deseo"),

    # --- Japan ---------------------------------------------------------------
    (r"\bstudio\s*ghibli\b",                        "Studio Ghibli"),
    (r"\b(shin)?toho\b",                            "Toho"),
    (r"\btoei\b",                                   "Toei"),
    (r"\bshochiku\b",                               "Shochiku"),
    (r"\bnikkatsu\b",                               "Nikkatsu"),
    (r"\bkadokawa\b",                               "Kadokawa"),
    (r"\bmadhouse\b",                               "Madhouse"),
    (r"\bbones\b",                                  "Bones"),
    (r"\bproduction\s*i\.?g\.?\b",                  "Production I.G"),
    (r"\bsunrise\b",                                "Sunrise"),

    # --- Hong Kong / China / Korea ------------------------------------------
    (r"\bshaw\s*brothers\b",                        "Shaw Brothers"),
    # Orange Sky / Orange Sky Golden Harvest = HK distributor (post-2009
    # merger). Must precede the generic Orange Studio rule below.
    (r"\borange\s*sky\b",                           "Orange Sky Golden Harvest"),
    (r"\bgolden\s*harvest\b",                       "Golden Harvest"),
    (r"\bmedia\s*asia\b",                           "Media Asia"),
    (r"\bcj\s*(entertainment|enm|investment)\b",    "CJ Entertainment"),
    (r"\bshowbox\b",                                "Showbox"),

    # --- Other ---------------------------------------------------------------
    # Bare "Orange" → French Orange Studio. Placed last so "Orange Sky"
    # above wins for the HK distributor.
    (r"\borange\b",                                 "Orange Studio"),
    (r"\bmosfilm\b",                                "Mosfilm"),
]


COMPILED_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), group) for pattern, group in GROUP_RULES
]


def classify(studio_name: str) -> str | None:
    for pattern, group in COMPILED_RULES:
        if pattern.search(studio_name):
            return group
    return None


async def show_top(session, limit: int) -> None:
    """Print the top N studio groups by distinct film count, after applying
    the mapping in-memory (does NOT mutate the DB)."""
    result = await session.execute(text(
        """
        SELECT s.studio_id, s.studio_name, COUNT(DISTINCT p.film_id) AS films
        FROM studio s
        LEFT JOIN production p ON p.studio_id = s.studio_id
        GROUP BY s.studio_id, s.studio_name
        ORDER BY films DESC
        """
    ))
    rows = result.fetchall()

    grouped: dict[str, int] = defaultdict(int)
    grouped_members: dict[str, list[tuple[str, int]]] = defaultdict(list)
    ungrouped: list[tuple[str, int]] = []

    # Build film_id sets per group to avoid double-counting films that belong
    # to multiple sub-labels of the same group.
    group_film_ids: dict[str, set[int]] = defaultdict(set)

    # We need film_ids for accurate distinct count per group.
    fid_result = await session.execute(text(
        """
        SELECT s.studio_id, s.studio_name, p.film_id
        FROM studio s
        JOIN production p ON p.studio_id = s.studio_id
        """
    ))
    for sid, name, fid in fid_result.fetchall():
        g = classify(name)
        if g:
            group_film_ids[g].add(fid)

    for sid, name, films in rows:
        g = classify(name)
        if g:
            grouped_members[g].append((name, int(films or 0)))
        else:
            ungrouped.append((name, int(films or 0)))

    final_groups = sorted(
        ((g, len(group_film_ids[g])) for g in grouped_members),
        key=lambda x: x[1],
        reverse=True,
    )[:limit]

    print(f"\nTop {limit} studio groups by distinct film count:\n")
    print(f"  {'Group':<30s} {'Films':>6s}   Sub-labels")
    print(f"  {'-' * 30} {'-' * 6}   {'-' * 40}")
    for g, n in final_groups:
        members = sorted(grouped_members[g], key=lambda x: -x[1])
        sample = ", ".join(f"{name} ({c})" for name, c in members[:4])
        if len(members) > 4:
            sample += f", … (+{len(members) - 4} more)"
        print(f"  {g:<30s} {n:>6d}   {sample}")

    print(f"\nUngrouped studios: {len(ungrouped)} rows "
          f"(top 10 by film count: "
          f"{', '.join(f'{n}({c})' for n, c in sorted(ungrouped, key=lambda x: -x[1])[:10])})")


async def apply_mapping(session, dry_run: bool) -> None:
    result = await session.execute(text(
        "SELECT studio_id, studio_name, studio_group FROM studio"
    ))
    rows = result.fetchall()

    to_update: list[tuple[int, str | None, str | None]] = []
    set_count: dict[str, int] = defaultdict(int)
    cleared = 0

    for sid, name, current_group in rows:
        new_group = classify(name)
        if new_group != current_group:
            to_update.append((sid, current_group, new_group))
            if new_group is None:
                cleared += 1
            else:
                set_count[new_group] += 1

    print(f"Studios scanned: {len(rows)}")
    print(f"Changes: {len(to_update)}  (set/changed: {len(to_update) - cleared}, cleared: {cleared})")
    if set_count:
        print("\nGroup assignments:")
        for g in sorted(set_count, key=lambda k: -set_count[k]):
            print(f"  {g:<30s} {set_count[g]:>5d} new/changed studios")

    if dry_run:
        print("\nDry run — no DB writes.")
        return

    for sid, _old, new_group in to_update:
        await session.execute(
            text("UPDATE studio SET studio_group = :g WHERE studio_id = :sid"),
            {"g": new_group, "sid": sid},
        )
    await session.commit()
    print(f"\nApplied {len(to_update)} updates.")


async def reset_all(session) -> None:
    result = await session.execute(text("UPDATE studio SET studio_group = NULL"))
    await session.commit()
    print(f"Cleared studio_group on {result.rowcount} rows.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Populate studio.studio_group from curated rules.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    parser.add_argument("--reset", action="store_true", help="NULL out studio_group for every row, then exit.")
    parser.add_argument("--top", type=int, default=None, help="Print top N groups by distinct film count and exit.")
    args = parser.parse_args()

    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL not set in environment / .env")

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        if args.reset:
            await reset_all(session)
            return
        if args.top is not None:
            await show_top(session, args.top)
            return
        await apply_mapping(session, dry_run=args.dry_run)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
