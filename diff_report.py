#!/usr/bin/env python3
"""Compare current reports.json with the previous committed version."""

import json
import subprocess
import sys
from pathlib import Path

REPORTS_FILE = Path(__file__).parent / "reports.json"
REPO_ROOT = Path(__file__).parent


def get_previous_reports():
    """Get reports.json from the previous commit."""
    try:
        result = subprocess.run(
            ["git", "show", "HEAD~1:reports.json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, Exception):
        return None


def get_current_reports():
    """Get current reports.json."""
    if not REPORTS_FILE.exists():
        return None
    with open(REPORTS_FILE) as f:
        return json.load(f)


def fmt_delta(curr, prev, lower_is_better=True):
    """Format delta with arrow indicator."""
    if prev is None or curr is None:
        return "N/A"
    diff = curr - prev
    if diff == 0:
        return f"{curr} (=)"
    arrow = "↓" if (diff < 0) == lower_is_better else "↑"
    pct = (diff / prev * 100) if prev != 0 else 0
    sign = "+" if diff > 0 else ""
    return f"{curr} ({sign}{diff:.1f}, {sign}{pct:.1f}% {arrow})"


def compare_runs(prev_run, curr_run):
    """Compare two runs and print diff."""
    prev_s = prev_run.get("summary", {})
    curr_s = curr_run.get("summary", {})

    print(f"\n{'Metric':<30} {'Previous':<25} {'Current':<25} {'Delta'}")
    print("-" * 105)

    rows = [
        ("Suite", prev_run.get("suite"), curr_run.get("suite"), None),
        ("Total tests", prev_s.get("total"), curr_s.get("total"), None),
        ("Passed", prev_s.get("passed"), curr_s.get("passed"), None),
        ("Failed", prev_s.get("failed"), curr_s.get("failed"), None),
        ("Accuracy %", prev_s.get("accuracy_pct"), curr_s.get("accuracy_pct"), False),
        ("Wall time (s)", prev_s.get("wall_time_s"), curr_s.get("wall_time_s"), True),
        (
            "Input tokens",
            prev_s.get("total_input_tokens"),
            curr_s.get("total_input_tokens"),
            True,
        ),
        (
            "Output tokens",
            prev_s.get("total_output_tokens"),
            curr_s.get("total_output_tokens"),
            True,
        ),
        (
            "Cost (USD)",
            prev_s.get("total_cost_usd"),
            curr_s.get("total_cost_usd"),
            True,
        ),
        ("Avg attempts", prev_s.get("avg_attempts"), curr_s.get("avg_attempts"), True),
    ]

    for label, prev, curr, lower_better in rows:
        if lower_better is None:
            prev_str = str(prev) if prev is not None else "N/A"
            curr_str = str(curr) if curr is not None else "N/A"
            delta = "=" if prev == curr else "→"
        else:
            prev_str = f"{prev:.1f}" if isinstance(prev, float) else str(prev)
            curr_str = f"{curr:.1f}" if isinstance(curr, float) else str(curr)
            delta = fmt_delta(curr, prev, lower_better)
        print(f"{label:<30} {prev_str:<25} {curr_str:<25} {delta}")

    # Per-test comparison
    prev_tests = {t["name"]: t for t in prev_run.get("tests", [])}
    curr_tests = {t["name"]: t for t in curr_run.get("tests", [])}

    all_tests = sorted(set(list(prev_tests.keys()) + list(curr_tests.keys())))
    regressed = []
    improved = []

    for name in all_tests:
        pt = prev_tests.get(name)
        ct = curr_tests.get(name)
        if pt and ct:
            pa = pt.get("attempts", 1)
            ca = ct.get("attempts", 1)
            if ca > pa:
                regressed.append((name, pa, ca))
            elif ca < pa:
                improved.append((name, pa, ca))

    if regressed:
        print(f"\n⚠ Regressed (more attempts):")
        for name, pa, ca in regressed:
            print(f"  {name}: {pa} → {ca}")

    if improved:
        print(f"\n✓ Improved (fewer attempts):")
        for name, pa, ca in improved:
            print(f"  {name}: {pa} → {ca}")


def main():
    prev_data = get_previous_reports()
    curr_data = get_current_reports()

    if not curr_data:
        print("No current reports.json found.")
        sys.exit(1)

    curr_runs = curr_data.get("runs", [])
    if not curr_runs:
        print("No runs in current reports.json.")
        sys.exit(1)

    curr_run = curr_runs[-1]

    if not prev_data or not prev_data.get("runs"):
        print("No previous run found in git history.")
        print(f"\nCurrent run: {curr_run.get('id')} ({curr_run.get('date')})")
        sys.exit(0)

    prev_run = prev_data["runs"][-1]

    print(f"Comparing: {prev_run.get('id')} → {curr_run.get('id')}")
    compare_runs(prev_run, curr_run)


if __name__ == "__main__":
    main()
