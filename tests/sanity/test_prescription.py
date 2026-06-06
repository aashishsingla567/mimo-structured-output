import logging
from pathlib import Path

import pytest

from extraction import get_client, extract_structured
from schemas.prescription import Prescription

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TEST_DOCS_DIR = Path(__file__).parent.parent.parent / "test_documents" / "sanity"


@pytest.mark.sanity
def test_prescription_extraction(record_result):
    doc = (TEST_DOCS_DIR / "prescription_ocr.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=Prescription,
        tool_name="parse_prescription",
        tool_description="Parse an OCR-scanned medical prescription into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["patient_name"], "patient_name missing"
    assert "Suresh" in data["patient_name"] or "Patel" in data["patient_name"]

    assert data["doctor_name"], "doctor_name missing"
    assert "Priya" in data["doctor_name"] or "Menon" in data["doctor_name"]

    assert data["date"], "date missing"

    meds = data["medications"]
    assert len(meds) == 4

    med_names = [m["name"].lower() for m in meds]
    assert any("metformin" in n for n in med_names)
    assert any("amlodipine" in n for n in med_names)
    assert any("omeprazole" in n for n in med_names)

    for m in meds:
        assert m["dosage"], f"dosage missing for {m['name']}"
        assert m["frequency"], f"frequency missing for {m['name']}"

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
def test_prescription_messy_ocr(record_result):
    """Messy OCR: 4 meds must be extracted, typos like 'Omeprazloe' preserved."""
    doc = (TEST_DOCS_DIR / "prescription_ocr_messy.txt").read_text()
    client = get_client()

    result = extract_structured(
        client=client,
        document=doc,
        schema=Prescription,
        tool_name="parse_prescription",
        tool_description="Parse an OCR-scanned medical prescription into structured data.",
    )

    record, _ = record_result
    record(result)
    data = result.data

    assert data["patient_name"], "patient_name missing"
    assert data["doctor_name"], "doctor_name missing"
    assert data["date"], "date missing"

    meds = data["medications"]
    assert len(meds) == 4

    for m in meds:
        assert m["name"], "medication name missing"
        assert m["dosage"], f"dosage missing for {m['name']}"
        assert m["frequency"], f"frequency missing for {m['name']}"

    log.info(
        "PASSED messy OCR — attempts=%d time=%.2fs tokens=%d/%d",
        result.attempts,
        result.elapsed,
        result.input_tokens,
        result.output_tokens,
    )
