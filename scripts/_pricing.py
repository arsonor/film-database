"""
Shared Anthropic pricing constants and cost helpers.

Imported by scripts/claude_enrichment_runner.py and scripts/retag_films.py so
the price table lives in exactly one place.
"""

# Anthropic pricing, $/million tokens.  # Rates verified 2026-08-14
#
# NOTE on Sonnet 5: $2/$10 is an INTRODUCTORY rate that ends 2026-08-31;
# standard is $3/$15.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-5":   (2.00, 10.00),   # intro; $3/$15 from 2026-09-01
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5":  (1.00, 5.00),
    "claude-opus-5":     (5.00, 25.00),
    "claude-opus-4-8":   (5.00, 25.00),
}
_DEFAULT_PRICE = (3.00, 15.00)

# Cache multipliers relative to the model's input price.
CACHE_READ_MULT = 0.10   # cache hits bill at 0.1x input
CACHE_WRITE_MULT = 1.25  # 5-minute cache writes bill at 1.25x input
# 1-hour cache writes bill at 2x input (reads stay at 0.1x).
CACHE_WRITE_1H_MULT = 2.0

# Batch API: 50% discount on all of the above.
BATCH_DISCOUNT = 0.5


def prices_for(model: str) -> tuple[float, float]:
    """(input, output) $/MTok for a model id, with a prefix fallback."""
    if model in MODEL_PRICES:
        return MODEL_PRICES[model]
    for known, price in MODEL_PRICES.items():
        if model.startswith(known):
            return price
    return _DEFAULT_PRICE


def call_cost(model: str, usage) -> float:
    """Actual $ for one response, honouring cache reads/writes."""
    in_price, out_price = prices_for(model)
    plain = getattr(usage, "input_tokens", 0) or 0
    write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    out = getattr(usage, "output_tokens", 0) or 0
    return (
        plain * in_price
        + write * in_price * CACHE_WRITE_MULT
        + read * in_price * CACHE_READ_MULT
        + out * out_price
    ) / 1_000_000


def totals_cost(model: str, totals: dict[str, int]) -> float:
    """$ for a ClaudeEnricher.usage_totals dict (cumulative across calls)."""
    in_price, out_price = prices_for(model)
    return (
        totals.get("input", 0) * in_price
        + totals.get("cache_write", 0) * in_price * CACHE_WRITE_MULT
        + totals.get("cache_read", 0) * in_price * CACHE_READ_MULT
        + totals.get("output", 0) * out_price
    ) / 1_000_000
