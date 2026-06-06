import logging
from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.uk_balance_sheet import UKBalanceSheet
from schemas.indian_pnl import IndianPnL
from schemas.cas_statement import CASStatement

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent.parent / "test_documents" / "real"

# Ground truth from README in ap539813/Financial-data-extraction-from-ocr-images
# Company 06101470 — FLEXI BUSINESS SOLUTIONS LIMITED
# Source: https://github.com/ap539813/Financial-data-extraction-from-ocr-images/blob/master/README.md
UK_BS_GROUND_TRUTH = {
    "current_assets": 51700,
    "creditors_amounts_falling_due_within_one_year": -55505,
    "net_current_liabilities": -3805,
    "total_assets_less_current_liabilities": -3805,
    "accruals_and_deferred_income": -500,
    "net_liabilities": -4305,
    "capital_and_reserves": -4305,
}


@pytest.mark.real
def test_uk_balance_sheet_flexi(record_result):
    """Real OCR from UK Companies House — FLEXI BUSINESS SOLUTIONS LIMITED (company 06101470).
    Raw text: Sample Dataset/sample1_0000001R.txt from ap539813/Financial-data-extraction-from-ocr-images
    Ground truth: Expected Output section in the same repo's README.md"""
    doc = (TEST_DOCS_DIR / "uk_balance_sheet_1.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=UKBalanceSheet,
        tool_name="parse_uk_balance_sheet",
        tool_description="Parse a UK balance sheet from OCR text.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["company_name"], "company_name missing"

    for field, expected in UK_BS_GROUND_TRUTH.items():
        actual = data.get(field)
        assert actual is not None, f"{field} is None, expected {expected}"
        assert actual == expected, f"{field}: got {actual}, expected {expected}"

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED UK balance sheet flexi — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


@pytest.mark.real
def test_indian_pnl_loyal_textile(record_result):
    """Real OCR from scanned Indian annual report — Loyal Textile Mills Limited.
    Source: https://loyaltextiles.com/wp-content/uploads/2025/05/BMOutcomeQ4Financial-Results.pdf
    Note: PDF is image-based. Raw text reconstructed from search snippets, not a direct copy.
    No published ground truth JSON exists. Structural assertions only."""
    doc = (TEST_DOCS_DIR / "indian_pnl_loyal_textile.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=IndianPnL,
        tool_name="parse_indian_pnl",
        tool_description="Parse an Indian profit and loss statement from OCR text.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["company_name"], "company_name missing"
    assert data["revenue_from_operations"] is not None, "revenue missing"
    assert data["total_income"] is not None, "total_income missing"
    assert data["total_expenses"] is not None, "total_expenses missing"
    assert data["profit_before_tax"] is not None, "profit_before_tax missing"

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED Indian P&L loyal textile — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )


@pytest.mark.real
def test_cas_statement_hdfc(record_result):
    """CAS statement text — CAMS format with 3 mutual fund folios.
    Source: Scribd document 989793884/Cas (search snippets only, paywall blocks full text).
    No published ground truth JSON exists. Structural assertions only."""
    doc = (TEST_DOCS_DIR / "cas_statement_hdfc.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=CASStatement,
        tool_name="parse_cas_statement",
        tool_description="Parse a CAMS Consolidated Account Statement from text.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["schemes"], "schemes list missing"
    assert len(data["schemes"]) >= 2, (
        f"expected >=2 schemes, got {len(data['schemes'])}"
    )
    assert data["total_portfolio_value"] is not None, "total_portfolio_value missing"

    for scheme in data["schemes"]:
        assert scheme["scheme_name"], "scheme_name missing"

    assert result.attempts <= 3
    assert result.input_tokens > 0

    log.info(
        "PASSED CAS statement HDFC — attempts=%d time=%.2fs tokens=%d/%d schemes=%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
        len(data["schemes"]),
    )
