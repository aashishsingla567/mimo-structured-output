# mimo-structured-output

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
├── conftest.py                   # pytest: --suite flag, --report flag, stats collection
├── commit_report.py              # Post-test script: commits reports.json
├── reports.json                  # Auto-generated test run stats (time, tokens, accuracy)
│
├── schemas/                      # One Pydantic model per document type
│   ├── invoice.py                #   Detailed GST invoice (items, summary, payment, references)
│   ├── simple_invoice.py         #   Minimal invoice (id, total, currency, status)
│   ├── receipt.py                #   Restaurant bill (items, tax, tip)
│   ├── business_card.py          #   Contact card (name, company, phone, email)
│   ├── prescription.py           #   Medical Rx (medications, dosage, frequency)
│   ├── bank_statement.py         #   Account statement (transactions, balances)
│   ├── purchase_order.py         #   PO (buyer, seller, line items)
│   └── shipping_label.py         #   Courier label (sender, recipient, tracking)
│
├── tests/
│   ├── sanity/                   # Hand-crafted clean/messy OCR tests (14 tests)
│   │   ├── test_bank_statement.py
│   │   ├── test_business_card.py
│   │   ├── test_invoice.py
│   │   ├── test_prescription.py
│   │   ├── test_purchase_order.py
│   │   ├── test_receipt.py
│   │   ├── test_shipping_label.py
│   │   └── test_simple_invoice.py
│   └── real/                     # Real OCR from cloned datasets (10 tests)
│       └── test_real_ocr.py      #   5 receipts + 5 invoices, parametrized
│
├── test_documents/
│   ├── sanity/                   # Hand-crafted OCR text (clean + messy variants)
│   └── real/                     # Real OCR output (mertbek10/receipt-OCR, DocILE)
│
├── reports.json                  # Per-run stats: time, tokens, accuracy, attempts
├── pyproject.toml                # Project config, pytest markers
└── .env                          # MIMO_API_KEY (gitignored)
```

## Quick Start

```bash
# Install
uv sync

# Set API key
echo 'MIMO_API_KEY="your-key"' > .env

# Run example
uv run main.py

# Run tests
uv run pytest --suite=sanity      # 14 hand-crafted tests
uv run pytest --suite=real        # 10 real OCR tests
uv run pytest --suite=full        # all 24 tests

# Run with reporting
uv run pytest --suite=full --report
uv run python commit_report.py    # commit the report
```

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
uv run pytest --suite=full --report  # run + write stats to reports.json
```

## reports.json

Every run with `--report` appends a structured entry to `reports.json`:

```json
{
  "runs": [
    {
      "id": "20260606_171350",
      "commit": "b0045bd",
      "date": "2026-06-06T17:13:50Z",
      "suite": "full",
      "summary": {
        "total": 24,
        "passed": 24,
        "failed": 0,
        "accuracy_pct": 100.0,
        "wall_time_s": 92.74,
        "total_input_tokens": 24580,
        "total_output_tokens": 8320,
        "avg_attempts": 1.0
      },
      "tests": [
        {
          "name": "tests/sanity/test_receipt.py::test_receipt_extraction",
          "status": "passed",
          "time_s": 3.51,
          "input_tokens": 962,
          "output_tokens": 348,
          "attempts": 1
        }
      ]
    }
  ]
}
```

**Guard rule**: If `reports.json` has uncommitted changes, `--report` is blocked until you commit or discard:

```
reports.json has uncommitted changes.
Commit or discard them before running tests:
  git add reports.json && git commit -m 'Update test report'
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
