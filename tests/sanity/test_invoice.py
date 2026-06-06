from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.invoice import Invoice
from tests.conftest import TEST_DOCS_SANITY
import logging

log = logging.getLogger(__name__)


@pytest.mark.sanity
def test_invoice_extraction(record_result):
    doc = (TEST_DOCS_SANITY / "invoice_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=Invoice,
        tool_name="parse_invoice",
        tool_description="Parse an OCR-scanned invoice into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["invoice_number"] == "INV-2026-00481"

    cust = data["customer"]
    assert "Acme" in cust["name"]
    assert "Bangalore" in cust["address"]
    assert cust["email"] == "accounts@acmetrading.co.in"

    items = data["items"]
    assert len(items) == 3
    assert items[0]["description"] == "Wireless Mouse"
    assert items[0]["quantity"] == 2
    assert items[0]["unit_price"] == 899.0
    assert items[0]["amount"] == 1798.0
    assert items[1]["description"] == "Mechanical Keyboard"
    assert items[2]["description"] == "USB-C Hub"

    s = data["summary"]
    assert s["subtotal"] == 6796.0
    assert s["discount"] == 339.8
    assert s["taxable_value"] == 6456.2
    assert s["cgst"] == 581.06
    assert s["sgst"] == 581.06
    assert s["grand_total"] == 7618.32

    p = data["payment"]
    assert p["payment_terms"] == "Net 30 Days"
    assert p["bank_name"] == "HDFC BANK"
    assert p["account_number"] == "50100123456789"
    assert p["ifsc"] == "HDFC0001234"

    r = data["references"]
    assert r["sales_order"] == "SO-7782"
    assert r["customer_po"] == "PO-99182"

    assert result.attempts <= 3
    assert result.input_tokens > 0
    assert result.output_tokens > 0

    log.info(
        "PASSED — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )
