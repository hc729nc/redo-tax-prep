from uuid import UUID, uuid4

from app.domain.entities import ExtractedField, UploadedDocument
from app.domain.enums import DocumentType, ExtractionStatus, FieldSourceType
from app.extraction.document_classifier import classify_document
from app.extraction.field_structurer import structure_fields
from app.extraction.pypdf_extractor import extract_raw_content
from app.repositories.interfaces import (
    DocumentBlobStore,
    DocumentRepository,
    ExtractedFieldRepository,
)


def upload_and_extract(
    *,
    tax_return_id: UUID,
    filename: str,
    content: bytes,
    document_repo: DocumentRepository,
    field_repo: ExtractedFieldRepository,
    blob_store: DocumentBlobStore,
) -> UploadedDocument:
    """Save the upload, classify it, extract + structure its fields, and persist
    them as unconfirmed ExtractedField rows for the user to review."""
    raw = extract_raw_content(content)
    doc_type = classify_document(raw) if raw.has_text else DocumentType.OTHER_UNRECOGNIZED

    # Create the row first so we have a real id to key the blob storage path on,
    # then backfill storage_key now that we know it.
    document = document_repo.create(
        tax_return_id=tax_return_id,
        filename=filename,
        doc_type=doc_type,
        storage_key="",
    )
    storage_key = blob_store.save(tax_return_id, document.id, content, filename)
    document_repo.set_storage_key(document.id, storage_key)

    if not raw.has_text:
        document_repo.set_extraction_status(
            document.id, ExtractionStatus.EXTRACTION_FAILED_NO_TEXT_LAYER
        )
        return document_repo.get(document.id)

    candidates = structure_fields(raw, doc_type)

    for candidate in candidates:
        field_repo.add(
            ExtractedField(
                id=uuid4(),
                tax_return_id=tax_return_id,
                document_id=document.id,
                field_name=candidate.field_name,
                value=candidate.value,
                source_type=FieldSourceType.TEXT_LAYER_SNIPPET,
                confirmed_by_user=False,
                source_page=candidate.source_page,
                source_acroform_field_name=None,
                source_text_snippet=candidate.source_text_snippet,
                source_conversation_message_id=None,
                superseded_by_field_id=None,
                created_at=document.uploaded_at,
            )
        )

    document_repo.set_extraction_status(document.id, ExtractionStatus.EXTRACTED)
    return document_repo.get(document.id)
