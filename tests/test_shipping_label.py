import logging
from pathlib import Path

from extraction import get_client, extract_structured
from schemas.shipping_label import ShippingLabel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"


def test_shipping_label_extraction():
    doc = (TEST_DOCS_DIR / "shipping_label_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=ShippingLabel,
        tool_name="parse_shipping_label",
        tool_description="Parse an OCR-scanned shipping label into structured data.",
    )

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


def test_shipping_label_messy_ocr():
    """Messy OCR: tracking, addresses extracted, typos like 'Vermma' preserved."""
    doc = (TEST_DOCS_DIR / "shipping_label_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=ShippingLabel,
        tool_name="parse_shipping_label",
        tool_description="Parse an OCR-scanned shipping label into structured data.",
    )

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


if __name__ == "__main__":
    test_shipping_label_extraction()
    test_shipping_label_messy_ocr()
