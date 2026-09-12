from decimal import Decimal

from app.taxcalc.models import LineItem, ScheduleAResult


def compute_schedule_a(itemized_items: dict[str, Decimal]) -> ScheduleAResult:
    total = sum(itemized_items.values(), Decimal("0"))
    line_items = [
        LineItem(line_ref=f"schedule_a.{name}", label=name, value=value)
        for name, value in itemized_items.items()
    ]
    line_items.append(LineItem(line_ref="schedule_a.17", label="Total itemized deductions", value=total))
    return ScheduleAResult(total_itemized_deductions=total, line_items=line_items)
