import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tax_returns: Mapped[list["TaxReturnModel"]] = relationship(back_populates="user")


class TaxReturnModel(Base):
    __tablename__ = "tax_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    tax_year: Mapped[int] = mapped_column(Integer)
    is_prior_year: Mapped[bool] = mapped_column(Boolean, default=False)
    filing_status: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    computed_return_json: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["UserModel"] = relationship(back_populates="tax_returns")
    documents: Mapped[list["UploadedDocumentModel"]] = relationship(back_populates="tax_return")
    extracted_fields: Mapped[list["ExtractedFieldModel"]] = relationship(back_populates="tax_return")


class UploadedDocumentModel(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    tax_return_id: Mapped[str] = mapped_column(String(36), ForeignKey("tax_returns.id"))
    original_filename: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(32))
    storage_key: Mapped[str] = mapped_column(String(512))
    extraction_status: Mapped[str] = mapped_column(String(32), default="pending")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tax_return: Mapped["TaxReturnModel"] = relationship(back_populates="documents")
    extracted_fields: Mapped[list["ExtractedFieldModel"]] = relationship(back_populates="document")


class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    tax_return_id: Mapped[str] = mapped_column(String(36), ForeignKey("tax_returns.id"))
    document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("uploaded_documents.id"), nullable=True
    )
    field_name: Mapped[str] = mapped_column(String(128))
    value: Mapped[str] = mapped_column(String(1024))
    source_type: Mapped[str] = mapped_column(String(32))
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_acroform_field_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_text_snippet: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_conversation_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    superseded_by_field_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tax_return: Mapped["TaxReturnModel"] = relationship(back_populates="extracted_fields")
    document: Mapped["UploadedDocumentModel | None"] = relationship(back_populates="extracted_fields")


class ConversationSessionModel(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    tax_return_id: Mapped[str] = mapped_column(String(36), ForeignKey("tax_returns.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
