"""Capital gains (Schedule D, aggregate-totals-only - no Form 8949 detail).

Hand-computed expected values for the preferential-rate stacking test:

Single filer, wages $55,750, long-term capital gain $20,000, standard deduction.
  AGI = 55,750 + 20,000 = $75,750
  Taxable income = 75,750 - 15,750 (standard deduction) = $60,000
  LTCG eligible for preferential rate = $20,000 (all of it, since no ST loss to net against)
  Ordinary portion = 60,000 - 20,000 = $40,000
  Tax on ordinary $40,000 (single): 10% x 11,925 = 1,192.50; 12% x (40,000-11,925) = 12% x 28,075
                                     = 3,369.00; total = 4,561.50 -> rounds to $4,562
  LTCG stacking: 0% bracket ceiling for single = $48,350. Ordinary income already fills
                 $40,000 of that, leaving $8,350 of room at 0% before hitting the 15% bracket.
                 0% portion = min(20,000, 48,350-40,000) = $8,350 -> $0 tax
                 Remaining $11,650 falls in the 15% bracket (48,350 to 533,400)
                 15% portion tax = 11,650 x 0.15 = $1,747.50
  Total tax = 4,562 + 1,747.50 = 6,309.50 -> rounds to $6,310
"""

from decimal import Decimal

from app.domain.enums import FilingStatus
from app.taxcalc.engine import compute_return
from app.taxcalc.models import StructuredReturnInput
from app.taxcalc.schedule_d import compute_schedule_d


def test_short_term_loss_nets_against_long_term_gain():
    result = compute_schedule_d(short_term_gain=Decimal("-5000"), long_term_gain=Decimal("8000"))
    assert result.total_capital_gain == Decimal("3000")
    # Only $3,000 of net gain exists overall, so only $3,000 (not the full $8,000
    # long-term gain) is eligible for the preferential rate.
    assert result.gain_eligible_for_preferential_rate == Decimal("3000")


def test_net_capital_loss_capped_at_annual_limit():
    result = compute_schedule_d(short_term_gain=Decimal("-10000"), long_term_gain=Decimal("2000"))
    assert result.total_capital_gain == Decimal("-3000")  # capped, not -8,000
    assert result.gain_eligible_for_preferential_rate == Decimal("0")


def test_long_term_gain_gets_preferential_rate_stacking():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("55750"),
            long_term_capital_gain=Decimal("20000"),
        )
    )
    assert result.form_1040.agi == Decimal("75750")
    assert result.form_1040.taxable_income == Decimal("60000")
    assert result.form_1040.tax_before_credits == Decimal("6310")


def test_short_term_gain_taxed_as_ordinary_income_no_preferential_rate():
    result = compute_return(
        StructuredReturnInput(
            filing_status=FilingStatus.SINGLE,
            wages=Decimal("40000"),
            short_term_capital_gain=Decimal("20000"),
        )
    )
    assert result.form_1040.taxable_income == Decimal("44250")
    # 10% x 11,925 + 12% x 32,325 = 1,192.50 + 3,879.00 = 5,071.50 -> rounds to 5,072
    assert result.form_1040.tax_before_credits == Decimal("5072")
