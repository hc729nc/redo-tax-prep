from decimal import Decimal

from app.domain.enums import FilingStatus
from app.taxcalc.constants_2025 import STANDARD_DEDUCTION, TAX_BRACKETS
from app.taxcalc.models import Form1040Result, LineItem, ScheduleAResult, ScheduleBResult, ScheduleCResult, ScheduleSEResult
from app.taxcalc.rounding import round_dollars

ZERO = Decimal("0")


def calculate_tax(taxable_income: Decimal, filing_status: FilingStatus) -> Decimal:
    """Marginal-bracket tax calculation (a simplification of the IRS Tax Tables, which
    round to $50 income bands for incomes under $100k - close enough for this MVP's
    purposes, but not an exact reproduction of the published tables)."""
    if taxable_income <= ZERO:
        return ZERO

    tax = ZERO
    lower_bound = ZERO
    for upper_bound, rate in TAX_BRACKETS[filing_status]:
        if upper_bound is None or taxable_income <= upper_bound:
            tax += (taxable_income - lower_bound) * rate
            break
        tax += (upper_bound - lower_bound) * rate
        lower_bound = upper_bound
    return round_dollars(tax)


def compute_form_1040(
    *,
    filing_status: FilingStatus,
    wages: Decimal,
    federal_withholding_w2: Decimal,
    federal_withholding_1099: Decimal = ZERO,
    schedule_b: ScheduleBResult | None = None,
    schedule_c: ScheduleCResult | None = None,
    schedule_se: ScheduleSEResult | None = None,
    schedule_a: ScheduleAResult | None = None,
) -> Form1040Result:
    taxable_interest = schedule_b.total_taxable_interest if schedule_b else ZERO
    ordinary_dividends = schedule_b.total_ordinary_dividends if schedule_b else ZERO
    business_income = schedule_c.net_profit if schedule_c else ZERO

    total_income = wages + taxable_interest + ordinary_dividends + business_income

    adjustments_to_income = schedule_se.half_se_tax_deduction if schedule_se else ZERO
    agi = total_income - adjustments_to_income

    standard_deduction = STANDARD_DEDUCTION[filing_status]
    itemized_total = schedule_a.total_itemized_deductions if schedule_a else ZERO
    deduction_is_itemized = itemized_total > standard_deduction
    deduction_amount = itemized_total if deduction_is_itemized else standard_deduction

    taxable_income = max(agi - deduction_amount, ZERO)
    tax_before_credits = calculate_tax(taxable_income, filing_status)

    se_tax = schedule_se.se_tax if schedule_se else ZERO
    total_tax = tax_before_credits + se_tax

    total_withholding = federal_withholding_w2 + federal_withholding_1099
    total_payments = total_withholding

    refund_amount = max(total_payments - total_tax, ZERO)
    amount_owed = max(total_tax - total_payments, ZERO)

    line_items = [
        LineItem(line_ref="1a", label="Wages from Form(s) W-2, box 1", value=wages),
        LineItem(line_ref="1z", label="Total wages", value=wages),
        LineItem(line_ref="2b", label="Taxable interest", value=taxable_interest),
        LineItem(line_ref="3b", label="Ordinary dividends", value=ordinary_dividends),
        LineItem(line_ref="8", label="Additional income from Schedule 1", value=business_income),
        LineItem(line_ref="9", label="Total income", value=total_income),
        LineItem(line_ref="10", label="Adjustments to income", value=adjustments_to_income),
        LineItem(line_ref="11", label="Adjusted gross income", value=agi),
        LineItem(line_ref="12", label="Standard or itemized deduction", value=deduction_amount),
        LineItem(line_ref="15", label="Taxable income", value=taxable_income),
        LineItem(line_ref="16", label="Tax", value=tax_before_credits),
        LineItem(line_ref="17", label="Amount from Schedule 2, line 3", value=ZERO),
        LineItem(line_ref="18", label="Add lines 16 and 17", value=tax_before_credits),
        LineItem(line_ref="21", label="Total credits", value=ZERO),
        LineItem(line_ref="22", label="Subtract line 21 from line 18", value=tax_before_credits),
        LineItem(line_ref="23", label="Other taxes (self-employment tax)", value=se_tax),
        LineItem(line_ref="24", label="Total tax", value=total_tax),
        LineItem(line_ref="25a", label="Federal income tax withheld - Form(s) W-2", value=federal_withholding_w2),
        LineItem(line_ref="25b", label="Federal income tax withheld - Form(s) 1099", value=federal_withholding_1099),
        LineItem(line_ref="25d", label="Total withholding", value=total_withholding),
        LineItem(line_ref="33", label="Total payments", value=total_payments),
        LineItem(line_ref="34", label="Overpayment", value=refund_amount),
        LineItem(line_ref="37", label="Amount you owe", value=amount_owed),
    ]

    return Form1040Result(
        total_income=total_income,
        adjustments_to_income=adjustments_to_income,
        agi=agi,
        deduction_amount=deduction_amount,
        deduction_is_itemized=deduction_is_itemized,
        taxable_income=taxable_income,
        tax_before_credits=tax_before_credits,
        total_tax=total_tax,
        total_payments=total_payments,
        refund_amount=refund_amount,
        amount_owed=amount_owed,
        line_items=line_items,
    )
