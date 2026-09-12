from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from app.domain.enums import FilingStatus
from app.pdfgen.filler import fill_form_1040
from app.taxcalc.engine import compute_return
from app.taxcalc.models import StructuredReturnInput


def test_schedule_a_not_attached_when_standard_deduction_wins():
    computed = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.HEAD_OF_HOUSEHOLD,
            wages=Decimal("52000"),
            itemized_deductions={"mortgage_interest": Decimal("14500"), "charitable_contributions": Decimal("3000")},
        )
    )
    assert computed.form_1040.deduction_is_itemized is False  # standard ($23,625) beats itemized ($17,500)

    pdf_bytes = fill_form_1040(computed, filing_status=FilingStatus.HEAD_OF_HOUSEHOLD)
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 2  # just the 1040, no Schedule A attached


def test_schedule_a_attached_when_itemizing_wins():
    computed = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("80000"),
            itemized_deductions={"mortgage_interest": Decimal("14000"), "charitable_contributions": Decimal("6000")},
        )
    )
    assert computed.form_1040.deduction_is_itemized is True

    pdf_bytes = fill_form_1040(computed, filing_status=FilingStatus.SINGLE)
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 3  # 1040 (2 pages) + Schedule A (1 page)
