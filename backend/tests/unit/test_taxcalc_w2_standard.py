"""Single filer, one W-2, standard deduction. Hand-computed expected values:

AGI = wages = $52,000 (no adjustments)
Standard deduction (single, 2025) = $15,750
Taxable income = 52,000 - 15,750 = $36,250
Tax: 10% x $11,925 = $1,192.50
     12% x (36,250 - 11,925) = 12% x $24,325 = $2,919.00
     total = $4,111.50 -> rounds to $4,112
Total tax = $4,112 (no SE tax)
Withholding = $6,100 -> refund = 6,100 - 4,112 = $1,988
"""

from decimal import Decimal

from app.domain.enums import FilingStatus
from app.taxcalc.engine import compute_return
from app.taxcalc.models import StructuredReturnInput


def test_w2_only_standard_deduction():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("52000"),
            federal_withholding_w2=Decimal("6100"),
        )
    )

    assert result.form_1040.agi == Decimal("52000")
    assert result.form_1040.deduction_amount == Decimal("15750")
    assert result.form_1040.deduction_is_itemized is False
    assert result.form_1040.taxable_income == Decimal("36250")
    assert result.form_1040.tax_before_credits == Decimal("4112")
    assert result.form_1040.total_tax == Decimal("4112")
    assert result.form_1040.refund_amount == Decimal("1988")
    assert result.form_1040.amount_owed == Decimal("0")
    assert result.schedule_se is None
    assert result.schedule_b is None
