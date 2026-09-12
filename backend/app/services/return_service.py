import json
from dataclasses import asdict
from decimal import Decimal
from uuid import UUID

from app.domain.entities import TaxReturn
from app.repositories.interfaces import ExtractedFieldRepository, TaxReturnRepository
from app.taxcalc.engine import compute_return as run_tax_engine
from app.taxcalc.models import ComputedReturn, StructuredReturnInput


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _build_structured_input(
    tax_return: TaxReturn, confirmed_fields: list
) -> StructuredReturnInput:
    """Sum same-named fields rather than taking the last one - a person can have
    multiple W-2s or multiple 1099s of the same type, and each contributes its own
    confirmed field row (corrections are excluded upstream via superseded_by_field_id,
    so this never double-counts a corrected value)."""
    values: dict[str, Decimal] = {}
    for f in confirmed_fields:
        try:
            parsed = Decimal(f.value)
        except Exception:
            continue
        values[f.field_name] = values.get(f.field_name, Decimal("0")) + parsed

    itemized_deductions = {
        name.removeprefix("schedule_a."): value
        for name, value in values.items()
        if name.startswith("schedule_a.")
    }

    return StructuredReturnInput(
        filing_status=tax_return.filing_status,
        wages=values.get("w2.box1_wages", Decimal("0")),
        federal_withholding_w2=values.get("w2.box2_federal_withholding", Decimal("0")),
        taxable_interest=values.get("1099_int.box1_interest", Decimal("0")),
        ordinary_dividends=values.get("1099_div.box1a_ordinary_dividends", Decimal("0")),
        self_employment_gross_receipts=values.get("1099_nec.box1_nonemployee_compensation", Decimal("0")),
        self_employment_expenses=values.get("1099_nec.total_expenses", Decimal("0")),
        itemized_deductions=itemized_deductions,
    )


def compute_and_persist(
    tax_return_id: UUID,
    *,
    return_repo: TaxReturnRepository,
    field_repo: ExtractedFieldRepository,
) -> ComputedReturn:
    tax_return = return_repo.get(tax_return_id)
    if tax_return is None:
        raise ValueError(f"TaxReturn {tax_return_id} not found")

    confirmed_fields = field_repo.list_for_return(tax_return_id, confirmed_only=True)
    structured_input = _build_structured_input(tax_return, confirmed_fields)
    computed = run_tax_engine(structured_input)

    computed_json = json.dumps(asdict(computed), default=_decimal_default)
    return_repo.save_computed_return(tax_return_id, computed_json)

    return computed
