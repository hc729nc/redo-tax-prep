from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.security import require_owned_field, require_owned_return
from app.db.session import get_db
from app.deps import get_auth_provider, get_blob_store, get_document_repo, get_extracted_field_repo, get_tax_return_repo
from app.repositories.interfaces import (
    AuthProvider,
    DocumentBlobStore,
    DocumentRepository,
    ExtractedFieldRepository,
    TaxReturnRepository,
)
from app.services.document_service import upload_and_extract
from app.services.rate_limit_service import RateLimitExceededError, check_and_increment_upload_usage

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: UUID
    tax_return_id: UUID
    original_filename: str
    document_type: str
    extraction_status: str


class ExtractedFieldOut(BaseModel):
    id: UUID
    field_name: str
    value: str
    confirmed_by_user: bool
    source_page: int | None
    source_text_snippet: str | None


class CorrectFieldRequest(BaseModel):
    new_value: str


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    tax_return_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    document_repo: DocumentRepository = Depends(get_document_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
    blob_store: DocumentBlobStore = Depends(get_blob_store),
    db: Session = Depends(get_db),
) -> DocumentOut:
    user = auth.get_current_user(request)
    require_owned_return(tax_return_id, user, return_repo)

    try:
        check_and_increment_upload_usage(db, user.id)
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=429,
            detail=f"You've reached today's limit of {e.limit} uploads. Please try again tomorrow.",
        )

    content = await file.read()
    document = upload_and_extract(
        tax_return_id=tax_return_id,
        filename=file.filename or "upload.pdf",
        content=content,
        document_repo=document_repo,
        field_repo=field_repo,
        blob_store=blob_store,
    )
    return DocumentOut(
        id=document.id,
        tax_return_id=document.tax_return_id,
        original_filename=document.original_filename,
        document_type=document.document_type.value,
        extraction_status=document.extraction_status.value,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    tax_return_id: UUID,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    document_repo: DocumentRepository = Depends(get_document_repo),
) -> list[DocumentOut]:
    user = auth.get_current_user(request)
    require_owned_return(tax_return_id, user, return_repo)

    docs = document_repo.list_for_return(tax_return_id)
    return [
        DocumentOut(
            id=d.id,
            tax_return_id=d.tax_return_id,
            original_filename=d.original_filename,
            document_type=d.document_type.value,
            extraction_status=d.extraction_status.value,
        )
        for d in docs
    ]


@router.get("/fields", response_model=list[ExtractedFieldOut])
def list_fields_for_return(
    tax_return_id: UUID,
    request: Request,
    confirmed_only: bool = False,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> list[ExtractedFieldOut]:
    user = auth.get_current_user(request)
    require_owned_return(tax_return_id, user, return_repo)

    fields = field_repo.list_for_return(tax_return_id, confirmed_only=confirmed_only)
    return [
        ExtractedFieldOut(
            id=f.id,
            field_name=f.field_name,
            value=f.value,
            confirmed_by_user=f.confirmed_by_user,
            source_page=f.source_page,
            source_text_snippet=f.source_text_snippet,
        )
        for f in fields
    ]


@router.patch("/fields/{field_id}/confirm", response_model=ExtractedFieldOut)
def confirm_field(
    field_id: UUID,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> ExtractedFieldOut:
    user = auth.get_current_user(request)
    require_owned_field(field_id, user, field_repo, return_repo)

    field_repo.confirm(field_id)
    updated = field_repo.get(field_id)
    return ExtractedFieldOut(
        id=updated.id,
        field_name=updated.field_name,
        value=updated.value,
        confirmed_by_user=updated.confirmed_by_user,
        source_page=updated.source_page,
        source_text_snippet=updated.source_text_snippet,
    )


@router.patch("/fields/{field_id}/correct", response_model=ExtractedFieldOut)
def correct_field(
    field_id: UUID,
    body: CorrectFieldRequest,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> ExtractedFieldOut:
    user = auth.get_current_user(request)
    require_owned_field(field_id, user, field_repo, return_repo)

    updated = field_repo.correct(field_id, body.new_value)
    return ExtractedFieldOut(
        id=updated.id,
        field_name=updated.field_name,
        value=updated.value,
        confirmed_by_user=updated.confirmed_by_user,
        source_page=updated.source_page,
        source_text_snippet=updated.source_text_snippet,
    )
