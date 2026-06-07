# Development setup and common tasks

# Setup project from scratch
setup:
    uv sync
    uv run prek install

# Run all linters
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-fix lint and format issues
format:
    uv run ruff check --fix .
    uv run ruff format .

# Run full test suite
test:
    uv run pytest --suite=full

# Run full test suite in parallel (4 workers, ~80 RPM, well under 100 RPM limit)
test-parallel:
    uv run pytest --suite=full -n 4 --dist loadscope

# Run sanity tests only
test-sanity:
    uv run pytest --suite=sanity

# Clean generated files
clean:
    rm -rf reports.json .pytest_cache .xdist_results
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Update pricing from official docs
update-pricing:
    uv run python scripts/update_pricing.py --apply
