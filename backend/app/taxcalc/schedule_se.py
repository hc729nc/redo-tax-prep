from decimal import Decimal

from app.taxcalc.constants_2025 import (
    SE_MEDICARE_RATE,
    SE_NET_EARNINGS_MULTIPLIER,
    SE_SOCIAL_SECURITY_RATE,
    SOCIAL_SECURITY_WAGE_BASE,
)
from app.taxcalc.models import LineItem, ScheduleSEResult
from app.taxcalc.rounding import round_dollars


def compute_schedule_se(schedule_c_net_profit: Decimal) -> ScheduleSEResult | None:
    """Self-employment tax. Not required (and not filed) if net profit is zero or less."""
    if schedule_c_net_profit <= 0:
        return None

    net_earnings = round_dollars(schedule_c_net_profit * SE_NET_EARNINGS_MULTIPLIER)

    if net_earnings <= SOCIAL_SECURITY_WAGE_BASE:
        social_security_tax = net_earnings * SE_SOCIAL_SECURITY_RATE
    else:
        social_security_tax = SOCIAL_SECURITY_WAGE_BASE * SE_SOCIAL_SECURITY_RATE
    medicare_tax = net_earnings * SE_MEDICARE_RATE
    se_tax = round_dollars(social_security_tax + medicare_tax)
    half_se_tax_deduction = round_dollars(se_tax / 2)

    return ScheduleSEResult(
        net_earnings_from_se=net_earnings,
        se_tax=se_tax,
        half_se_tax_deduction=half_se_tax_deduction,
        line_items=[
            LineItem(line_ref="schedule_se.3", label="Net profit from Schedule C", value=schedule_c_net_profit),
            LineItem(line_ref="schedule_se.6", label="Net earnings from self-employment", value=net_earnings),
            LineItem(line_ref="schedule_se.12", label="Self-employment tax", value=se_tax),
            LineItem(
                line_ref="schedule_se.13",
                label="Deduction for one-half of self-employment tax",
                value=half_se_tax_deduction,
            ),
        ],
    )
