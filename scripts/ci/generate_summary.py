#!/usr/bin/env python3
"""Generate GitHub Actions job summary from reports.json."""

import json
from pathlib import Path


def main():
    path = Path("reports.json")
    if not path.exists():
        print("### Tests")
        print("No reports.json generated.")
        return

    data = json.loads(path.read_text())
    runs = data.get("runs", [])
    if not runs:
        print("### Tests")
        print("No runs found in reports.json.")
        return

    run = runs[-1]
    s = run["summary"]
    model = run.get("model", "unknown")
    run_id = run.get("id", "unknown")

    status = "PASS" if s["failed"] == 0 else "FAIL"
    emoji = "&#9989;" if status == "PASS" else "&#10060;"

    print(f"### {emoji} Test Results — `{model}`")
    print()
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Status | **{status}** |")
    print(f"| Passed | {s['passed']}/{s['total']} |")
    print(f"| Accuracy | {s['accuracy_pct']}% |")
    print(f"| Wall time | {s['wall_time_s']}s |")
    print(f"| Input tokens | {s['total_input_tokens']:,} |")
    print(f"| Output tokens | {s['total_output_tokens']:,} |")
    print(f"| Cached tokens | {s.get('total_cached_tokens', 0):,} |")
    print(f"| Cost | ${s['total_cost_usd']:.4f} |")
    print(f"| Avg attempts | {s['avg_attempts']} |")
    print(f"| Run ID | `{run_id}` |")
    print()

    failed = [t for t in run["tests"] if t["status"] == "failed"]
    if failed:
        print("### Failed Tests")
        print()
        print("| Test | Attempts |")
        print("|------|----------|")
        for t in failed:
            print(f"| `{t['name']}` | {t.get('attempts', 1)} |")
        print()


if __name__ == "__main__":
    main()
