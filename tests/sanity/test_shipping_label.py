import logging

import pytest

from extraction import extract_structured, get_client
from schemas.shipping_label import ShippingLabel
from tests.conftest import TEST_DOCS_SANITY

log = logging.getLogger(__name__)


@pytest.mark.sanity
def test_shipping_label_extraction(record_result):
    doc = (TEST_DOCS_SANITY / "shipping_label_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=ShippingLabel,
        tool_name="parse_shipping_label",
        tool_description="Parse an OCR-scanned shipping label into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["tracking_number"], "tracking_number missing"
    assert "DTDC" in data["tracking_number"] or "98765" in data["tracking_number"]

    assert data["sender"], "sender missing"
    assert data["recipient"], "recipient missing"

    assert "Priyanka" in data["sender"]["name"] or "Verma" in data["sender"]["name"]
    assert "Vikram" in data["recipient"]["name"] or "Singh" in data["recipient"]["name"]

    assert data["sender"]["city"] == "Kolkata"
    assert data["recipient"]["city"] == "Gurugram"

    assert data["weight"], "weight missing"
    assert data["pieces"] == 1

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
def test_shipping_label_messy_ocr(record_result):
    """Messy OCR: tracking, addresses extracted, typos like 'Vermma' preserved."""
    doc = (TEST_DOCS_SANITY / "shipping_label_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=ShippingLabel,
        tool_name="parse_shipping_label",
        tool_description="Parse an OCR-scanned shipping label into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["tracking_number"], "tracking_number missing"
    assert data["sender"], "sender missing"
    assert data["recipient"], "recipient missing"
    assert data["sender"]["city"] == "Kolkata"
    assert data["recipient"]["city"] == "Gurugram"
    assert data["pieces"] == 1

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )
