from pathlib import Path

import pytest

from tests.integration.conftest import requires_api_key

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _upload(client, return_id, fixture_name):
    with open(FIXTURES_DIR / fixture_name, "rb") as f:
        resp = client.post(
            f"/api/documents/upload?tax_return_id={return_id}",
            files={"file": (fixture_name, f, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    return resp.json()


@requires_api_key
def test_w2_upload_extracts_wages_and_withholding_with_provenance(client, return_id):
    doc = _upload(client, return_id, "sample_w2_textlayer.pdf")
    assert doc["document_type"] == "w2"
    assert doc["extraction_status"] == "extracted"

    fields = client.get(f"/api/documents/fields?tax_return_id={return_id}").json()
    by_name = {f["field_name"]: f for f in fields}

    assert by_name["w2.box1_wages"]["value"] == "52000.00"
    assert by_name["w2.box1_wages"]["source_page"] == 1
    assert "52000" in by_name["w2.box1_wages"]["source_text_snippet"]

    assert by_name["w2.box2_federal_withholding"]["value"] == "6100.00"


@requires_api_key
@pytest.mark.parametrize(
    "fixture_name,doc_type,field_name,expected_value",
    [
        ("sample_1099_int.pdf", "1099_int", "1099_int.box1_interest", "1850.00"),
        ("sample_1099_div.pdf", "1099_div", "1099_div.box1a_ordinary_dividends", "920.00"),
        ("sample_1099_nec.pdf", "1099_nec", "1099_nec.box1_nonemployee_compensation", "15000.00"),
        ("sample_1098_mortgage.pdf", "1098", "schedule_a.mortgage_interest", "14500.00"),
    ],
)
def test_each_1099_and_1098_variant_extracts_correctly(
    client, return_id, fixture_name, doc_type, field_name, expected_value
):
    doc = _upload(client, return_id, fixture_name)
    assert doc["document_type"] == doc_type

    fields = client.get(f"/api/documents/fields?tax_return_id={return_id}").json()
    by_name = {f["field_name"]: f for f in fields}
    assert by_name[field_name]["value"] == expected_value


@requires_api_key
def test_1099_b_extracts_both_short_and_long_term_aggregate_totals(client, return_id):
    doc = _upload(client, return_id, "sample_1099_b.pdf")
    assert doc["document_type"] == "1099_b"

    fields = client.get(f"/api/documents/fields?tax_return_id={return_id}").json()
    by_name = {f["field_name"]: f["value"] for f in fields}

    assert by_name["1099_b.net_short_term_gain_loss"] == "-3000.00"
    assert by_name["1099_b.net_long_term_gain_loss"] == "8000.00"


@requires_api_key
def test_prior_year_1040_extracts_all_summary_lines(client, return_id):
    with open(FIXTURES_DIR / "sample_prior_year_1040.pdf", "rb") as f:
        resp = client.post(
            f"/api/prior-year/upload?current_return_id={return_id}",
            files={"file": ("sample_prior_year_1040.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    prior_return_id = resp.json()["tax_return_id"]

    fields = client.get(f"/api/documents/fields?tax_return_id={prior_return_id}").json()
    by_name = {f["field_name"]: f["value"] for f in fields}

    assert by_name["prior_year.wages"] == "58000"
    assert by_name["prior_year.agi"] == "58800"
    assert by_name["prior_year.total_tax"] == "4989"


def test_no_text_layer_pdf_fails_extraction_cleanly_instead_of_crashing(client, return_id):
    """A scanned/image-only PDF has no text for pypdf to read (it does no OCR) -
    this must surface as a clean status, not a crash, and must NOT call Claude
    (so this test runs even without an API key)."""
    doc = _upload(client, return_id, "sample_scanned_no_text.pdf")

    assert doc["extraction_status"] == "extraction_failed_no_text_layer"

    fields = client.get(f"/api/documents/fields?tax_return_id={return_id}").json()
    assert fields == []
