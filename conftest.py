import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPORTS_FILE = Path(__file__).parent / "reports.json"
PRICING_FILE = Path(__file__).parent / "model_pricing.json"
REPO_ROOT = Path(__file__).parent


def _is_reports_json_dirty():
    """Check if reports.json has uncommitted changes (staged or unstaged)."""
    if not REPORTS_FILE.exists():
        return False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "reports.json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def _load_pricing():
    """Load model pricing from model_pricing.json."""
    if not PRICING_FILE.exists():
        return None
    with open(PRICING_FILE) as f:
        return json.load(f)


def _calculate_cost(input_tokens, output_tokens, model="mimo-v2.5"):
    """Calculate cost in USD for given token counts."""
    pricing = _load_pricing()
    if not pricing or model not in pricing["models"]:
        return None
    rates = pricing["models"][model]
    # Use cache miss pricing for input (worst case)
    input_cost = (input_tokens / 1_000_000) * rates["input_per_1m_cache_miss"]
    output_cost = (output_tokens / 1_000_000) * rates["output_per_1m"]
    return round(input_cost + output_cost, 6)


def pytest_configure(config):
    """Block test runs if reports.json has uncommitted changes."""
    if _is_reports_json_dirty():
        pytest.exit(
            "\n\nreports.json has uncommitted changes.\n"
            "Commit or discard them before running tests:\n\n"
            "  git add reports.json && git commit -m 'Update test report'\n"
            "  # or\n"
            "  git checkout -- reports.json\n",
            returncode=1,
        )
    # Set model from --model option
    model = config.getoption("--model")
    os.environ["MIMO_MODEL"] = model


def pytest_addoption(parser):
    parser.addoption(
        "--suite",
        action="store",
        default="sanity",
        choices=["sanity", "real", "full"],
        help="Test suite to run: sanity, real, or full",
    )
    parser.addoption(
        "--model",
        action="store",
        default="mimo-v2.5",
        help="Model to use for extraction (default: mimo-v2.5)",
    )
    parser.addoption(
        "--report",
        action="store_true",
        default=False,
        help="(deprecated) Reports are now always written",
    )


def pytest_collection_modifyitems(config, items):
    suite = config.getoption("--suite")
    if suite == "full":
        return

    skip_real = pytest.mark.skip(reason="use --suite=real or --suite=full")
    skip_sanity = pytest.mark.skip(reason="use --suite=sanity or --suite=full")

    for item in items:
        if suite == "sanity" and "real" in item.keywords:
            item.add_marker(skip_real)
        elif suite == "real" and "sanity" in item.keywords:
            item.add_marker(skip_sanity)


@pytest.fixture
def record_result(request):
    """Fixture that tests call to record their ExtractionResult stats."""
    store = {}

    def _record(result):
        store["time_s"] = round(result.elapsed, 2)
        store["input_tokens"] = result.input_tokens
        store["output_tokens"] = result.output_tokens
        store["attempts"] = result.attempts

    return _record, store


def pytest_runtest_makereport(item, call):
    if call.when == "call":
        item._test_result_info = {
            "name": item.nodeid,
            "status": "passed" if call.excinfo is None else "failed",
            "time_s": round(call.duration, 2),
        }
        for fixture_name, fixture_val in item.funcargs.items():
            if fixture_name == "record_result" and isinstance(fixture_val, tuple):
                _, store = fixture_val
                if store:
                    item._test_result_info.update(store)


def pytest_sessionfinish(session, exitstatus):

    suite = session.config.getoption("--suite")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
        ).strip()
    except Exception:
        commit = "unknown"

    tests = []
    total = passed = failed = 0
    total_time = 0.0
    total_in = 0
    total_out = 0
    total_attempts = 0

    for item in session.items:
        info = getattr(item, "_test_result_info", None)
        if info is None:
            continue
        total += 1
        if info["status"] == "passed":
            passed += 1
        else:
            failed += 1
        total_time += info.get("time_s", 0)
        total_in += info.get("input_tokens", 0)
        total_out += info.get("output_tokens", 0)
        total_attempts += info.get("attempts", 0)

        test_entry = {
            "name": info["name"],
            "status": info["status"],
            "time_s": info.get("time_s", 0),
        }
        if "input_tokens" in info:
            test_entry["input_tokens"] = info["input_tokens"]
            test_entry["output_tokens"] = info["output_tokens"]
            test_entry["attempts"] = info["attempts"]
            test_entry["cost_usd"] = _calculate_cost(
                info["input_tokens"], info["output_tokens"]
            )
        tests.append(test_entry)

    accuracy_pct = round((passed / total * 100), 1) if total > 0 else 0.0
    avg_attempts = round(total_attempts / total, 2) if total > 0 else 0
    total_cost = _calculate_cost(total_in, total_out)

    run_entry = {
        "id": run_id,
        "commit": commit,
        "date": datetime.now(timezone.utc).isoformat(),
        "suite": suite,
        "model": os.environ.get("MIMO_MODEL", "mimo-v2.5"),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy_pct": accuracy_pct,
            "wall_time_s": round(total_time, 2),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_cost_usd": total_cost,
            "avg_attempts": avg_attempts,
        },
        "tests": tests,
    }

    reports = {"runs": [run_entry]}

    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=2)

    print(f"\nReport written to {REPORTS_FILE} (run {run_id})")
