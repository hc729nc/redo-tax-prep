from decimal import Decimal

from app.taxcalc.schedule_b import compute_schedule_b


def test_schedule_b_not_required_under_threshold():
    result = compute_schedule_b(
        total_taxable_interest=Decimal("1000"), total_ordinary_dividends=Decimal("200")
    )
    assert result.required is False


def test_schedule_b_required_when_interest_exceeds_threshold():
    result = compute_schedule_b(
        total_taxable_interest=Decimal("2000"), total_ordinary_dividends=Decimal("0")
    )
    assert result.required is True


def test_schedule_b_required_when_dividends_exceed_threshold():
    result = compute_schedule_b(
        total_taxable_interest=Decimal("0"), total_ordinary_dividends=Decimal("1501")
    )
    assert result.required is True


def test_schedule_b_exactly_at_threshold_not_required():
    result = compute_schedule_b(
        total_taxable_interest=Decimal("1500"), total_ordinary_dividends=Decimal("1500")
    )
    assert result.required is False
