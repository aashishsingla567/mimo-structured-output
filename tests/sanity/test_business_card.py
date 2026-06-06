from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.business_card import BusinessCard
from tests.conftest import TEST_DOCS_SANITY
import logging

log = logging.getLogger(__name__)


@pytest.mark.sanity
def test_business_card_extraction(record_result):
    doc = (TEST_DOCS_SANITY / "business_card_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=BusinessCard,
        tool_name="parse_business_card",
        tool_description="Parse an OCR-scanned business card into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["name"], "name missing"
    assert "Rajesh" in data["name"] or "RAJESH" in data["name"]

    assert data["company"], "company missing"
    assert "Infosys" in data["company"] or "infosys" in data["company"].lower()

    assert data["email"], "email missing"
    assert "@" in data["email"]

    assert data["phone"], "phone missing"

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
def test_business_card_messy_ocr(record_result):
    """Messy OCR: structure correct, typos like 'shama' instead of 'sharma' preserved."""
    doc = (TEST_DOCS_SANITY / "business_card_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=BusinessCard,
        tool_name="parse_business_card",
        tool_description="Parse an OCR-scanned business card into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["name"], "name missing"
    assert data["company"], "company missing"
    assert data["email"], "email missing"
    assert "@" in data["email"]

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )
