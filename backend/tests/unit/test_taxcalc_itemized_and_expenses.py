"""Single filer, W-2 wages, with Schedule C expenses and itemized deductions.

Scenario 1 - Schedule C expenses reduce net profit:
  $40,000 gross receipts - $10,000 expenses = $30,000 net profit (vs. $35,000 in the
  no-expenses test elsewhere) - just confirms total_expenses actually flows through.

Scenario 2 - itemizing only wins when it beats the standard deduction:
  Single filer, standard deduction is $15,750. $20,000 in itemized (mortgage interest
  + charitable) should be used instead of standard. $10,000 itemized should NOT be
  used (standard deduction of $15,750 is larger).
"""

from decimal import Decimal

from app.domain.enums import FilingStatus
from app.taxcalc.engine import compute_return
from app.taxcalc.models import StructuredReturnInput


def test_schedule_c_expenses_reduce_net_profit():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            self_employment_gross_receipts=Decimal("40000"),
            self_employment_expenses=Decimal("10000"),
        )
    )
    assert result.schedule_c.net_profit == Decimal("30000")


def test_itemized_deductions_used_when_larger_than_standard():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("80000"),
            itemized_deductions={
                "mortgage_interest": Decimal("14000"),
                "charitable_contributions": Decimal("6000"),
            },
        )
    )
    assert result.schedule_a is not None
    assert result.schedule_a.total_itemized_deductions == Decimal("20000")
    assert result.form_1040.deduction_is_itemized is True
    assert result.form_1040.deduction_amount == Decimal("20000")


def test_standard_deduction_used_when_itemized_is_smaller():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("80000"),
            itemized_deductions={"mortgage_interest": Decimal("10000")},
        )
    )
    assert result.form_1040.deduction_is_itemized is False
    assert result.form_1040.deduction_amount == Decimal("15750")
