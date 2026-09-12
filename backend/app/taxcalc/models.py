from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from app.domain.enums import FilingStatus


@dataclass
class StructuredReturnInput:
    """Plain-data input to the engine, assembled by return_service from confirmed
    ExtractedField rows. The engine never touches the database directly."""

    filing_status: FilingStatus
    wages: Decimal = Decimal("0")
    federal_withholding_w2: Decimal = Decimal("0")
    federal_withholding_1099: Decimal = Decimal("0")
    taxable_interest: Decimal = Decimal("0")
    ordinary_dividends: Decimal = Decimal("0")
    self_employment_gross_receipts: Decimal = Decimal("0")
    self_employment_expenses: Decimal = Decimal("0")
    itemized_deductions: dict[str, Decimal] = field(default_factory=dict)


@dataclass
class LineItem:
    line_ref: str
    label: str
    value: Decimal
    source_field_ids: list[UUID] = field(default_factory=list)


@dataclass
class ScheduleCResult:
    gross_receipts: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    line_items: list[LineItem]


@dataclass
class ScheduleSEResult:
    net_earnings_from_se: Decimal
    se_tax: Decimal
    half_se_tax_deduction: Decimal
    line_items: list[LineItem]


@dataclass
class ScheduleBResult:
    total_taxable_interest: Decimal
    total_ordinary_dividends: Decimal
    required: bool
    line_items: list[LineItem]


@dataclass
class ScheduleAResult:
    total_itemized_deductions: Decimal
    line_items: list[LineItem]


@dataclass
class Form1040Result:
    total_income: Decimal
    adjustments_to_income: Decimal
    agi: Decimal
    deduction_amount: Decimal
    deduction_is_itemized: bool
    taxable_income: Decimal
    tax_before_credits: Decimal
    total_tax: Decimal
    total_payments: Decimal
    refund_amount: Decimal
    amount_owed: Decimal
    line_items: list[LineItem]


@dataclass
class ComputedReturn:
    tax_year: int
    form_1040: Form1040Result
    schedule_a: ScheduleAResult | None
    schedule_b: ScheduleBResult | None
    schedule_c: ScheduleCResult | None
    schedule_se: ScheduleSEResult | None

    def all_line_items(self) -> list[LineItem]:
        items = list(self.form_1040.line_items)
        for sched in (self.schedule_a, self.schedule_b, self.schedule_c, self.schedule_se):
            if sched is not None:
                items.extend(sched.line_items)
        return items
