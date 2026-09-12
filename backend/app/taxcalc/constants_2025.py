"""Tax year 2025 constants.

Standard deduction amounts confirmed directly from the text of the official IRS
f1040.pdf (2025 revision) - the 2025 One Big Beautiful Bill Act raised these above
the normal inflation-only adjustment, so they must not be assumed from prior years.
Bracket thresholds and the Social Security wage base confirmed via Tax Foundation /
SSA for 2025 (OBBBA kept TCJA rates/thresholds on the standard inflation schedule).
"""

from decimal import Decimal

from app.domain.enums import FilingStatus

STANDARD_DEDUCTION: dict[FilingStatus, Decimal] = {
    FilingStatus.SINGLE: Decimal("15750"),
    FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("15750"),
    FilingStatus.MARRIED_FILING_JOINTLY: Decimal("31500"),
    FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("23625"),
}

# Each bracket: (upper bound of the bracket, rate). The last bracket's upper bound
# is None, meaning unbounded.
TaxBracket = tuple[Decimal | None, Decimal]

TAX_BRACKETS: dict[FilingStatus, list[TaxBracket]] = {
    FilingStatus.SINGLE: [
        (Decimal("11925"), Decimal("0.10")),
        (Decimal("48475"), Decimal("0.12")),
        (Decimal("103350"), Decimal("0.22")),
        (Decimal("197300"), Decimal("0.24")),
        (Decimal("250525"), Decimal("0.32")),
        (Decimal("626350"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.MARRIED_FILING_JOINTLY: [
        (Decimal("23850"), Decimal("0.10")),
        (Decimal("96950"), Decimal("0.12")),
        (Decimal("206700"), Decimal("0.22")),
        (Decimal("394600"), Decimal("0.24")),
        (Decimal("501050"), Decimal("0.32")),
        (Decimal("751600"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.MARRIED_FILING_SEPARATELY: [
        (Decimal("11925"), Decimal("0.10")),
        (Decimal("48475"), Decimal("0.12")),
        (Decimal("103350"), Decimal("0.22")),
        (Decimal("197300"), Decimal("0.24")),
        (Decimal("250525"), Decimal("0.32")),
        (Decimal("375800"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (Decimal("17000"), Decimal("0.10")),
        (Decimal("64850"), Decimal("0.12")),
        (Decimal("103350"), Decimal("0.22")),
        (Decimal("197300"), Decimal("0.24")),
        (Decimal("250500"), Decimal("0.32")),
        (Decimal("626350"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
}

SCHEDULE_B_THRESHOLD = Decimal("1500")

SE_TAX_RATE = Decimal("0.153")  # 12.4% Social Security + 2.9% Medicare
SE_SOCIAL_SECURITY_RATE = Decimal("0.124")
SE_MEDICARE_RATE = Decimal("0.029")
SE_NET_EARNINGS_MULTIPLIER = Decimal("0.9235")
SOCIAL_SECURITY_WAGE_BASE = Decimal("176100")
