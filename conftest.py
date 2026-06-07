import json
import subprocess
from datetime import UTC, datetime

import pytest

from utils import (
    REPO_ROOT,
    REPORTS_FILE,
    TokenUsage,
    calculate_cost,
    env,
)


def pytest_configure(config):
    model = config.getoption("--model")
    env.MIMO_MODEL = model


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
        default=env.MIMO_MODEL,
        help=f"Model to use for extraction (default: {env.MIMO_MODEL})",
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
        store["cached_tokens"] = result.cached_tokens
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
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

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
    total_cached = 0
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
        total_cached += info.get("cached_tokens", 0)
        total_attempts += info.get("attempts", 0)

        test_entry = {
            "name": info["name"],
            "status": info["status"],
            "time_s": info.get("time_s", 0),
        }
        if "input_tokens" in info:
            test_entry["input_tokens"] = info["input_tokens"]
            test_entry["output_tokens"] = info["output_tokens"]
            test_entry["cached_tokens"] = info.get("cached_tokens", 0)
            test_entry["attempts"] = info["attempts"]
            test_usage = TokenUsage(
                prompt_tokens=info["input_tokens"],
                completion_tokens=info["output_tokens"],
                cached_tokens=info.get("cached_tokens", 0),
            )
            test_entry["cost_usd"] = calculate_cost(test_usage)
        tests.append(test_entry)

    accuracy_pct = round((passed / total * 100), 1) if total > 0 else 0.0
    avg_attempts = round(total_attempts / total, 2) if total > 0 else 0
    total_usage = TokenUsage(
        prompt_tokens=total_in,
        completion_tokens=total_out,
        cached_tokens=total_cached,
    )
    total_cost = calculate_cost(total_usage)

    run_entry = {
        "id": run_id,
        "commit": commit,
        "date": datetime.now(UTC).isoformat(),
        "suite": suite,
        "model": env.MIMO_MODEL,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy_pct": accuracy_pct,
            "wall_time_s": round(total_time, 2),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_cached_tokens": total_cached,
            "total_cost_usd": total_cost,
            "avg_attempts": avg_attempts,
        },
        "tests": tests,
    }

    reports = {"runs": [run_entry]}

    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, separators=(",", ":"))

    print(f"\nReport written to {REPORTS_FILE} (run {run_id})")
