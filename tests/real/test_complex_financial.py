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


@pytest.mark.real
def test_uk_balance_sheet_flexi(record_result):
    """Real OCR from UK Companies House — FLEXI BUSINESS LIMITED (company 06101470)."""
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
    assert data["current_assets"] is not None, "current_assets missing"
    assert data["creditors_amounts_falling_due_within_one_year"] is not None, (
        "creditors missing"
    )
    assert data["net_current_liabilities"] is not None, (
        "net_current_liabilities missing"
    )

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
    """Real OCR from scanned Indian annual report — Loyal Textile Mills Limited."""
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
        "PASSED Indian P&L loyal textile — attempts=%d time=%.2fs tokens=%d/%d revenue=%.0f",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
        data["revenue_from_operations"],
    )


@pytest.mark.real
def test_cas_statement_hdfc(record_result):
    """Real CAS statement text — CAMS format with 3 mutual fund folios."""
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
        assert (
            scheme["closing_units"] is not None or scheme["closing_value"] is not None
        ), f"scheme {scheme['scheme_name']} missing closing data"

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
