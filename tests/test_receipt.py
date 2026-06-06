import logging
from pathlib import Path

from extraction import get_client, extract_structured
from schemas.receipt import RestaurantReceipt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"


def test_receipt_extraction():
    doc = (TEST_DOCS_DIR / "receipt_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=RestaurantReceipt,
        tool_name="parse_receipt",
        tool_description="Parse an OCR-scanned restaurant receipt into structured data.",
    )

    data = result.data

    assert data["merchant_name"], "merchant_name missing"
    assert data["date"], "date missing"
    assert data["items"], "items missing"
    assert len(data["items"]) == 6

    item_descs = [i["description"] for i in data["items"]]
    assert any("Paneer" in d for d in item_descs)
    assert any("Biryani" in d for d in item_descs)
    assert any("Naan" in d for d in item_descs)

    assert data["subtotal"] == 1420.0
    assert data["tax"] == 142.0
    assert data["total"] == 1562.0

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


def test_receipt_messy_ocr():
    """Messy OCR: structure must be correct, but OCR typos preserved as-is."""
    doc = (TEST_DOCS_DIR / "receipt_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=RestaurantReceipt,
        tool_name="parse_receipt",
        tool_description="Parse an OCR-scanned restaurant receipt into structured data.",
    )

    data = result.data

    assert data["merchant_name"], "merchant_name missing"
    assert data["date"], "date missing"
    assert len(data["items"]) == 6
    assert data["subtotal"] == 1420.0
    assert data["total"] == 1562.0

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


if __name__ == "__main__":
    test_receipt_extraction()
    test_receipt_messy_ocr()
