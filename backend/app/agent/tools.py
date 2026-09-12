from datetime import date
from decimal import Decimal
from uuid import UUID

from strands import tool

from app.config import get_settings
from app.db.session import SessionLocal
from app.domain.enums import FieldSourceType
from app.repositories.filesystem_blob_store import LocalFilesystemBlobStore
from app.repositories.sqlite_impl import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyExtractedFieldRepository,
    SqlAlchemyTaxReturnRepository,
)
from app.services.prior_year_service import get_comparison
from app.services.return_service import compute_and_persist


@tool
def get_filing_deadline() -> dict:
    """Get the federal filing deadline for the tax year this return covers.

    Returns the tax year and the Form 1040 due date (April 15 of the following year,
    or the next business day if that falls on a weekend/holiday - simplified here to
    the standard date).
    """
    tax_year = get_settings().tax_year
    deadline = date(tax_year + 1, 4, 15)
    return {"tax_year": tax_year, "deadline": deadline.isoformat()}


def build_tools_for_return(tax_return_id: UUID) -> list:
    """Build the set of tools bound to one tax return, for use by agent_factory.

    Each tool opens its own short-lived DB session since Strands tools run outside
    FastAPI's request-scoped Depends - there is no request to hang a session off of.
    """

    @tool
    def list_missing_documents() -> dict:
        """Check what's been confirmed so far versus what hasn't been provided yet,
        across every income type this return can handle (W-2, 1099-INT, 1099-DIV,
        1099-NEC). Call this before asking the user for a document, so you don't
        re-ask for something already uploaded and confirmed. Note: 'not_yet_provided'
        does NOT mean required - only ask about a type there if the conversation
        suggests it might apply to this person (e.g. they mentioned freelance work
        but no 1099-NEC has been confirmed)."""
        db = SessionLocal()
        try:
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            confirmed = field_repo.list_for_return(tax_return_id, confirmed_only=True)
            confirmed_names = {f.field_name for f in confirmed}

            doc_types = {
                "W-2 (wages and federal withholding)": "w2.box1_wages",
                "1099-INT (interest income)": "1099_int.box1_interest",
                "1099-DIV (dividend income)": "1099_div.box1a_ordinary_dividends",
                "1099-NEC (self-employment/freelance income)": "1099_nec.box1_nonemployee_compensation",
                "1098 (mortgage interest, if itemizing)": "schedule_a.mortgage_interest",
            }
            not_yet_provided = [
                label for label, field_name in doc_types.items() if field_name not in confirmed_names
            ]
            provided = [label for label in doc_types if label not in not_yet_provided]

            return {"provided": provided, "not_yet_provided": not_yet_provided}
        finally:
            db.close()

    @tool
    def list_pending_fields() -> dict:
        """List fields extracted from uploaded documents that are awaiting the
        user's confirmation, with their source document/page for provenance."""
        db = SessionLocal()
        try:
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            all_fields = field_repo.list_for_return(tax_return_id)
            pending = [f for f in all_fields if not f.confirmed_by_user]
            return {
                "pending_fields": [
                    {
                        "field_id": str(f.id),
                        "field_name": f.field_name,
                        "value": f.value,
                        "source_page": f.source_page,
                    }
                    for f in pending
                ]
            }
        finally:
            db.close()

    @tool
    def confirm_or_correct_field(field_id: str, new_value: str | None = None) -> dict:
        """Confirm an extracted field as correct, or correct its value if the user
        says it's wrong. Pass new_value only when correcting; omit it to confirm
        as-is."""
        db = SessionLocal()
        try:
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            if new_value is not None:
                updated = field_repo.correct(UUID(field_id), new_value)
                return {"field_id": str(updated.id), "value": updated.value, "status": "corrected"}
            field_repo.confirm(UUID(field_id))
            return {"field_id": field_id, "status": "confirmed"}
        finally:
            db.close()

    @tool
    def record_extracted_field(field_name: str, value: str, confirmed: bool = True) -> dict:
        """Record a tax-relevant field the user told you directly in conversation
        (not from an uploaded document) - e.g. they mention wages or interest amounts
        verbally. Allowed field_name values: w2.box1_wages, w2.box2_federal_withholding,
        1099_int.box1_interest, 1099_div.box1a_ordinary_dividends,
        1099_nec.box1_nonemployee_compensation, 1099_nec.total_expenses (business
        expenses against self-employment income), schedule_a.mortgage_interest,
        schedule_a.charitable_contributions (cash gifts only - only worth itemizing
        if these exceed the standard deduction; mention that tradeoff if relevant).

        Pass confirmed=False only when proposing a DRAFT value carried forward from
        last year's return (via lookup_prior_year_field) - that still needs the
        user's explicit confirmation since amounts change year to year. Anything the
        user states directly themselves should be confirmed=True (the default)."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from app.domain.entities import ExtractedField

        db = SessionLocal()
        try:
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            created = field_repo.add(
                ExtractedField(
                    id=uuid4(),
                    tax_return_id=tax_return_id,
                    document_id=None,
                    field_name=field_name,
                    value=value,
                    source_type=FieldSourceType.CONVERSATION_DERIVED,
                    confirmed_by_user=confirmed,
                    source_page=None,
                    source_acroform_field_name=None,
                    source_text_snippet="Carried forward from last year's return, pending confirmation"
                    if not confirmed
                    else None,
                    source_conversation_message_id=None,
                    superseded_by_field_id=None,
                    created_at=datetime.now(timezone.utc),
                )
            )
            return {"field_id": str(created.id), "status": "recorded", "confirmed": confirmed}
        finally:
            db.close()

    @tool
    def lookup_prior_year_field(field_name: str) -> dict:
        """Look up a value from the user's prior-year return, if they've uploaded
        one. field_name must be one of: prior_year.wages, prior_year.taxable_interest,
        prior_year.ordinary_dividends, prior_year.agi, prior_year.total_tax,
        prior_year.refund_amount, prior_year.amount_owed. Use this when the user
        implies their situation is similar to last year (e.g. "same as last year"),
        then consider proposing it as a draft via record_extracted_field with
        confirmed=False - never treat a prior-year value as confirmed for this
        year without the user explicitly agreeing."""
        db = SessionLocal()
        try:
            return_repo = SqlAlchemyTaxReturnRepository(db)
            field_repo = SqlAlchemyExtractedFieldRepository(db)

            current = return_repo.get(tax_return_id)
            if current is None:
                return {"found": False}
            prior = return_repo.find_by_year(current.user_id, current.tax_year - 1, is_prior_year=True)
            if prior is None:
                return {"found": False, "reason": "No prior-year return uploaded yet."}

            matching = [
                f for f in field_repo.list_for_return(prior.id, confirmed_only=True)
                if f.field_name == field_name
            ]
            if not matching:
                return {"found": False, "reason": "That field wasn't found on the prior-year return."}

            total = sum((Decimal(f.value) for f in matching), Decimal("0"))
            return {"found": True, "value": str(total), "prior_tax_year": prior.tax_year}
        finally:
            db.close()

    @tool
    def summarize_year_over_year_changes() -> dict:
        """Get the structured comparison between this year's computed return and
        the confirmed figures from the prior-year return, if one has been uploaded.
        Use this to narrate a year-over-year summary when the user asks how their
        taxes changed, or after generating a comparison."""
        db = SessionLocal()
        try:
            return_repo = SqlAlchemyTaxReturnRepository(db)
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            return get_comparison(tax_return_id, return_repo=return_repo, field_repo=field_repo)
        finally:
            db.close()

    @tool
    def explain_field_provenance(field_name: str) -> dict:
        """Explain where a field's value came from - which document(s) (with page
        number and the exact text/value read from it) or that the user told you
        directly in conversation. If multiple documents contributed to the same
        field (e.g. two W-2s), every contributing source is listed along with the
        total. Use this whenever the user asks "where did this come from" or
        similar about a number on their return."""
        db = SessionLocal()
        try:
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            document_repo = SqlAlchemyDocumentRepository(db)
            all_fields = field_repo.list_for_return(tax_return_id)
            matching = [f for f in all_fields if f.field_name == field_name]

            if not matching:
                return {"field_name": field_name, "sources": [], "note": "No value recorded for this field yet."}

            sources = []
            total = Decimal("0")
            for f in matching:
                try:
                    total += Decimal(f.value)
                except Exception:
                    pass
                if f.source_type == FieldSourceType.CONVERSATION_DERIVED:
                    sources.append({"origin": "conversation", "value": f.value, "confirmed": f.confirmed_by_user})
                else:
                    doc = document_repo.get(f.document_id) if f.document_id else None
                    sources.append(
                        {
                            "origin": "document",
                            "document_filename": doc.original_filename if doc else None,
                            "page": f.source_page,
                            "text_snippet": f.source_text_snippet,
                            "value": f.value,
                            "confirmed": f.confirmed_by_user,
                        }
                    )

            return {"field_name": field_name, "sources": sources, "total": str(total)}
        finally:
            db.close()

    @tool
    def compute_return() -> dict:
        """Compute the tax return from all confirmed fields so far. This is the ONLY
        way to get dollar amounts for this return - never state a tax number you
        haven't gotten from this tool's output."""
        db = SessionLocal()
        try:
            return_repo = SqlAlchemyTaxReturnRepository(db)
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            computed = compute_and_persist(tax_return_id, return_repo=return_repo, field_repo=field_repo)
            f = computed.form_1040
            return {
                "agi": str(f.agi),
                "deduction_amount": str(f.deduction_amount),
                "taxable_income": str(f.taxable_income),
                "total_tax": str(f.total_tax),
                "refund_amount": str(f.refund_amount),
                "amount_owed": str(f.amount_owed),
            }
        finally:
            db.close()

    @tool
    def generate_return_pdf() -> dict:
        """Generate the filled Form 1040 PDF from the most recent computed return.
        Call compute_return first if the return hasn't been computed yet."""
        from app.pdfgen.filler import fill_form_1040

        db = SessionLocal()
        try:
            return_repo = SqlAlchemyTaxReturnRepository(db)
            field_repo = SqlAlchemyExtractedFieldRepository(db)
            settings = get_settings()

            tax_return = return_repo.get(tax_return_id)
            computed = compute_and_persist(tax_return_id, return_repo=return_repo, field_repo=field_repo)
            pdf_bytes = fill_form_1040(computed, filing_status=tax_return.filing_status)

            blob_store = LocalFilesystemBlobStore(settings.storage_root)
            storage_key = blob_store.save_generated(tax_return_id, "form_1040.pdf", pdf_bytes)
            return {"status": "generated", "storage_key": storage_key}
        finally:
            db.close()

    return [
        get_filing_deadline,
        list_missing_documents,
        list_pending_fields,
        confirm_or_correct_field,
        record_extracted_field,
        explain_field_provenance,
        lookup_prior_year_field,
        summarize_year_over_year_changes,
        compute_return,
        generate_return_pdf,
    ]
