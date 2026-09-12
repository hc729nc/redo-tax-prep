from decimal import Decimal
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.domain.enums import FilingStatus
from app.pdfgen.field_maps import (
    FILING_STATUS_CHECKBOX_FIELDS,
    FORM_1040_FIELD_MAP,
    FORM_1040_NAME_SSN_FIELDS,
    SCHEDULE_A_FIELD_MAP,
    SCHEDULE_B_FIELD_MAP,
    SCHEDULE_C_FIELD_MAP,
    SCHEDULE_D_FIELD_MAP,
    SCHEDULE_SE_FIELD_MAP,
)
from app.taxcalc.models import ComputedReturn

IRS_FORMS_DIR = Path(__file__).parent / "irs_forms"


def _format_dollar(value: Decimal) -> str:
    return f"{value:,.0f}"


def _format_ssn(ssn: str) -> str:
    return "".join(ch for ch in ssn if ch.isdigit())[:9]


def _append_and_fill(
    writer: PdfWriter, form_filename: str, page_fields: dict[int, dict[str, str]]
) -> None:
    """Append every page of `form_filename` to `writer`, then fill the given fields
    on each page (page_fields keyed by 0-indexed page number within that form)."""
    reader = PdfReader(IRS_FORMS_DIR / form_filename)
    start_page = len(writer.pages)
    writer.append(reader)

    for local_page_index, fields in page_fields.items():
        if not fields:
            continue
        writer.update_page_form_field_values(
            writer.pages[start_page + local_page_index], fields, auto_regenerate=False
        )


def fill_form_1040(
    computed_return: ComputedReturn,
    *,
    filing_status: FilingStatus,
    first_name_and_mi: str = "",
    last_name: str = "",
    ssn: str = "",
) -> bytes:
    """Fill the official IRS Form 1040 AcroForm fields from a ComputedReturn, plus
    any supporting schedules (A/B/C/SE) the return actually needs, and return the
    combined PDF as bytes."""
    writer = PdfWriter()

    line_values = {item.line_ref: item.value for item in computed_return.form_1040.line_items}
    # Line 11 (AGI) appears on both page 1 (as 11a) and page 2 (as 11b, restated).
    agi = line_values.get("11", Decimal("0"))

    page1_fields = {
        FORM_1040_NAME_SSN_FIELDS["first_name_and_mi"]: first_name_and_mi,
        FORM_1040_NAME_SSN_FIELDS["last_name"]: last_name,
        FORM_1040_NAME_SSN_FIELDS["ssn"]: _format_ssn(ssn),
    }
    checkbox = FILING_STATUS_CHECKBOX_FIELDS.get(filing_status.value)
    if checkbox is not None:
        field_name, on_value = checkbox
        page1_fields[field_name] = on_value

    page2_fields = {FORM_1040_FIELD_MAP["11b"]: _format_dollar(agi)}

    for line_ref, field_name in FORM_1040_FIELD_MAP.items():
        if line_ref == "11b":
            continue
        value = line_values.get(line_ref)
        if value is None:
            continue
        target = page1_fields if ".Page1[0]." in field_name else page2_fields
        target[field_name] = _format_dollar(value)

    _append_and_fill(writer, "f1040.pdf", {0: page1_fields, 1: page2_fields})

    # Only attach Schedule A if itemizing actually won - a real return wouldn't
    # include it just because the user reported itemized amounts that turned out
    # smaller than the standard deduction.
    if computed_return.schedule_a is not None and computed_return.form_1040.deduction_is_itemized:
        a = computed_return.schedule_a
        itemized_by_category = {
            item.line_ref.removeprefix("schedule_a."): item.value for item in a.line_items
        }
        mortgage_interest = itemized_by_category.get("mortgage_interest", Decimal("0"))
        charitable_contributions = itemized_by_category.get("charitable_contributions", Decimal("0"))
        fields = {
            SCHEDULE_A_FIELD_MAP["8e"]: _format_dollar(mortgage_interest),
            SCHEDULE_A_FIELD_MAP["10"]: _format_dollar(mortgage_interest),
            SCHEDULE_A_FIELD_MAP["11"]: _format_dollar(charitable_contributions),
            SCHEDULE_A_FIELD_MAP["14"]: _format_dollar(charitable_contributions),
            SCHEDULE_A_FIELD_MAP["17"]: _format_dollar(a.total_itemized_deductions),
        }
        _append_and_fill(writer, "f1040sa.pdf", {0: fields})

    if computed_return.schedule_b is not None:
        b = computed_return.schedule_b
        fields = {
            SCHEDULE_B_FIELD_MAP["2"]: _format_dollar(b.total_taxable_interest),
            SCHEDULE_B_FIELD_MAP["4"]: _format_dollar(b.total_taxable_interest),
            SCHEDULE_B_FIELD_MAP["6"]: _format_dollar(b.total_ordinary_dividends),
        }
        _append_and_fill(writer, "f1040sb.pdf", {0: fields})

    if computed_return.schedule_d is not None:
        d = computed_return.schedule_d
        schedule_d_page1_fields = {
            SCHEDULE_D_FIELD_MAP["7"]: _format_dollar(d.net_short_term_gain),
            SCHEDULE_D_FIELD_MAP["15"]: _format_dollar(d.net_long_term_gain),
        }
        schedule_d_page2_fields = {SCHEDULE_D_FIELD_MAP["16"]: _format_dollar(d.total_capital_gain)}
        _append_and_fill(writer, "f1040sd.pdf", {0: schedule_d_page1_fields, 1: schedule_d_page2_fields})

    if computed_return.schedule_c is not None:
        c = computed_return.schedule_c
        fields = {
            SCHEDULE_C_FIELD_MAP["1"]: _format_dollar(c.gross_receipts),
            SCHEDULE_C_FIELD_MAP["28"]: _format_dollar(c.total_expenses),
            SCHEDULE_C_FIELD_MAP["31"]: _format_dollar(c.net_profit),
        }
        _append_and_fill(writer, "f1040sc.pdf", {0: fields})

    if computed_return.schedule_se is not None:
        se = computed_return.schedule_se
        net_profit = computed_return.schedule_c.net_profit if computed_return.schedule_c else Decimal("0")
        fields = {
            SCHEDULE_SE_FIELD_MAP["2"]: _format_dollar(net_profit),
            SCHEDULE_SE_FIELD_MAP["3"]: _format_dollar(net_profit),
            SCHEDULE_SE_FIELD_MAP["4a"]: _format_dollar(se.net_earnings_from_se),
            SCHEDULE_SE_FIELD_MAP["4c"]: _format_dollar(se.net_earnings_from_se),
            SCHEDULE_SE_FIELD_MAP["6"]: _format_dollar(se.net_earnings_from_se),
            SCHEDULE_SE_FIELD_MAP["12"]: _format_dollar(se.se_tax),
            SCHEDULE_SE_FIELD_MAP["13"]: _format_dollar(se.half_se_tax_deduction),
        }
        _append_and_fill(writer, "f1040sse.pdf", {0: fields})

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
