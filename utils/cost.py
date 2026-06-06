"""Cost calculation for API usage."""

import json

from utils.constants import PRICING_FILE
from utils.env import env
from utils.tokens import TokenUsage


def load_pricing() -> dict | None:
    """Load model pricing from model_pricing.json."""
    if not PRICING_FILE.exists():
        return None
    with open(PRICING_FILE) as f:
        return json.load(f)


def calculate_cost(usage: TokenUsage, model: str | None = None) -> float | None:
    """Calculate cost in USD for given token counts.

    Splits prompt_tokens into cache-hit and cache-miss portions,
    each billed at their respective rates.
    """
    model = model or env.MIMO_MODEL
    pricing = load_pricing()
    if not pricing or model not in pricing["models"]:
        return None
    rates = pricing["models"][model]

    miss_cost = (usage.billable_input_tokens / 1_000_000) * rates["input_per_1m_cache_miss"]
    hit_cost = (usage.cached_tokens / 1_000_000) * rates["input_per_1m_cache_hit"]
    out_cost = (usage.completion_tokens / 1_000_000) * rates["output_per_1m"]

    return round(miss_cost + hit_cost + out_cost, 6)
