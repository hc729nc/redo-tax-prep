from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.routes_documents import DocumentOut
from app.deps import (
    get_blob_store,
    get_document_repo,
    get_extracted_field_repo,
    get_tax_return_repo,
)
from app.repositories.interfaces import (
    DocumentBlobStore,
    DocumentRepository,
    ExtractedFieldRepository,
    TaxReturnRepository,
)
from app.services.document_service import upload_and_extract
from app.services.prior_year_service import ensure_prior_year_return, get_comparison

router = APIRouter(prefix="/api/prior-year", tags=["prior-year"])


@router.post("/upload", response_model=DocumentOut)
async def upload_prior_year_return(
    current_return_id: UUID,
    file: UploadFile = File(...),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    document_repo: DocumentRepository = Depends(get_document_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
    blob_store: DocumentBlobStore = Depends(get_blob_store),
) -> DocumentOut:
    current = return_repo.get(current_return_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Tax return not found")

    prior_return = ensure_prior_year_return(current, return_repo)

    content = await file.read()
    document = upload_and_extract(
        tax_return_id=prior_return.id,
        filename=file.filename or "prior_year_1040.pdf",
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


@router.get("/compare")
def compare_to_prior_year(
    current_return_id: UUID,
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> dict:
    return get_comparison(current_return_id, return_repo=return_repo, field_repo=field_repo)
