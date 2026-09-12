from decimal import Decimal

from app.taxcalc.constants_2025 import SCHEDULE_B_THRESHOLD
from app.taxcalc.models import LineItem, ScheduleBResult


def compute_schedule_b(total_taxable_interest: Decimal, total_ordinary_dividends: Decimal) -> ScheduleBResult:
    required = (
        total_taxable_interest > SCHEDULE_B_THRESHOLD
        or total_ordinary_dividends > SCHEDULE_B_THRESHOLD
    )
    return ScheduleBResult(
        total_taxable_interest=total_taxable_interest,
        total_ordinary_dividends=total_ordinary_dividends,
        required=required,
        line_items=[
            LineItem(line_ref="schedule_b.2", label="Total taxable interest", value=total_taxable_interest),
            LineItem(line_ref="schedule_b.6", label="Total ordinary dividends", value=total_ordinary_dividends),
        ],
    )
