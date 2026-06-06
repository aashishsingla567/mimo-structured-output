import logging
from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.purchase_order import PurchaseOrder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent.parent / "test_documents" / "sanity"


@pytest.mark.sanity
def test_purchase_order_extraction(record_result):
    doc = (TEST_DOCS_DIR / "purchase_order_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=PurchaseOrder,
        tool_name="parse_purchase_order",
        tool_description="Parse an OCR-scanned purchase order into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["po_number"], "po_number missing"
    assert "0892" in data["po_number"]

    assert data["date"], "date missing"
    assert data["buyer"], "buyer missing"
    assert data["seller"], "seller missing"

    assert "Reliance" in data["buyer"]["name"] or "RELIANCE" in data["buyer"]["name"]
    assert "Samsung" in data["seller"]["name"] or "SAMSUNG" in data["seller"]["name"]

    items = data["items"]
    assert len(items) == 4

    assert items[0]["quantity"] == 10
    assert items[0]["unit_price"] == 134999.00

    assert data["total_amount"] == 3469070.20

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


@pytest.mark.sanity
def test_purchase_order_messy_ocr(record_result):
    """Messy OCR: 4 items extracted, numeric values correct, typos preserved."""
    doc = (TEST_DOCS_DIR / "purchase_order_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=PurchaseOrder,
        tool_name="parse_purchase_order",
        tool_description="Parse an OCR-scanned purchase order into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["po_number"], "po_number missing"
    assert data["buyer"], "buyer missing"
    assert data["seller"], "seller missing"

    items = data["items"]
    assert len(items) == 4
    assert data["total_amount"] == 3469070.20

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )
