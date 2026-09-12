from decimal import Decimal

from app.taxcalc.models import LineItem, ScheduleCResult
from app.taxcalc.rounding import round_dollars


def compute_schedule_c(gross_receipts: Decimal, total_expenses: Decimal) -> ScheduleCResult:
    net_profit = round_dollars(gross_receipts - total_expenses)
    return ScheduleCResult(
        gross_receipts=gross_receipts,
        total_expenses=total_expenses,
        net_profit=net_profit,
        line_items=[
            LineItem(line_ref="schedule_c.1", label="Gross receipts", value=gross_receipts),
            LineItem(line_ref="schedule_c.28", label="Total expenses", value=total_expenses),
            LineItem(line_ref="schedule_c.31", label="Net profit or (loss)", value=net_profit),
        ],
    )
