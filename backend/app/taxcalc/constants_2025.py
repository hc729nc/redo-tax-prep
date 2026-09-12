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

# Long-term capital gains preferential rate thresholds, confirmed via Tax
# Foundation / NerdWallet for 2025 (cross-checked across both sources).
LongTermCapitalGainsBracket = tuple[Decimal | None, Decimal]

LTCG_BRACKETS: dict[FilingStatus, list[LongTermCapitalGainsBracket]] = {
    FilingStatus.SINGLE: [
        (Decimal("48350"), Decimal("0.00")),
        (Decimal("533400"), Decimal("0.15")),
        (None, Decimal("0.20")),
    ],
    FilingStatus.MARRIED_FILING_JOINTLY: [
        (Decimal("96700"), Decimal("0.00")),
        (Decimal("600050"), Decimal("0.15")),
        (None, Decimal("0.20")),
    ],
    FilingStatus.MARRIED_FILING_SEPARATELY: [
        (Decimal("48350"), Decimal("0.00")),
        (Decimal("300000"), Decimal("0.15")),
        (None, Decimal("0.20")),
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (Decimal("64750"), Decimal("0.00")),
        (Decimal("566700"), Decimal("0.15")),
        (None, Decimal("0.20")),
    ],
}

# A net capital loss can only offset up to this much ordinary income per year;
# anything beyond carries over to future years, which this MVP does not track
# (no persistent multi-year state) - see docs/mvp-scope.md.
CAPITAL_LOSS_ANNUAL_LIMIT = Decimal("3000")

SCHEDULE_B_THRESHOLD = Decimal("1500")

SE_TAX_RATE = Decimal("0.153")  # 12.4% Social Security + 2.9% Medicare
SE_SOCIAL_SECURITY_RATE = Decimal("0.124")
SE_MEDICARE_RATE = Decimal("0.029")
SE_NET_EARNINGS_MULTIPLIER = Decimal("0.9235")
SOCIAL_SECURITY_WAGE_BASE = Decimal("176100")
