from decimal import Decimal
from uuid import UUID

from app.domain.entities import TaxReturn
from app.repositories.interfaces import ExtractedFieldRepository, TaxReturnRepository
from app.services.return_service import compute_and_persist


def ensure_prior_year_return(
    current_tax_return: TaxReturn, return_repo: TaxReturnRepository
) -> TaxReturn:
    """Get or create the prior-year TaxReturn row (tax_year - 1) linked to the same
    user as the given current-year return."""
    prior_tax_year = current_tax_return.tax_year - 1
    existing = return_repo.find_by_year(
        current_tax_return.user_id, prior_tax_year, is_prior_year=True
    )
    if existing is not None:
        return existing
    return return_repo.create(
        user_id=current_tax_return.user_id,
        tax_year=prior_tax_year,
        filing_status=current_tax_return.filing_status,
        is_prior_year=True,
    )


def _sum_confirmed_prior_fields(
    prior_return_id: UUID, field_repo: ExtractedFieldRepository
) -> dict[str, Decimal]:
    values: dict[str, Decimal] = {}
    for f in field_repo.list_for_return(prior_return_id, confirmed_only=True):
        try:
            parsed = Decimal(f.value)
        except Exception:
            continue
        values[f.field_name] = values.get(f.field_name, Decimal("0")) + parsed
    return values


def get_comparison(
    current_return_id: UUID,
    *,
    return_repo: TaxReturnRepository,
    field_repo: ExtractedFieldRepository,
) -> dict:
    """Compare the current return's computed numbers against the confirmed
    prior-year figures (extracted straight from the prior-year 1040, not
    recomputed - those numbers were already filed)."""
    current = return_repo.get(current_return_id)
    if current is None:
        raise ValueError(f"TaxReturn {current_return_id} not found")

    prior = return_repo.find_by_year(current.user_id, current.tax_year - 1, is_prior_year=True)
    if prior is None:
        return {"has_prior_year": False}

    prior_values = _sum_confirmed_prior_fields(prior.id, field_repo)
    if not prior_values:
        return {"has_prior_year": True, "prior_tax_year": prior.tax_year, "prior_year_has_data": False}

    current_computed = compute_and_persist(current_return_id, return_repo=return_repo, field_repo=field_repo)
    current_lines = {item.line_ref: item.value for item in current_computed.form_1040.line_items}

    comparisons = [
        ("wages", current_lines.get("1z", Decimal("0")), prior_values.get("prior_year.wages")),
        ("agi", current_computed.form_1040.agi, prior_values.get("prior_year.agi")),
        ("total_tax", current_computed.form_1040.total_tax, prior_values.get("prior_year.total_tax")),
    ]

    deltas = {}
    for label, current_value, prior_value in comparisons:
        deltas[label] = {
            "current": str(current_value),
            "prior": str(prior_value) if prior_value is not None else None,
            "change": str(current_value - prior_value) if prior_value is not None else None,
        }

    return {
        "has_prior_year": True,
        "prior_tax_year": prior.tax_year,
        "prior_year_has_data": True,
        "comparisons": deltas,
    }
