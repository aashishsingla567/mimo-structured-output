# AGENTS.md

This project extracts structured JSON from OCR text using an LLM with tool-call forced output and Pydantic validation.

## Build & Test

```bash
uv sync                          # install dependencies
uv run pytest --suite=sanity     # 14 hand-crafted tests
uv run pytest --suite=real       # 10 real OCR tests
uv run pytest --suite=full       # all 24 tests
uv run pytest --suite=full --report  # run + write reports.json
uv run python commit_report.py   # commit reports.json
```

## Project Structure

- `extraction.py` — core pipeline (`extract_structured`, `ExtractionConfig`, `ExtractionResult`)
- `schemas/` — one Pydantic model per document type
- `tests/sanity/` — hand-crafted OCR tests with exact assertions
- `tests/real/` — real OCR from cloned datasets with structural assertions
- `conftest.py` — `--suite` flag, `--report` flag, stats collection
- `commit_report.py` — post-test script to commit reports.json

## Conventions

- One schema per file in `schemas/`
- One test file per document type in `tests/`
- Test documents in `test_documents/sanity/` and `test_documents/real/`
- Tests use `@pytest.mark.sanity` or `@pytest.mark.real` decorators
- Tests use `record_result` fixture to capture extraction stats
- Never commit `reports.json` without running `commit_report.py`
