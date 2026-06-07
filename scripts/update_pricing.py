#!/usr/bin/env python3
"""Fetch latest MiMo pay-as-you-go pricing from official Xiaomi docs.

Usage:
    python scripts/update_pricing.py              # show diff
    python scripts/update_pricing.py --apply      # write to model_pricing.json
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

PRICING_URL = "https://platform.xiaomimimo.com/docs/en-US/price/pay-as-you-go"
LOCAL_FILE = Path(__file__).parent / "model_pricing.json"

# All known MiMo chat models (skip ASR/TTS)
CHAT_MODELS = {"mimo-v2.5", "mimo-v2.5-pro", "mimo-v2-flash", "mimo-v2-omni", "mimo-v2-pro"}


def fetch_page() -> str:
    r = httpx.get(PRICING_URL, follow_redirects=True, timeout=15)
    r.raise_for_status()
    return r.text


def parse_overseas_pricing(html: str) -> dict[str, dict[str, float]]:
    """Extract overseas USD pricing by scanning full document text.

    Finds every 'model-name $X $Y $Z' pattern where model is a known chat model.
    No table-index dependency.
    """
    # Strip all HTML to plain text
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    models = {}
    for model in CHAT_MODELS:
        # Find: model_name $A $B $C (three consecutive dollar amounts after the model name)
        pattern = re.escape(model) + r"\s+\$([0-9.]+)\s+\$([0-9.]+)\s+\$([0-9.]+)"
        match = re.search(pattern, text)
        if match:
            # First match per model is overseas (domestic uses ¥, not $)
            models[model] = {
                "input_per_1m_cache_hit": float(match.group(1)),
                "input_per_1m_cache_miss": float(match.group(2)),
                "output_per_1m": float(match.group(3)),
            }

    return models


def main():
    apply_mode = "--apply" in sys.argv

    print("Fetching pricing from", PRICING_URL)
    html = fetch_page()
    fetched = parse_overseas_pricing(html)

    if not fetched:
        print("ERROR: No pricing found in page. HTML structure may have changed.")
        sys.exit(1)

    with open(LOCAL_FILE) as f:
        current = json.load(f)

    print("\n=== Current (model_pricing.json) ===")
    for m, r in sorted(current.get("models", {}).items()):
        print(
            f"  {m}: hit=${r['input_per_1m_cache_hit']}, miss=${r['input_per_1m_cache_miss']}, out=${r['output_per_1m']}"
        )

    print("\n=== Fetched (official docs — overseas USD) ===")
    for m, r in sorted(fetched.items()):
        print(
            f"  {m}: hit=${r['input_per_1m_cache_hit']}, miss=${r['input_per_1m_cache_miss']}, out=${r['output_per_1m']}"
        )

    print("\n=== Diff ===")
    has_diff = False
    all_models = sorted(set(list(current.get("models", {}).keys()) + list(fetched.keys())))
    for model in all_models:
        curr = current.get("models", {}).get(model, {})
        fetch = fetched.get(model, {})
        if curr != fetch:
            has_diff = True
            if model not in current.get("models", {}):
                print(f"  {model}: NEW (not in local)")
            elif model not in fetched:
                print(f"  {model}: NOT in fetched (local only)")
            else:
                for key in ["input_per_1m_cache_hit", "input_per_1m_cache_miss", "output_per_1m"]:
                    c = curr.get(key, "N/A")
                    f = fetch.get(key, "N/A")
                    if c != f:
                        print(f"  {model}.{key}: {c} -> {f}")

    if not has_diff:
        print("  No differences found.")

    if apply_mode:
        for model, rates in fetched.items():
            current["models"][model] = rates
        current["source"] = PRICING_URL
        current["effective_date"] = datetime.now(UTC).strftime("%Y-%m-%d")
        with open(LOCAL_FILE, "w") as f:
            json.dump(current, f, indent=2)
            f.write("\n")
        print(f"\nUpdated {LOCAL_FILE}")
    else:
        print(f"\nRun with --apply to update {LOCAL_FILE}")


if __name__ == "__main__":
    main()
