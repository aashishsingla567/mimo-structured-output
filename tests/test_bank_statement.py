import logging
from pathlib import Path

from extraction import get_client, extract_structured, ExtractionConfig
from schemas.bank_statement import BankStatement

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"


def test_bank_statement_extraction():
    doc = (TEST_DOCS_DIR / "bank_statement_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=BankStatement,
        tool_name="parse_bank_statement",
        tool_description="Parse an OCR-scanned bank statement into structured data.",
    )

    data = result.data

    assert data["account_holder"], "account_holder missing"
    assert "AMITABH" in data["account_holder"].upper()
    assert "BACHCHAN" in data["account_holder"].upper()

    assert data["account_number"], "account_number missing"
    assert data["statement_period"], "statement_period missing"

    assert data["opening_balance"] == 125430.50
    assert data["closing_balance"] == 178894.25

    txns = data["transactions"]
    assert len(txns) == 8

    credits = [t for t in txns if t.get("credit")]
    debits = [t for t in txns if t.get("debit")]
    assert len(credits) >= 1
    assert len(debits) >= 5

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


def test_bank_statement_messy_ocr():
    """Messy OCR: 8 txns extracted, typos like 'Balanoe' preserved as-is."""
    doc = (TEST_DOCS_DIR / "bank_statement_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=BankStatement,
        tool_name="parse_bank_statement",
        tool_description="Parse an OCR-scanned bank statement into structured data.",
    )

    data = result.data

    assert data["account_holder"], "account_holder missing"
    assert data["account_number"], "account_number missing"
    assert data["opening_balance"] == 125430.50
    assert data["closing_balance"] == 178894.25

    txns = data["transactions"]
    assert len(txns) == 8

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


if __name__ == "__main__":
    test_bank_statement_extraction()
    test_bank_statement_messy_ocr()
