#!/usr/bin/env python3
"""Post-test script: commit reports.json after a test run.

Usage:
    uv run pytest --suite=full --report && python commit_report.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
REPORTS_FILE = REPO_ROOT / "reports.json"


def main():
    if not REPORTS_FILE.exists():
        print("No reports.json found. Run tests with --report first.")
        sys.exit(1)

    # Check if there are actual changes
    result = subprocess.run(
        ["git", "diff", "--quiet", "reports.json"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        # Also check untracked
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "reports.json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            print("reports.json has no changes to commit.")
            sys.exit(0)

    # Get last run info from reports.json
    import json

    with open(REPORTS_FILE) as f:
        reports = json.load(f)

    last_run = reports["runs"][-1] if reports.get("runs") else {}
    run_id = last_run.get("id", "unknown")
    summary = last_run.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    failed = summary.get("failed", 0)
    accuracy = summary.get("accuracy_pct", 0)

    msg = f"test report: {passed}/{total} passed ({accuracy}%) [run {run_id}]"
    if failed > 0:
        msg += f" ({failed} FAILED)"

    subprocess.run(["git", "add", "reports.json"], cwd=str(REPO_ROOT), check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO_ROOT), check=True)
    print(f"Committed: {msg}")


if __name__ == "__main__":
    main()
