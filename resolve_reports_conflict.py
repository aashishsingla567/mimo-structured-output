#!/usr/bin/env python3
"""Auto-resolve merge conflicts in reports.json by keeping the newer run.

Reports.json is overwritten each test run, so when two branches both run
tests, git marks the whole file as conflicted. This script parses both
sides of the conflict, compares run IDs (timestamps), and keeps the newer one.

Usage:
    python resolve_reports_conflict.py
    python resolve_reports_conflict.py --dry-run
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPORTS_FILE = Path(__file__).parent / "reports.json"

CONFLICT_PATTERN = re.compile(
    r"^<<<<<<<\s+HEAD\n"
    r"(?P<ours>.*?)\n"
    r"^=======\n"
    r"(?P<theirs>.*?)\n"
    r"^>>>>>>>\s+.*$",
    re.MULTILINE | re.DOTALL,
)


def extract_run_id(text: str) -> str | None:
    """Extract the run ID from a reports.json fragment."""
    try:
        data = json.loads(text)
        runs = data.get("runs", [])
        if runs:
            return runs[-1].get("id", "")
    except json.JSONDecodeError:
        pass
    return None


def parse_run_timestamp(run_id: str) -> datetime | None:
    """Parse run ID timestamp (format: YYYYMMDD_HHMMSS)."""
    try:
        return datetime.strptime(run_id, "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def resolve_conflict(content: str) -> str | None:
    """Resolve conflict markers by keeping the newer run."""
    match = CONFLICT_PATTERN.search(content)
    if not match:
        return None

    ours_id = extract_run_id(match.group("ours"))
    theirs_id = extract_run_id(match.group("theirs"))

    if not ours_id or not theirs_id:
        print("  Could not parse run IDs from conflict, keeping HEAD (ours)")
        winner_content = match.group("ours")
    else:
        ours_time = parse_run_timestamp(ours_id)
        theirs_time = parse_run_timestamp(theirs_id)

        if ours_time and theirs_time:
            if theirs_time > ours_time:
                winner = "theirs"
                winner_content = match.group("theirs")
            else:
                winner = "ours"
                winner_content = match.group("ours")
        else:
            if theirs_id > ours_id:
                winner = "theirs"
                winner_content = match.group("theirs")
            else:
                winner = "ours"
                winner_content = match.group("ours")

        print(f"  HEAD run:     {ours_id}")
        print(f"  Incoming run: {theirs_id}")
        print(f"  Winner:       {winner} ({max(ours_id, theirs_id)})")

    try:
        winner_data = json.loads(winner_content)
        return json.dumps(winner_data, indent=2)
    except json.JSONDecodeError:
        return content[: match.start()] + winner_content + content[match.end() :]


def main():
    dry_run = "--dry-run" in sys.argv

    if not REPORTS_FILE.exists():
        print("No reports.json found.")
        sys.exit(1)

    content = REPORTS_FILE.read_text()

    if "<<<<<<" not in content:
        print("No merge conflicts in reports.json.")
        sys.exit(0)

    conflicts = list(CONFLICT_PATTERN.finditer(content))
    print(f"Found {len(conflicts)} conflict(s) in reports.json.")

    resolved = resolve_conflict(content)
    if resolved is None:
        print("ERROR: Could not parse conflict. Resolve manually.")
        sys.exit(1)

    if "<<<<<<" in resolved:
        print("ERROR: Multiple conflicts found. Resolve manually.")
        sys.exit(1)

    try:
        data = json.loads(resolved)
        runs = data.get("runs", [])
        print(f"Valid JSON with {len(runs)} run(s).")
    except json.JSONDecodeError as e:
        print(f"ERROR: Result is not valid JSON: {e}")
        sys.exit(1)

    if dry_run:
        print("Dry run — not writing file.")
    else:
        REPORTS_FILE.write_text(resolved)
        print("Resolved reports.json.")

    final_run = data["runs"][-1] if data.get("runs") else None
    if final_run:
        summary = final_run.get("summary", {})
        print(f"\nFinal run: {final_run.get('id')}")
        print(f"  Model:    {final_run.get('model')}")
        print(f"  Passed:   {summary.get('passed')}/{summary.get('total')}")
        print(f"  Cost:     ${summary.get('total_cost_usd', 0):.4f}")


if __name__ == "__main__":
    main()
