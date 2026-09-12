from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import FilingStatus, ReturnStatus


class UserOut(BaseModel):
    id: UUID
    display_name: str
    email: str | None


class TaxReturnCreate(BaseModel):
    tax_year: int
    filing_status: FilingStatus


class TaxReturnOut(BaseModel):
    id: UUID
    user_id: UUID
    tax_year: int
    is_prior_year: bool
    filing_status: FilingStatus
    status: ReturnStatus
    created_at: datetime
    updated_at: datetime
