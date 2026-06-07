import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from filelock import FileLock

from utils import (
    REPO_ROOT,
    REPORTS_FILE,
    TokenUsage,
    calculate_cost,
    env,
)

# Collects test results on the coordinator. Populated by pytest_runtest_logreport
# which receives serialized reports from all xdist workers automatically.
_test_results: dict[str, dict] = {}

# Worker observability: tracks active test per worker
_worker_status: dict[str, str] = {}  # worker_id -> test name
_worker_start: dict[str, float] = {}  # worker_id -> start time


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
    """Fixture that tests call to record their ExtractionResult stats.

    Stores data on user_properties so xdist can serialize it to the coordinator.
    """
    store = {}

    def _record(result):
        store["time_s"] = round(result.elapsed, 2)
        store["input_tokens"] = result.input_tokens
        store["output_tokens"] = result.output_tokens
        store["cached_tokens"] = result.cached_tokens
        store["attempts"] = result.attempts

    return _record, store


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Runs in each worker. Stores test info on the report for xdist serialization."""
    outcome = yield
    report = outcome.get_result()
    if call.when == "call":
        info = {
            "name": item.nodeid,
            "status": "passed" if report.outcome == "passed" else "failed",
            "time_s": round(report.duration, 2),
        }
        for fixture_name, fixture_val in item.funcargs.items():
            if fixture_name == "record_result" and isinstance(fixture_val, tuple):
                _, store = fixture_val
                if store:
                    info.update(store)
        report.user_properties = [("test_result_info", info)]


def pytest_runtest_logreport(report):
    """Runs on the coordinator. Receives serialized reports from all workers."""
    if report.when == "call":
        worker_id = getattr(report, "worker_id", "?")
        _test_results[report.nodeid] = {
            "name": report.nodeid,
            "status": report.outcome,
            "time_s": round(report.duration, 2),
            "worker_id": worker_id,
        }
        for key, value in report.user_properties:
            if key == "test_result_info":
                _test_results[report.nodeid].update(value)
                break

        # Worker observability
        status = "PASS" if report.outcome == "passed" else "FAIL"
        elapsed = report.duration
        icon = "\u2713" if status == "PASS" else "\u2717"
        print(
            f"  [{worker_id}] {icon} {report.nodeid.split('::')[-1]} ({elapsed:.1f}s)",
            flush=True,
        )


def pytest_sessionstart(session):
    session._session_start = datetime.now(UTC)


def pytest_sessionfinish(session, exitstatus):
    # Only the coordinator writes the report
    try:
        from xdist import is_xdist_worker

        if is_xdist_worker(session):
            return
    except ImportError:
        pass

    suite = session.config.getoption("--suite")
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    wall_time = (datetime.now(UTC) - session._session_start).total_seconds()

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

    # Iterate _test_results directly (coordinator has empty session.items)
    for _nodeid, info in _test_results.items():
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
            "wall_time_s": round(wall_time, 2),
            "total_time_s": round(total_time, 2),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_cached_tokens": total_cached,
            "total_cost_usd": total_cost,
            "avg_attempts": avg_attempts,
        },
        "tests": tests,
    }

    lock_path = Path(str(REPORTS_FILE) + ".lock")
    with FileLock(lock_path):
        existing = {"runs": []}
        if REPORTS_FILE.exists():
            content = REPORTS_FILE.read_text().strip()
            if content:
                existing = json.loads(content)
        existing["runs"].append(run_entry)
        REPORTS_FILE.write_text(json.dumps(existing, separators=(",", ":")))

    # Print per-worker summary
    worker_tests: dict[str, list[str]] = {}
    for info in _test_results.values():
        wid = info.get("worker_id", "?")
        worker_tests.setdefault(wid, []).append(info["name"].split("::")[-1])

    if worker_tests and len(worker_tests) > 1:
        print("\nWorker summary:")
        for wid in sorted(worker_tests):
            tests = worker_tests[wid]
            print(f"  {wid}: {len(tests)} tests")

    print(f"\nReport written to {REPORTS_FILE} (run {run_id})")
