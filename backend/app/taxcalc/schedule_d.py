from decimal import Decimal

from app.taxcalc.constants_2025 import CAPITAL_LOSS_ANNUAL_LIMIT
from app.taxcalc.models import LineItem, ScheduleDResult

ZERO = Decimal("0")


def compute_schedule_d(short_term_gain: Decimal, long_term_gain: Decimal) -> ScheduleDResult:
    """Aggregate-totals-only Schedule D (no Form 8949 transaction detail - see
    docs/mvp-scope.md). Net short-term and long-term figures are each assumed to
    already be netted across all transactions of that holding period.

    gain_eligible_for_preferential_rate follows the real Schedule D Tax Worksheet
    rule: long-term gain only gets the preferential rate up to the overall net gain
    (so a short-term loss that partly offsets a long-term gain correctly reduces
    how much of it qualifies for the lower rate)."""
    combined = short_term_gain + long_term_gain
    total_capital_gain = max(combined, -CAPITAL_LOSS_ANNUAL_LIMIT)

    if long_term_gain <= ZERO or total_capital_gain <= ZERO:
        eligible = ZERO
    else:
        eligible = min(long_term_gain, total_capital_gain)

    return ScheduleDResult(
        net_short_term_gain=short_term_gain,
        net_long_term_gain=long_term_gain,
        total_capital_gain=total_capital_gain,
        gain_eligible_for_preferential_rate=eligible,
        line_items=[
            LineItem(line_ref="schedule_d.7", label="Net short-term capital gain or (loss)", value=short_term_gain),
            LineItem(line_ref="schedule_d.15", label="Net long-term capital gain or (loss)", value=long_term_gain),
            LineItem(line_ref="schedule_d.16", label="Total capital gain or (loss)", value=total_capital_gain),
        ],
    )
