from decimal import ROUND_HALF_UP, Decimal


def round_dollars(value: Decimal) -> Decimal:
    """IRS forms are completed in whole dollars - round every computed line, not just
    the final total, so intermediate fractional cents never leak into later lines."""
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
