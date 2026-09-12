from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models import (
    ConversationSessionModel,
    ExtractedFieldModel,
    TaxReturnModel,
    UploadedDocumentModel,
)
from app.domain.entities import ConversationSession, ExtractedField, TaxReturn, UploadedDocument
from app.domain.enums import (
    DocumentType,
    ExtractionStatus,
    FieldSourceType,
    FilingStatus,
    ReturnStatus,
)
from app.repositories.interfaces import (
    ConversationSessionRepository,
    DocumentRepository,
    ExtractedFieldRepository,
    TaxReturnRepository,
)


def _tax_return_to_entity(m: TaxReturnModel) -> TaxReturn:
    return TaxReturn(
        id=UUID(m.id),
        user_id=UUID(m.user_id),
        tax_year=m.tax_year,
        is_prior_year=m.is_prior_year,
        filing_status=FilingStatus(m.filing_status),
        status=ReturnStatus(m.status),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _document_to_entity(m: UploadedDocumentModel) -> UploadedDocument:
    return UploadedDocument(
        id=UUID(m.id),
        tax_return_id=UUID(m.tax_return_id),
        original_filename=m.original_filename,
        document_type=DocumentType(m.document_type),
        storage_key=m.storage_key,
        extraction_status=ExtractionStatus(m.extraction_status),
        uploaded_at=m.uploaded_at,
    )


def _conversation_session_to_entity(m: ConversationSessionModel) -> ConversationSession:
    return ConversationSession(
        id=UUID(m.id),
        tax_return_id=UUID(m.tax_return_id),
        user_id=UUID(m.user_id),
        created_at=m.created_at,
        last_active_at=m.last_active_at,
    )


def _field_to_entity(m: ExtractedFieldModel) -> ExtractedField:
    return ExtractedField(
        id=UUID(m.id),
        tax_return_id=UUID(m.tax_return_id),
        document_id=UUID(m.document_id) if m.document_id else None,
        field_name=m.field_name,
        value=m.value,
        source_type=FieldSourceType(m.source_type),
        confirmed_by_user=m.confirmed_by_user,
        source_page=m.source_page,
        source_acroform_field_name=m.source_acroform_field_name,
        source_text_snippet=m.source_text_snippet,
        source_conversation_message_id=(
            UUID(m.source_conversation_message_id) if m.source_conversation_message_id else None
        ),
        superseded_by_field_id=(
            UUID(m.superseded_by_field_id) if m.superseded_by_field_id else None
        ),
        created_at=m.created_at,
    )


class SqlAlchemyTaxReturnRepository(TaxReturnRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, return_id: UUID) -> TaxReturn | None:
        m = self.db.get(TaxReturnModel, str(return_id))
        return _tax_return_to_entity(m) if m else None

    def list_for_user(self, user_id: UUID) -> list[TaxReturn]:
        rows = (
            self.db.query(TaxReturnModel)
            .filter(TaxReturnModel.user_id == str(user_id))
            .order_by(TaxReturnModel.tax_year.desc())
            .all()
        )
        return [_tax_return_to_entity(m) for m in rows]

    def find_by_year(self, user_id: UUID, tax_year: int, is_prior_year: bool) -> TaxReturn | None:
        m = (
            self.db.query(TaxReturnModel)
            .filter(
                TaxReturnModel.user_id == str(user_id),
                TaxReturnModel.tax_year == tax_year,
                TaxReturnModel.is_prior_year == is_prior_year,
            )
            .first()
        )
        return _tax_return_to_entity(m) if m else None

    def create(
        self,
        user_id: UUID,
        tax_year: int,
        filing_status: FilingStatus,
        is_prior_year: bool = False,
    ) -> TaxReturn:
        m = TaxReturnModel(
            id=str(uuid4()),
            user_id=str(user_id),
            tax_year=tax_year,
            filing_status=filing_status.value,
            is_prior_year=is_prior_year,
            status=ReturnStatus.DRAFT.value,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _tax_return_to_entity(m)

    def update_status(self, return_id: UUID, status: ReturnStatus) -> None:
        m = self.db.get(TaxReturnModel, str(return_id))
        if m is None:
            raise ValueError(f"TaxReturn {return_id} not found")
        m.status = status.value
        self.db.commit()

    def save_computed_return(self, return_id: UUID, computed_return_json: str) -> None:
        m = self.db.get(TaxReturnModel, str(return_id))
        if m is None:
            raise ValueError(f"TaxReturn {return_id} not found")
        m.computed_return_json = computed_return_json
        m.status = ReturnStatus.COMPUTED.value
        self.db.commit()

    def get_computed_return_json(self, return_id: UUID) -> str | None:
        m = self.db.get(TaxReturnModel, str(return_id))
        return m.computed_return_json if m else None


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tax_return_id: UUID,
        filename: str,
        doc_type: DocumentType,
        storage_key: str,
    ) -> UploadedDocument:
        m = UploadedDocumentModel(
            id=str(uuid4()),
            tax_return_id=str(tax_return_id),
            original_filename=filename,
            document_type=doc_type.value,
            storage_key=storage_key,
            extraction_status=ExtractionStatus.PENDING.value,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _document_to_entity(m)

    def get(self, document_id: UUID) -> UploadedDocument | None:
        m = self.db.get(UploadedDocumentModel, str(document_id))
        return _document_to_entity(m) if m else None

    def list_for_return(self, tax_return_id: UUID) -> list[UploadedDocument]:
        rows = (
            self.db.query(UploadedDocumentModel)
            .filter(UploadedDocumentModel.tax_return_id == str(tax_return_id))
            .order_by(UploadedDocumentModel.uploaded_at.asc())
            .all()
        )
        return [_document_to_entity(m) for m in rows]

    def set_extraction_status(self, document_id: UUID, status: ExtractionStatus) -> None:
        m = self.db.get(UploadedDocumentModel, str(document_id))
        if m is None:
            raise ValueError(f"UploadedDocument {document_id} not found")
        m.extraction_status = status.value
        self.db.commit()

    def set_storage_key(self, document_id: UUID, storage_key: str) -> None:
        m = self.db.get(UploadedDocumentModel, str(document_id))
        if m is None:
            raise ValueError(f"UploadedDocument {document_id} not found")
        m.storage_key = storage_key
        self.db.commit()


class SqlAlchemyExtractedFieldRepository(ExtractedFieldRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, field: ExtractedField) -> ExtractedField:
        m = ExtractedFieldModel(
            id=str(field.id),
            tax_return_id=str(field.tax_return_id),
            document_id=str(field.document_id) if field.document_id else None,
            field_name=field.field_name,
            value=field.value,
            source_type=field.source_type.value,
            confirmed_by_user=field.confirmed_by_user,
            source_page=field.source_page,
            source_acroform_field_name=field.source_acroform_field_name,
            source_text_snippet=field.source_text_snippet,
            source_conversation_message_id=(
                str(field.source_conversation_message_id)
                if field.source_conversation_message_id
                else None
            ),
            superseded_by_field_id=(
                str(field.superseded_by_field_id) if field.superseded_by_field_id else None
            ),
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _field_to_entity(m)

    def list_for_return(
        self, tax_return_id: UUID, confirmed_only: bool = False
    ) -> list[ExtractedField]:
        query = self.db.query(ExtractedFieldModel).filter(
            ExtractedFieldModel.tax_return_id == str(tax_return_id),
            ExtractedFieldModel.superseded_by_field_id.is_(None),
        )
        if confirmed_only:
            query = query.filter(ExtractedFieldModel.confirmed_by_user.is_(True))
        rows = query.order_by(ExtractedFieldModel.created_at.asc()).all()
        return [_field_to_entity(m) for m in rows]

    def get(self, field_id: UUID) -> ExtractedField | None:
        m = self.db.get(ExtractedFieldModel, str(field_id))
        return _field_to_entity(m) if m else None

    def confirm(self, field_id: UUID) -> None:
        m = self.db.get(ExtractedFieldModel, str(field_id))
        if m is None:
            raise ValueError(f"ExtractedField {field_id} not found")
        m.confirmed_by_user = True
        self.db.commit()

    def correct(self, field_id: UUID, new_value: str) -> ExtractedField:
        old = self.db.get(ExtractedFieldModel, str(field_id))
        if old is None:
            raise ValueError(f"ExtractedField {field_id} not found")

        new = ExtractedFieldModel(
            id=str(uuid4()),
            tax_return_id=old.tax_return_id,
            document_id=old.document_id,
            field_name=old.field_name,
            value=new_value,
            source_type=FieldSourceType.USER_MANUAL_ENTRY.value,
            confirmed_by_user=True,
            source_page=old.source_page,
            source_acroform_field_name=old.source_acroform_field_name,
            source_text_snippet=old.source_text_snippet,
            source_conversation_message_id=old.source_conversation_message_id,
        )
        self.db.add(new)
        self.db.flush()
        old.superseded_by_field_id = new.id
        self.db.commit()
        self.db.refresh(new)
        return _field_to_entity(new)


class SqlAlchemyConversationSessionRepository(ConversationSessionRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, tax_return_id: UUID, user_id: UUID) -> ConversationSession:
        m = ConversationSessionModel(
            id=str(uuid4()), tax_return_id=str(tax_return_id), user_id=str(user_id)
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _conversation_session_to_entity(m)

    def get(self, session_id: UUID) -> ConversationSession | None:
        m = self.db.get(ConversationSessionModel, str(session_id))
        return _conversation_session_to_entity(m) if m else None

    def touch(self, session_id: UUID) -> None:
        m = self.db.get(ConversationSessionModel, str(session_id))
        if m is None:
            raise ValueError(f"ConversationSession {session_id} not found")
        m.last_active_at = datetime.now(timezone.utc)
        self.db.commit()
