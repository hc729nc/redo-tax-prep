from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities import ExtractedField, TaxReturn
from app.domain.enums import FieldSourceType, FilingStatus, ReturnStatus
from app.services.return_service import _build_structured_input


def _field(field_name: str, value: str) -> ExtractedField:
    return ExtractedField(
        id=uuid4(),
        tax_return_id=uuid4(),
        document_id=uuid4(),
        field_name=field_name,
        value=value,
        source_type=FieldSourceType.TEXT_LAYER_SNIPPET,
        confirmed_by_user=True,
        source_page=1,
        source_acroform_field_name=None,
        source_text_snippet=None,
        source_conversation_message_id=None,
        superseded_by_field_id=None,
        created_at=datetime.now(timezone.utc),
    )


def test_two_w2s_sum_wages_and_withholding():
    tax_return = TaxReturn(
        id=uuid4(),
        user_id=uuid4(),
        tax_year=2025,
        is_prior_year=False,
        filing_status=FilingStatus.SINGLE,
        status=ReturnStatus.DRAFT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    confirmed_fields = [
        _field("w2.box1_wages", "40000"),
        _field("w2.box2_federal_withholding", "4000"),
        _field("w2.box1_wages", "25000"),  # second job's W-2
        _field("w2.box2_federal_withholding", "2500"),
    ]

    result = _build_structured_input(tax_return, confirmed_fields)

    assert result.wages == Decimal("65000")
    assert result.federal_withholding_w2 == Decimal("6500")
