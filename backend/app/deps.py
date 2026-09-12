from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.filesystem_blob_store import LocalFilesystemBlobStore
from app.repositories.interfaces import (
    AuthProvider,
    ConversationSessionRepository,
    DocumentBlobStore,
    DocumentRepository,
    ExtractedFieldRepository,
    TaxReturnRepository,
)
from app.repositories.mock_auth import MockAuthProvider
from app.repositories.sqlite_impl import (
    SqlAlchemyConversationSessionRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyExtractedFieldRepository,
    SqlAlchemyTaxReturnRepository,
)

# This module is the single place that decides "mock vs. real" for each
# repository interface. Migrating to Postgres/S3/Cognito later means adding a
# new *_impl.py and changing only the constructors below - no route, service,
# or agent-tool code changes, since all of those depend on the ABCs in
# app.repositories.interfaces, never on these concrete classes.


def get_tax_return_repo(db: Session = Depends(get_db)) -> TaxReturnRepository:
    return SqlAlchemyTaxReturnRepository(db)


def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(db)


def get_extracted_field_repo(db: Session = Depends(get_db)) -> ExtractedFieldRepository:
    return SqlAlchemyExtractedFieldRepository(db)


def get_conversation_session_repo(
    db: Session = Depends(get_db),
) -> ConversationSessionRepository:
    return SqlAlchemyConversationSessionRepository(db)


def get_blob_store(settings: Settings = Depends(get_settings)) -> DocumentBlobStore:
    return LocalFilesystemBlobStore(settings.storage_root)


def get_auth_provider(db: Session = Depends(get_db)) -> AuthProvider:
    return MockAuthProvider(db)
