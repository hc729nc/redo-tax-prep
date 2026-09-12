from app.config import get_settings
from app.taxcalc.form_1040 import compute_form_1040
from app.taxcalc.models import ComputedReturn, StructuredReturnInput
from app.taxcalc.schedule_a import compute_schedule_a
from app.taxcalc.schedule_b import compute_schedule_b
from app.taxcalc.schedule_c import compute_schedule_c
from app.taxcalc.schedule_d import compute_schedule_d
from app.taxcalc.schedule_se import compute_schedule_se


def compute_return(structured_input: StructuredReturnInput) -> ComputedReturn:
    schedule_c = None
    if structured_input.self_employment_gross_receipts or structured_input.self_employment_expenses:
        schedule_c = compute_schedule_c(
            gross_receipts=structured_input.self_employment_gross_receipts,
            total_expenses=structured_input.self_employment_expenses,
        )

    schedule_se = compute_schedule_se(schedule_c.net_profit) if schedule_c else None

    schedule_b = None
    if structured_input.taxable_interest or structured_input.ordinary_dividends:
        schedule_b = compute_schedule_b(
            total_taxable_interest=structured_input.taxable_interest,
            total_ordinary_dividends=structured_input.ordinary_dividends,
        )

    schedule_a = None
    if structured_input.itemized_deductions:
        schedule_a = compute_schedule_a(structured_input.itemized_deductions)

    schedule_d = None
    if structured_input.short_term_capital_gain or structured_input.long_term_capital_gain:
        schedule_d = compute_schedule_d(
            short_term_gain=structured_input.short_term_capital_gain,
            long_term_gain=structured_input.long_term_capital_gain,
        )

    form_1040 = compute_form_1040(
        filing_status=structured_input.filing_status,
        wages=structured_input.wages,
        federal_withholding_w2=structured_input.federal_withholding_w2,
        federal_withholding_1099=structured_input.federal_withholding_1099,
        schedule_b=schedule_b,
        schedule_c=schedule_c,
        schedule_d=schedule_d,
        schedule_se=schedule_se,
        schedule_a=schedule_a,
    )

    return ComputedReturn(
        tax_year=get_settings().tax_year,
        form_1040=form_1040,
        schedule_a=schedule_a,
        schedule_b=schedule_b,
        schedule_c=schedule_c,
        schedule_d=schedule_d,
        schedule_se=schedule_se,
    )
