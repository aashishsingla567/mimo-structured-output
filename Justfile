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

# Run sanity tests only
test-sanity:
    uv run pytest --suite=sanity

# Clean generated files
clean:
    rm -rf reports.json .pytest_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Update pricing from official docs
update-pricing:
    uv run python update_pricing.py --apply
