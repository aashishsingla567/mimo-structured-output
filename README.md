# mimo-structured-output

Structured data extraction from OCR documents using mimo-v2.5 with Pydantic validation and automatic retry.

## Quick Start

```bash
# Install
uv sync

# Set API key
echo 'MIMO_API_KEY="your-key"' > .env

# Run main example
uv run main.py

# Run all tests (8 doc types × 2 variants = 16 tests)
uv run python -m tests.test_simple_invoice
uv run python -m tests.test_invoice
uv run python -m tests.test_receipt
uv run python -m tests.test_business_card
uv run python -m tests.test_prescription
uv run python -m tests.test_bank_statement
uv run python -m tests.test_purchase_order
uv run python -m tests.test_shipping_label
```

## How It Works

```
OCR text → LLM (tool_call with Pydantic schema) → validate → retry on failure → structured JSON
```

The `extract_structured()` function:

1. Registers a tool whose JSON schema matches your Pydantic model
2. Sends the OCR text to mimo-v2.5 with forced `tool_choice`
3. Parses the tool call arguments
4. Validates against Pydantic schema
5. On failure, appends the validation error and retries (up to `max_attempts`)
6. Returns `ExtractionResult` with `.data`, token counts, and timing

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

## Test Documents

Each document type has two variants in `test_documents/`:

- **Clean OCR**: Well-formatted, readable text
- **Messy OCR** (`_messy.txt`): Character substitutions (`0`↔`O`, `l`↔`1`), merged words, missing characters — real-world scanner noise

Tests assert:

- **Structure is correct** — fields present, types match, counts/amounts are right
- **OCR errors are preserved** — the function structures data, it does NOT correct typos

## Key Findings

### mimo-v2.5 Performance

| Metric                            | Value             |
| --------------------------------- | ----------------- |
| Clean OCR first-attempt pass rate | 100% (8/8)        |
| Messy OCR first-attempt pass rate | 100% (8/8)        |
| Average latency                   | 2-6 seconds       |
| Average tokens (input/output)     | 400-1800 / 60-570 |

### What Works Well

- **Structure inference from messy text**: Model correctly parses tabular data even when columns are misaligned
- **OCR error preservation**: Typos like `JUNCT1ON`, `B1ryani`, `Omeprazloe`, `Balanoe` are passed through as-is
- **Nested JSON coercion**: Model sometimes serializes nested objects as JSON strings — `_coerce_nested_json_strings()` handles this transparently
- **Retry loop**: When validation fails (e.g., tip returned as `"None"` string), the model self-corrects on retry with the validation error feedback

### What to Watch For

- **Token limits matter**: Bank statements with 8+ transactions need `max_completion_tokens ≥ 1024` (default 5120)
- **Nested object serialization**: Some models return `{"customer": "{\"name\": \"...\"}"}` instead of proper nested JSON — always run `_coerce_nested_json_strings` before validation
- **Nil handling**: Model may return `"None"` string instead of JSON `null` for optional fields — Pydantic catches this as a validation error, triggering retry
- **Schema size**: Complex schemas (Invoice with 6 sub-models) work but use more tokens; simpler schemas (InvoiceSummary) are faster and cheaper

### Architecture Decisions

- **Tool-call forced extraction** > JSON mode: Forces structured output without prompt engineering tricks
- **Pydantic validation** as retry signal: Pass exact error back to model for self-correction
- **`_coerce_nested_json_strings`**: Necessary workaround for models that stringify nested objects in tool arguments
- **Per-file schemas**: One schema per file keeps models maintainable as document types grow

## Project Structure

```
mimo-structured-output/
├── .env                          # API key (gitignored)
├── extraction.py                 # Core: get_client(), extract_structured(), ExtractionConfig
├── main.py                       # Entry point with example
├── schemas/
│   ├── __init__.py
│   ├── invoice.py
│   ├── simple_invoice.py
│   ├── receipt.py
│   ├── business_card.py
│   ├── prescription.py
│   ├── bank_statement.py
│   ├── purchase_order.py
│   └── shipping_label.py
├── tests/
│   ├── test_simple_invoice.py
│   ├── test_invoice.py
│   ├── test_receipt.py
│   ├── test_business_card.py
│   ├── test_prescription.py
│   ├── test_bank_statement.py
│   ├── test_purchase_order.py
│   └── test_shipping_label.py
├── test_documents/
│   ├── simple_invoice.txt
│   ├── invoice_ocr.txt
│   ├── receipt_ocr.txt / receipt_ocr_messy.txt
│   ├── business_card_ocr.txt / business_card_ocr_messy.txt
│   ├── prescription_ocr.txt / prescription_ocr_messy.txt
│   ├── bank_statement_ocr.txt / bank_statement_ocr_messy.txt
│   ├── purchase_order_ocr.txt / purchase_order_ocr_messy.txt
│   └── shipping_label_ocr.txt / shipping_label_ocr_messy.txt
└── pyproject.toml
```

## API

### `ExtractionConfig`

```python
@dataclass
class ExtractionConfig:
    model: str = "mimo-v2.5"           # model name
    max_attempts: int = 3               # retry limit
    max_completion_tokens: int = 5120   # output token budget
    temperature: float = 0              # deterministic
    top_p: float = 1
    base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
```

### `ExtractionResult`

```python
@dataclass
class ExtractionResult:
    data: dict                          # validated Pydantic output
    input_tokens: int = 0               # total prompt tokens
    output_tokens: int = 0              # total completion tokens
    elapsed: float = 0.0                # wall-clock seconds
    attempts: int = 0                   # API calls made
```
