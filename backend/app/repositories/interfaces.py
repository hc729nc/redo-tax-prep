from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from fastapi import Request

from app.domain.entities import ConversationSession, ExtractedField, TaxReturn, UploadedDocument, User
from app.domain.enums import DocumentType, ExtractionStatus, FilingStatus, ReturnStatus


class TaxReturnRepository(ABC):
    @abstractmethod
    def get(self, return_id: UUID) -> TaxReturn | None: ...

    @abstractmethod
    def list_for_user(self, user_id: UUID) -> list[TaxReturn]: ...

    @abstractmethod
    def find_by_year(
        self, user_id: UUID, tax_year: int, is_prior_year: bool
    ) -> TaxReturn | None: ...

    @abstractmethod
    def create(
        self,
        user_id: UUID,
        tax_year: int,
        filing_status: FilingStatus,
        is_prior_year: bool = False,
    ) -> TaxReturn: ...

    @abstractmethod
    def update_status(self, return_id: UUID, status: ReturnStatus) -> None: ...

    @abstractmethod
    def save_computed_return(self, return_id: UUID, computed_return_json: str) -> None: ...

    @abstractmethod
    def get_computed_return_json(self, return_id: UUID) -> str | None: ...


class DocumentRepository(ABC):
    @abstractmethod
    def create(
        self,
        tax_return_id: UUID,
        filename: str,
        doc_type: DocumentType,
        storage_key: str,
    ) -> UploadedDocument: ...

    @abstractmethod
    def get(self, document_id: UUID) -> UploadedDocument | None: ...

    @abstractmethod
    def list_for_return(self, tax_return_id: UUID) -> list[UploadedDocument]: ...

    @abstractmethod
    def set_extraction_status(self, document_id: UUID, status: ExtractionStatus) -> None: ...

    @abstractmethod
    def set_storage_key(self, document_id: UUID, storage_key: str) -> None: ...


class ExtractedFieldRepository(ABC):
    @abstractmethod
    def add(self, field: ExtractedField) -> ExtractedField: ...

    @abstractmethod
    def list_for_return(
        self, tax_return_id: UUID, confirmed_only: bool = False
    ) -> list[ExtractedField]: ...

    @abstractmethod
    def get(self, field_id: UUID) -> ExtractedField | None: ...

    @abstractmethod
    def confirm(self, field_id: UUID) -> None: ...

    @abstractmethod
    def correct(self, field_id: UUID, new_value: str) -> ExtractedField: ...


class DocumentBlobStore(ABC):
    @abstractmethod
    def save(
        self, tax_return_id: UUID, document_id: UUID, content: bytes, filename: str
    ) -> str: ...

    @abstractmethod
    def load(self, storage_key: str) -> bytes: ...

    @abstractmethod
    def delete(self, storage_key: str) -> None: ...


class ConversationSessionRepository(ABC):
    @abstractmethod
    def create(self, tax_return_id: UUID, user_id: UUID) -> ConversationSession: ...

    @abstractmethod
    def get(self, session_id: UUID) -> ConversationSession | None: ...

    @abstractmethod
    def get_latest_for_return(self, tax_return_id: UUID) -> ConversationSession | None: ...

    @abstractmethod
    def touch(self, session_id: UUID) -> None: ...


class AuthProvider(ABC):
    @abstractmethod
    def get_current_user(self, request: Request) -> User: ...

    @abstractmethod
    def create_session(self, user: User) -> str: ...
