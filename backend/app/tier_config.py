"""
Tier-based access configuration.
Mirrors the frontend tier config for server-side validation.
"""

TIER_ALLOWED_DIMENSIONS: dict[str, set[str]] = {
    "anonymous": {"categories", "time_periods", "atmospheres"},
    "free": {
        "categories", "time_periods", "place_contexts",
        "themes", "atmospheres", "characters",
        "motivations", "cinema_types",
    },
    "pro": {
        "categories", "themes", "atmospheres", "characters", "motivations",
        "messages", "cinema_types", "time_periods", "place_contexts", "studios",
    },
    "admin": {
        "categories", "themes", "atmospheres", "characters", "motivations",
        "messages", "cinema_types", "time_periods", "place_contexts", "studios",
    },
}

# Per-dimension max sort_order allowed (missing = all allowed)
TIER_DIMENSION_MAX_SORT_ORDER: dict[str, dict[str, int]] = {
    "anonymous": {"atmospheres": 299},
    "free": {
        "themes": 399,
        "atmospheres": 299,
        "place_contexts": 299,
        "characters": 299,
        "motivations": 199,
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
