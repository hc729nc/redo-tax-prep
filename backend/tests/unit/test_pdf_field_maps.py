from pypdf import PdfReader

from app.pdfgen.field_maps import (
    FILING_STATUS_CHECKBOX_FIELDS,
    FORM_1040_FIELD_MAP,
    FORM_1040_NAME_SSN_FIELDS,
    SCHEDULE_A_FIELD_MAP,
    SCHEDULE_B_FIELD_MAP,
    SCHEDULE_C_FIELD_MAP,
    SCHEDULE_SE_FIELD_MAP,
)
from app.pdfgen.filler import IRS_FORMS_DIR

FORMS_AND_MAPS = [
    ("f1040.pdf", {**FORM_1040_FIELD_MAP, **FORM_1040_NAME_SSN_FIELDS}),
    ("f1040sa.pdf", SCHEDULE_A_FIELD_MAP),
    ("f1040sb.pdf", SCHEDULE_B_FIELD_MAP),
    ("f1040sc.pdf", SCHEDULE_C_FIELD_MAP),
    ("f1040sse.pdf", SCHEDULE_SE_FIELD_MAP),
]


def test_all_mapped_fields_exist_in_blank_templates():
    """Catches silent drift if the IRS revises one of these forms' AcroForm field names."""
    for form_filename, field_map in FORMS_AND_MAPS:
        reader = PdfReader(IRS_FORMS_DIR / form_filename)
        actual_fields = reader.get_fields()

        for line_ref, field_name in field_map.items():
            assert field_name in actual_fields, (
                f"{form_filename}: line {line_ref} field {field_name!r} not found in template"
            )


def test_filing_status_checkbox_fields_exist_with_matching_export_value():
    reader = PdfReader(IRS_FORMS_DIR / "f1040.pdf")
    actual_fields = reader.get_fields()

    for status, (field_name, on_value) in FILING_STATUS_CHECKBOX_FIELDS.items():
        assert field_name in actual_fields, f"filing status {status}: field {field_name!r} not found"
        states = actual_fields[field_name].get("/_States_")
        assert on_value in states, (
            f"filing status {status}: on-value {on_value!r} not in field's states {states!r}"
        )
