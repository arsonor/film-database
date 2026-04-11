"""
Tier-based access configuration.
Mirrors the frontend tier config for server-side validation.
"""

TIER_ALLOWED_DIMENSIONS: dict[str, set[str]] = {
    "anonymous": {"categories", "time_periods", "place_contexts"},
    "free": {"categories", "time_periods", "place_contexts", "studios", "themes"},
    "pro": {
        "categories", "themes", "atmospheres", "characters", "motivations",
        "messages", "cinema_types", "time_periods", "place_contexts", "studios",
    },
    "admin": {
        "categories", "themes", "atmospheres", "characters", "motivations",
        "messages", "cinema_types", "time_periods", "place_contexts", "studios",
    },
}

# For themes: max sort_order allowed (None = all allowed)
TIER_THEME_MAX_SORT_ORDER: dict[str, int | None] = {
    "anonymous": None,   # themes not in allowed dims
    "free": 299,         # G1 + G2 only
    "pro": None,
    "admin": None,
}

TIER_MAX_FILTERS: dict[str, int | None] = {
    "anonymous": 2,
    "free": 5,
    "pro": None,
    "admin": None,
}

TIER_CAN_USE_OR_NOT: dict[str, bool] = {
    "anonymous": False,
    "free": False,
    "pro": True,
    "admin": True,
}
