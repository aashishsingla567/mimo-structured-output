import logging
from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.receipt import RestaurantReceipt
from schemas.invoice import Invoice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"

REAL_RECEIPT_FILES = [
    "receipt_real_1.txt",
    "receipt_real_2.txt",
    "receipt_real_3.txt",
    "receipt_real_4.txt",
    "receipt_real_5.txt",
]

REAL_INVOICE_FILES = [
    "invoice_real_1.txt",
    "invoice_real_2.txt",
    "invoice_real_3.txt",
    "invoice_real_4.txt",
    "invoice_real_5.txt",
]


@pytest.mark.parametrize("receipt_file", REAL_RECEIPT_FILES)
def test_real_receipt_extraction(receipt_file):
    """Real OCR receipts from Malaysian supermarkets (Tesseract output)."""
    doc = (TEST_DOCS_DIR / receipt_file).read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=RestaurantReceipt,
        tool_name="parse_receipt",
        tool_description="Parse an OCR-scanned receipt into structured data.",
    )

    data = result.data

    assert data["merchant_name"], f"{receipt_file}: merchant_name missing"
    assert data["total"] > 0, f"{receipt_file}: total must be positive"
    assert len(data["items"]) > 0, f"{receipt_file}: must have at least 1 item"

    for item in data["items"]:
        assert item["description"], f"{receipt_file}: item description missing"
        assert item["amount"] >= 0, f"{receipt_file}: item amount must be non-negative"

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED real receipt %s — attempts=%d time=%.2fs tokens=%d/%d items=%d total=%.2f",
        receipt_file,
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
        len(data["items"]),
        data["total"],
    )


@pytest.mark.parametrize("invoice_file", REAL_INVOICE_FILES)
def test_real_invoice_extraction(invoice_file):
    """Real OCR invoices from DocILE (US business documents, DocTR output)."""
    doc = (TEST_DOCS_DIR / invoice_file).read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=Invoice,
        tool_name="parse_invoice",
        tool_description="Parse an OCR-scanned invoice into structured data.",
    )

    data = result.data

    assert data["invoice_number"], f"{invoice_file}: invoice_number missing"
    assert data["customer"], f"{invoice_file}: customer missing"
    assert len(data["items"]) > 0, f"{invoice_file}: must have at least 1 item"
    assert data["summary"], f"{invoice_file}: summary missing"

    for item in data["items"]:
        assert item["description"], f"{invoice_file}: item description missing"
        assert isinstance(item["amount"], (int, float)), (
            f"{invoice_file}: item amount must be numeric"
        )

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED real invoice %s — attempts=%d time=%.2fs tokens=%d/%d items=%d",
        invoice_file,
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
        len(data["items"]),
    )
