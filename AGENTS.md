# AGENTS.md

Extracts structured JSON from OCR text using LLM tool-call forced output + Pydantic validation.

## Commands

```bash
uv sync                              # install deps
uv run pytest --suite=sanity         # 14 hand-crafted tests (fast, default)
uv run pytest --suite=real           # 13 real OCR tests (receipts, invoices, financial docs)
uv run pytest --suite=full           # 27 tests total
uv run pytest --suite=full           # run + always write reports.json (guard: must be committed first)
uv run python commit_report.py       # commit reports.json with summary message
```

Single test: `uv run pytest tests/sanity/test_receipt.py::test_receipt_extraction -v`

## Key Gotchas

- **`.env` required**: `MIMO_API_KEY` must be set. `get_client()` reads `os.environ["MIMO_API_KEY"]` directly — no fallback.
- **`reports.json` guard**: Running with `--report` blocks if `reports.json` has uncommitted changes. Must `uv run python commit_report.py` first, or `git checkout -- reports.json`.
- **`pythonpath = ["."]`** in pyproject.toml is what makes `from extraction import ...` work in tests. Don't remove it.
- **`record_result` fixture**: Every test function that calls `extract_structured` must accept `record_result` as a parameter and call `record, _ = record_result; record(result)` to capture stats for reports.json. Tests without this fixture still run but won't report token/time stats.
- **Nested JSON coercion**: mimo-v2.5 sometimes returns nested objects as JSON strings in tool args. `_coerce_nested_json_strings()` in extraction.py handles this — always run it before `model_validate()`.
- **`thinking` disabled**: The API call uses `extra_body={"thinking": {"type": "disabled"}}` — this is model-specific, not standard OpenAI.

## Structure

- `extraction.py` — `extract_structured()`, `ExtractionConfig`, `ExtractionResult`, `_coerce_nested_json_strings()`
- `schemas/` — one Pydantic model per document type (11 total)
  - Receipt, Invoice, Simple Invoice, Business Card, Prescription, Bank Statement, Purchase Order, Shipping Label
  - `uk_balance_sheet.py` — UK Companies House balance sheets
  - `indian_pnl.py` — Indian multi-column P&L statements
  - `cas_statement.py` — CAMS/KFintech mutual fund CAS statements
- `tests/sanity/` — hand-crafted OCR, exact value assertions
- `tests/real/` — real OCR from [mertbek10/receipt-OCR](https://github.com/mertbek10/receipt-OCR), [DocILE](https://github.com/eliottthomas99/Data_QUEST), [Companies House](https://github.com/ap539813/Financial-data-extraction-from-ocr-images), Loyal Textile Mills, and [Scribd CAS](https://www.scribd.com/document/989793884/Cas); structural assertions only
- `test_documents/sanity/` and `test_documents/real/` — OCR text inputs
- `conftest.py` — `--suite`/`--report` flags, `record_result` fixture, stats collection, reports.json guard
- `commit_report.py` — commits reports.json with test summary in message
- `reports.json` — accumulated test run stats (committed, not gitignored)

## Conventions

- One schema per file in `schemas/`, one test file per type in `tests/sanity/`
- Tests use `@pytest.mark.sanity` or `@pytest.mark.real`
- Tests assert structure correctness, not OCR accuracy — typos from messy OCR are preserved as-is
- Adding a new doc type: add schema in `schemas/`, test in `tests/sanity/`, OCR text in `test_documents/sanity/`
