"""Single filer, self-employment only via 1099-NEC. Hand-computed expected values:

Schedule C: gross receipts $40,000 - expenses $5,000 = net profit $35,000
Schedule SE: net earnings = 35,000 x 0.9235 = 32,322.50 -> rounds to $32,323
             SS tax = 32,323 x 12.4% = $4,008.052
             Medicare tax = 32,323 x 2.9% = $937.367
             SE tax = 4,008.052 + 937.367 = 4,945.419 -> rounds to $4,945
             Half-SE-tax deduction = 4,945 / 2 = 2,472.50 -> rounds to $2,473
Form 1040: AGI = 35,000 - 2,473 = $32,527
           Taxable income = 32,527 - 15,750 (standard deduction) = $16,777
           Income tax: 10% x 11,925 = 1,192.50; 12% x (16,777-11,925) = 12% x 4,852 = 582.24
                       total = 1,774.74 -> rounds to $1,775
           Total tax = 1,775 + 4,945 (SE tax) = $6,720
No withholding -> amount owed = $6,720
"""

from decimal import Decimal

from app.domain.enums import FilingStatus
from app.taxcalc.engine import compute_return
from app.taxcalc.models import StructuredReturnInput


def test_self_employment_schedule_c_and_se():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            self_employment_gross_receipts=Decimal("40000"),
            self_employment_expenses=Decimal("5000"),
        )
    )

    assert result.schedule_c is not None
    assert result.schedule_c.net_profit == Decimal("35000")

    assert result.schedule_se is not None
    assert result.schedule_se.net_earnings_from_se == Decimal("32323")
    assert result.schedule_se.se_tax == Decimal("4945")
    assert result.schedule_se.half_se_tax_deduction == Decimal("2473")

    assert result.form_1040.agi == Decimal("32527")
    assert result.form_1040.taxable_income == Decimal("16777")
    assert result.form_1040.tax_before_credits == Decimal("1775")
    assert result.form_1040.total_tax == Decimal("6720")
    assert result.form_1040.amount_owed == Decimal("6720")
    assert result.form_1040.refund_amount == Decimal("0")


def test_self_employment_loss_skips_schedule_se():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            self_employment_gross_receipts=Decimal("1000"),
            self_employment_expenses=Decimal("5000"),
        )
    )

    assert result.schedule_c.net_profit == Decimal("-4000")
    assert result.schedule_se is None
