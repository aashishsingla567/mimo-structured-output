# mimo-structured-output

[![CI](https://github.com/aashishsingla567/mimo-structured-output/actions/workflows/test.yml/badge.svg)](https://github.com/aashishsingla567/mimo-structured-output/actions/workflows/test.yml)

Extract structured JSON from messy OCR text using an LLM with tool-call forced output, Pydantic validation, and automatic retry.

## Objective

OCR output from scanned documents is messy — misaligned columns, character substitutions, merged words, missing delimiters. Traditional regex-based extraction breaks down on real-world noise. This project uses an LLM's reasoning ability to understand the _semantic structure_ of messy text and extract clean, typed, validated data.

The core idea: **let the model do the parsing, let Pydantic do the validation, let the retry loop handle the rest.**

## How It Works

The pipeline forces the LLM to return structured output via a **tool call** (function calling), not free-form text:

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────┐
│  OCR text   │────▶│  LLM + tool  │────▶│  Validate  │────▶│  Result  │
│  (messy)    │     │  call        │     │  (Pydantic)│     │  (clean) │
└─────────────┘     └──────────────┘     └─────┬──────┘     └──────────┘
                                                │
                                          ┌─────▼──────┐
                                          │  Retry on  │
                                          │  failure   │
                                          └────────────┘
```

### Step by step

1. **Define a Pydantic schema** — describes the output shape (fields, types, nested models)
2. **Register a tool** — convert the Pydantic JSON schema into an OpenAI tool definition
3. **Force the tool call** — send the OCR text with `tool_choice` locked to our tool, so the model _must_ return structured JSON
4. **Parse and validate** — `json.loads()` → `_coerce_nested_json_strings()` → `schema.model_validate()`
5. **Retry on failure** — if validation fails, append the error message to the conversation and retry (up to 3 attempts)
6. **Return `ExtractionResult`** — validated dict + token counts + timing + attempt count

### Why tool calls instead of JSON mode?

| Approach                        | Problem                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------- |
| JSON mode / prompt engineering  | Model can still return free text, extra commentary, or malformed JSON                     |
| **Tool-call forced extraction** | Model is _required_ to fill in the tool arguments — no escape hatch, guaranteed structure |

The tool-call approach treats the LLM as a **function that takes text and returns typed data**, not a chatbot.

### Nested JSON coercion

Some models (including mimo-v2.5) occasionally serialize nested objects as JSON strings inside tool arguments:

```json
{ "customer": "{\"name\": \"Acme\", \"address\": \"Bangalore\"}" }
```

`_coerce_nested_json_strings()` recursively detects and parses these, so Pydantic validation succeeds transparently.

## Project Structure

```
mimo-structured-output/
├── extraction.py                 # Core pipeline: extract_structured(), ExtractionConfig, ExtractionResult
├── main.py                       # Example entry point
├── conftest.py                   # pytest: --suite/--model flags, stats collection, reports.json output
├── diff_report.py                # Compare current vs previous run (tokens, cost, time)
├── model_pricing.json            # Pricing per model (USD/1M tokens)
├── reports.json                  # Local test run stats (not committed — local tracking only)
│
├── utils/                        # Shared utilities
│   ├── __init__.py               #   Public exports
│   ├── env.py                    #   T3-style Pydantic BaseSettings for env validation
│   ├── tokens.py                 #   TokenUsage dataclass with cache-aware billing
│   ├── cost.py                   #   calculate_cost() with cache-hit/miss split pricing
│   └── constants.py              #   MAX_ATTEMPTS, MAX_COMPLETION_TOKENS, file paths
│
├── schemas/                      # One Pydantic model per document type (11 total)
│   ├── invoice.py                #   Detailed GST invoice (items, summary, payment, references)
│   ├── simple_invoice.py         #   Minimal invoice (id, total, currency, status)
│   ├── receipt.py                #   Restaurant bill (items, tax, tip)
│   ├── business_card.py          #   Contact card (name, company, phone, email)
│   ├── prescription.py           #   Medical Rx (medications, dosage, frequency)
│   ├── bank_statement.py         #   Account statement (transactions, balances)
│   ├── purchase_order.py         #   PO (buyer, seller, line items)
│   ├── shipping_label.py         #   Courier label (sender, recipient, tracking)
│   ├── uk_balance_sheet.py       #   UK Companies House balance sheet
│   ├── indian_pnl.py             #   Indian multi-column P&L
│   └── cas_statement.py          #   CAMS/KFintech mutual fund CAS
│
├── tests/
│   ├── sanity/                   # Hand-crafted clean/messy OCR tests (14 tests)
│   │   └── ...
│   └── real/                     # Real OCR from cloned datasets (13 tests)
│       ├── test_real_ocr.py      #   5 receipts + 5 invoices
│       └── test_complex_financial.py  # UK BS, Indian P&L, CAS
│
├── test_documents/
│   ├── sanity/                   # Hand-crafted OCR text (clean + messy variants)
│   └── real/                     # Real OCR output
│
├── .github/workflows/test.yml    # CI: runs full suite, job summary with results
├── pyproject.toml                # Project config, pytest markers, ruff config
└── .env                          # MIMO_API_KEY, MIMO_BASE_URL (gitignored)
```

## Quick Start

```bash
# Install
uv sync

# Set API key (Token Plan or Pay-as-you-go)
cp .env.example .env  # edit with your key

# Run example
uv run main.py

# Run tests
uv run pytest --suite=sanity      # 14 hand-crafted tests
uv run pytest --suite=real        # 13 real OCR tests
uv run pytest --suite=full        # all 27 tests

# Compare model performance
uv run pytest --suite=full --model=mimo-v2.5
uv run python diff_report.py      # show gains vs previous run
```

## API Endpoints

| Plan              | Base URL                                   | Key format | Supported models                                           |
| ----------------- | ------------------------------------------ | ---------- | ---------------------------------------------------------- |
| **Token Plan**    | `https://token-plan-sgp.xiaomimimo.com/v1` | `tp-xxxxx` | mimo-v2.5, mimo-v2.5-pro, mimo-v2-pro, mimo-v2-omni, + TTS |
| **Pay-as-you-go** | `https://api.xiaomimimo.com/v1`            | `sk-xxxxx` | All models including mimo-v2-flash                         |

Set via `MIMO_BASE_URL` in `.env`. Defaults to Token Plan.

## Test Suites

Tests are split into two categories:

### `sanity` (14 tests)

Hand-crafted OCR text — clean and messy variants for 8 document types. Tests assert **exact values** (amounts, counts, field presence) to verify the pipeline extracts correctly.

### `real` (10 tests)

Real OCR output from open-source datasets:

- **5 receipts** — Malaysian supermarket receipts (Tesseract OCR output from [mertbek10/receipt-OCR](https://github.com/mertbek10/receipt-OCR))
- **5 invoices** — US business documents (DocTR OCR output from [DocILE dataset](https://github.com/eliottthomas99/Data_QUEST))

Tests assert **structural correctness** — fields exist, types match, amounts are numeric. OCR artifacts are preserved as-is.

### CLI flags

```bash
uv run pytest --suite=sanity       # only sanity tests (default)
uv run pytest --suite=real         # only real OCR tests
uv run pytest --suite=full         # both suites
uv run pytest --model=mimo-v2.5    # select model (default: mimo-v2.5)
uv run pytest --model=mimo-v2-omni # compare with omni
```

## reports.json

Every test run writes a structured entry to `reports.json` (local tracking, not committed):

```json
{
  "runs": [
    {
      "id": "20260606_171350",
      "commit": "b0045bd",
      "date": "2026-06-06T17:13:50Z",
      "suite": "full",
      "model": "mimo-v2.5",
      "summary": {
        "total": 24,
        "passed": 24,
        "failed": 0,
        "accuracy_pct": 100.0,
        "wall_time_s": 92.74,
        "total_input_tokens": 24580,
        "total_output_tokens": 8320,
        "total_cost_usd": 0.0084,
        "avg_attempts": 1.0
      },
      "tests": [...]
    }
  ]
}
```

## Usage

```python
from extraction import get_client, extract_structured, ExtractionConfig
from schemas.invoice import Invoice

client = get_client()
result = extract_structured(
    client=client,
    document=ocr_text,
    schema=Invoice,
    tool_name="parse_invoice",
    tool_description="Parse an OCR invoice into structured data.",
    config=ExtractionConfig(model="mimo-v2.5", max_attempts=3),
)

print(result.data)           # validated dict
print(result.input_tokens)   # prompt tokens used
print(result.output_tokens)  # completion tokens used
print(result.cached_tokens)  # cache-hit tokens (cost savings)
print(result.elapsed)        # total time in seconds
print(result.attempts)       # API calls made
```

## API

### `ExtractionConfig`

| Field                   | Type    | Default                                      | Description          |
| ----------------------- | ------- | -------------------------------------------- | -------------------- |
| `model`                 | `str`   | `"mimo-v2.5"`                                | Model name           |
| `max_attempts`          | `int`   | `3`                                          | Retry limit          |
| `max_completion_tokens` | `int`   | `5120`                                       | Output token budget  |
| `temperature`           | `float` | `0`                                          | Deterministic output |
| `top_p`                 | `float` | `1`                                          | Nucleus sampling     |
| `base_url`              | `str`   | `"https://token-plan-sgp.xiaomimimo.com/v1"` | API endpoint         |

### `ExtractionResult`

| Field           | Type    | Description                                 |
| --------------- | ------- | ------------------------------------------- |
| `data`          | `dict`  | Validated Pydantic output                   |
| `input_tokens`  | `int`   | Total prompt tokens across all attempts     |
| `output_tokens` | `int`   | Total completion tokens across all attempts |
| `cached_tokens` | `int`   | Cache-hit tokens (cost savings)             |
| `elapsed`       | `float` | Wall-clock seconds                          |
| `attempts`      | `int`   | Number of API calls made                    |

## Schemas

| File                        | Model               | Use case                                                      |
| --------------------------- | ------------------- | ------------------------------------------------------------- |
| `schemas/invoice.py`        | `Invoice`           | Detailed GST invoice with items, summary, payment, references |
| `schemas/simple_invoice.py` | `InvoiceSummary`    | Minimal invoice (id, total, currency, status)                 |
| `schemas/receipt.py`        | `RestaurantReceipt` | Restaurant bill with items, tax, tip                          |
| `schemas/business_card.py`  | `BusinessCard`      | Contact card (name, company, phone, email)                    |
| `schemas/prescription.py`   | `Prescription`      | Medical Rx with medications and dosage                        |
| `schemas/bank_statement.py` | `BankStatement`     | Account statement with transaction history                    |
| `schemas/purchase_order.py` | `PurchaseOrder`     | PO with buyer, seller, line items                             |
| `schemas/shipping_label.py` | `ShippingLabel`     | Courier label with sender/recipient                           |

## Key Findings

### What works well

- **Structure inference from messy text** — model correctly parses tabular data even when columns are misaligned
- **OCR error preservation** — typos like `JUNCT1ON`, `B1ryani`, `Omeprazloe`, `Balanoe` are passed through as-is (the function structures data, it doesn't correct it)
- **Retry self-correction** — when validation fails (e.g., tip returned as `"None"` string), the model fixes it on retry using the error feedback
- **Real OCR tolerance** — handles genuine Tesseract/DocTR output with merged words, missing delimiters, and character noise

### What to watch for

- **Token limits** — complex schemas with many line items need `max_completion_tokens >= 1024`
- **Nested object serialization** — always run `_coerce_nested_json_strings` before Pydantic validation
- **Nil handling** — model may return `"None"` string instead of JSON `null` for optional fields
- **Schema complexity** — simpler schemas (InvoiceSummary) are faster and cheaper than complex ones (Invoice with 6 sub-models)

## Data Sources

Real OCR test documents sourced from:

| Source      | Type                 | Files     | Source repo                                                               |
| ----------- | -------------------- | --------- | ------------------------------------------------------------------------- |
| ICDAR-SROIE | Receipts (Tesseract) | 987 files | [mertbek10/receipt-OCR](https://github.com/mertbek10/receipt-OCR)         |
| DocILE      | Invoices (DocTR)     | 671 files | [eliottthomas99/Data_QUEST](https://github.com/eliottthomas99/Data_QUEST) |

## License

MIT
