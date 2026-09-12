from uuid import UUID

from fastapi import HTTPException

from app.domain.entities import ExtractedField, TaxReturn, UploadedDocument, User
from app.repositories.interfaces import (
    DocumentRepository,
    ExtractedFieldRepository,
    TaxReturnRepository,
)

_NOT_FOUND = HTTPException(status_code=404, detail="Not found")


def require_owned_return(
    return_id: UUID, user: User, return_repo: TaxReturnRepository
) -> TaxReturn:
    """Fetch a tax return and verify the current user owns it. Raises 404 (not
    403) on both "doesn't exist" and "exists but isn't yours" so a caller can't
    use this to enumerate other users' return IDs."""
    tax_return = return_repo.get(return_id)
    if tax_return is None or tax_return.user_id != user.id:
        raise _NOT_FOUND
    return tax_return


def require_owned_document(
    document_id: UUID,
    user: User,
    document_repo: DocumentRepository,
    return_repo: TaxReturnRepository,
) -> UploadedDocument:
    document = document_repo.get(document_id)
    if document is None:
        raise _NOT_FOUND
    require_owned_return(document.tax_return_id, user, return_repo)
    return document


def require_owned_field(
    field_id: UUID,
    user: User,
    field_repo: ExtractedFieldRepository,
    return_repo: TaxReturnRepository,
) -> ExtractedField:
    field = field_repo.get(field_id)
    if field is None:
        raise _NOT_FOUND
    require_owned_return(field.tax_return_id, user, return_repo)
    return field
