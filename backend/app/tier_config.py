"""
Tier-based access configuration.
Mirrors the frontend tier config for server-side validation.

Taxonomy v2 (7 dimensions): categories, themes, time_periods, place_contexts,
atmospheres, characters, cinema_types (+ studios for pro/admin).
"""

TIER_ALLOWED_DIMENSIONS: dict[str, set[str]] = {
    "anonymous": {"categories", "time_periods", "atmospheres"},
    "free": {
        "categories", "themes", "time_periods", "place_contexts",
        "atmospheres", "characters", "cinema_types",
    },
    "pro": {
        "categories", "themes", "time_periods", "place_contexts",
        "atmospheres", "characters", "cinema_types", "studios",
    },
    "admin": {
        "categories", "themes", "time_periods", "place_contexts",
        "atmospheres", "characters", "cinema_types", "studios",
    },
}

# Per-dimension max sort_order allowed (missing = all allowed).
# sort_order blocks of 100 = one named sub-dimension, so these caps expose
# whole groups at a time (e.g. categories 199 = main genres only).
TIER_DIMENSION_MAX_SORT_ORDER: dict[str, dict[str, int]] = {
    "anonymous": {
        "categories": 199,      # main genres only
        "time_periods": 99,     # chronological only
        "atmospheres": 299,
    },
    "free": {
        "themes": 699,
        "atmospheres": 299,
        "place_contexts": 299,
        "characters": 399,
        "cinema_types": 199,
    },
    "pro": {},
    "admin": {},
}

TIER_MAX_FILTERS: dict[str, int | None] = {
    "anonymous": 2,
    "free": 3,
    "pro": None,
    "admin": None,
}

TIER_CAN_USE_OR_NOT: dict[str, bool] = {
    "anonymous": False,
    "free": False,
    "pro": True,
    "admin": True,
}

TIER_MAX_LISTS: dict[str, int | None] = {
    "anonymous": 0,
    "free": 3,
    "pro": None,
    "admin": None,
}
