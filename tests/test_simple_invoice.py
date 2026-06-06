import logging
from pathlib import Path

from extraction import get_client, extract_structured
from schemas.simple_invoice import InvoiceSummary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"


def test_simple_invoice_extraction():
    doc = (TEST_DOCS_DIR / "simple_invoice.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=InvoiceSummary,
        tool_name="emit_invoice",
        tool_description="Return exactly one Invoice object.",
    )

    data = result.data

    assert data["invoice_id"] == "INV-1024"
    assert data["total"] == 149.50
    assert data["currency"] == "INR"
    assert data["status"] == "paid"

    assert result.attempts == 1
    assert result.input_tokens > 0
    assert result.output_tokens > 0

    log.info(
        "PASSED — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


if __name__ == "__main__":
    test_simple_invoice_extraction()
