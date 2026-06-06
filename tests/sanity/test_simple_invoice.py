import logging

import pytest

from extraction import extract_structured, get_client
from schemas.simple_invoice import InvoiceSummary
from tests.conftest import TEST_DOCS_SANITY

log = logging.getLogger(__name__)


@pytest.mark.sanity
def test_simple_invoice_extraction(record_result):
    doc = (TEST_DOCS_SANITY / "simple_invoice.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=InvoiceSummary,
        tool_name="emit_invoice",
        tool_description="Return exactly one Invoice object.",
    )

    record, _ = record_result
    record(result)
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
