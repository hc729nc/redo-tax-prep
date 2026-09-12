from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import (
    DocumentType,
    ExtractionStatus,
    FieldSourceType,
    FilingStatus,
    ReturnStatus,
)


@dataclass
class User:
    id: UUID
    display_name: str
    email: str | None
    created_at: datetime


@dataclass
class TaxReturn:
    id: UUID
    user_id: UUID
    tax_year: int
    is_prior_year: bool
    filing_status: FilingStatus
    status: ReturnStatus
    created_at: datetime
    updated_at: datetime


@dataclass
class UploadedDocument:
    id: UUID
    tax_return_id: UUID
    original_filename: str
    document_type: DocumentType
    storage_key: str
    extraction_status: ExtractionStatus
    uploaded_at: datetime


@dataclass
class ExtractedField:
    id: UUID
    tax_return_id: UUID
    document_id: UUID | None
    field_name: str
    value: str
    source_type: FieldSourceType
    confirmed_by_user: bool
    source_page: int | None
    source_acroform_field_name: str | None
    source_text_snippet: str | None
    source_conversation_message_id: UUID | None
    superseded_by_field_id: UUID | None
    created_at: datetime


@dataclass
class ConversationSession:
    id: UUID
    tax_return_id: UUID
    user_id: UUID
    created_at: datetime
    last_active_at: datetime
