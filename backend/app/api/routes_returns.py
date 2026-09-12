from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.api.schemas import TaxReturnCreate, TaxReturnOut
from app.config import get_settings
from app.deps import get_auth_provider, get_extracted_field_repo, get_tax_return_repo
from app.pdfgen.filler import fill_form_1040
from app.repositories.filesystem_blob_store import LocalFilesystemBlobStore
from app.repositories.interfaces import AuthProvider, ExtractedFieldRepository, TaxReturnRepository
from app.services.return_service import compute_and_persist

router = APIRouter(prefix="/api/returns", tags=["returns"])


def _to_out(r) -> TaxReturnOut:
    return TaxReturnOut(
        id=r.id,
        user_id=r.user_id,
        tax_year=r.tax_year,
        is_prior_year=r.is_prior_year,
        filing_status=r.filing_status,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.post("", response_model=TaxReturnOut)
def create_return(
    body: TaxReturnCreate,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    repo: TaxReturnRepository = Depends(get_tax_return_repo),
) -> TaxReturnOut:
    user = auth.get_current_user(request)
    created = repo.create(
        user_id=user.id, tax_year=body.tax_year, filing_status=body.filing_status
    )
    return _to_out(created)


@router.get("", response_model=list[TaxReturnOut])
def list_returns(
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    repo: TaxReturnRepository = Depends(get_tax_return_repo),
) -> list[TaxReturnOut]:
    user = auth.get_current_user(request)
    return [_to_out(r) for r in repo.list_for_user(user.id)]


@router.get("/{return_id}", response_model=TaxReturnOut)
def get_return(
    return_id: UUID,
    repo: TaxReturnRepository = Depends(get_tax_return_repo),
) -> TaxReturnOut:
    found = repo.get(return_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return _to_out(found)


@router.post("/{return_id}/compute")
def compute_return_endpoint(
    return_id: UUID,
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> dict:
    computed = compute_and_persist(return_id, return_repo=return_repo, field_repo=field_repo)
    f = computed.form_1040
    return {
        "agi": str(f.agi),
        "deduction_amount": str(f.deduction_amount),
        "taxable_income": str(f.taxable_income),
        "total_tax": str(f.total_tax),
        "refund_amount": str(f.refund_amount),
        "amount_owed": str(f.amount_owed),
    }


@router.get("/{return_id}/pdf")
def get_return_pdf(
    return_id: UUID,
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    field_repo: ExtractedFieldRepository = Depends(get_extracted_field_repo),
) -> Response:
    tax_return = return_repo.get(return_id)
    if tax_return is None:
        raise HTTPException(status_code=404, detail="Tax return not found")

    computed = compute_and_persist(return_id, return_repo=return_repo, field_repo=field_repo)
    pdf_bytes = fill_form_1040(computed, filing_status=tax_return.filing_status)

    settings = get_settings()
    blob_store = LocalFilesystemBlobStore(settings.storage_root)
    blob_store.save_generated(return_id, "form_1040.pdf", pdf_bytes)

    return Response(content=pdf_bytes, media_type="application/pdf")
