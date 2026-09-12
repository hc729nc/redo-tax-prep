from dataclasses import dataclass

from anthropic import Anthropic

from app.config import get_settings
from app.domain.enums import DocumentType
from app.extraction.pypdf_extractor import RawExtraction

# Canonical field names the rest of the system understands. Kept small and scoped to
# the MVP's supported document types - see docs/mvp-scope.md.
CANONICAL_FIELDS_BY_DOC_TYPE: dict[DocumentType, list[str]] = {
    DocumentType.W2: ["w2.box1_wages", "w2.box2_federal_withholding"],
    DocumentType.FORM_1099_INT: ["1099_int.box1_interest"],
    DocumentType.FORM_1099_DIV: ["1099_div.box1a_ordinary_dividends"],
    DocumentType.FORM_1099_NEC: ["1099_nec.box1_nonemployee_compensation"],
    DocumentType.FORM_1098: ["schedule_a.mortgage_interest"],
    DocumentType.FORM_1099_B: [
        "1099_b.net_short_term_gain_loss",
        "1099_b.net_long_term_gain_loss",
    ],
    DocumentType.PRIOR_YEAR_1040: [
        "prior_year.wages",
        "prior_year.taxable_interest",
        "prior_year.ordinary_dividends",
        "prior_year.agi",
        "prior_year.total_tax",
        "prior_year.refund_amount",
        "prior_year.amount_owed",
    ],
}

# Extra context for fields whose canonical name alone doesn't say which form line
# to look for - helps Claude locate the right box instead of guessing from the name.
_FIELD_HINTS: dict[str, str] = {
    "schedule_a.mortgage_interest": "Form 1098 Box 1 (mortgage interest received from payer)",
    "1099_b.net_short_term_gain_loss": (
        "The TOTAL/aggregate net short-term gain or loss, usually in a 'Summary of "
        "Proceeds' section (e.g. 'Total Short-Term'). Only record if there's a clear "
        "aggregate total - do not sum individual transaction rows yourself."
    ),
    "1099_b.net_long_term_gain_loss": (
        "The TOTAL/aggregate net long-term gain or loss, usually in a 'Summary of "
        "Proceeds' section (e.g. 'Total Long-Term'). Only record if there's a clear "
        "aggregate total - do not sum individual transaction rows yourself."
    ),
    "prior_year.wages": "Form 1040 line 1z (total wages)",
    "prior_year.taxable_interest": "Form 1040 line 2b (taxable interest)",
    "prior_year.ordinary_dividends": "Form 1040 line 3b (ordinary dividends)",
    "prior_year.agi": "Form 1040 line 11 (adjusted gross income)",
    "prior_year.total_tax": "Form 1040 line 24 (total tax)",
    "prior_year.refund_amount": "Form 1040 line 34 (overpayment/refund)",
    "prior_year.amount_owed": "Form 1040 line 37 (amount you owe)",
}

_RECORD_FIELDS_TOOL = {
    "name": "record_extracted_fields",
    "description": "Record the canonical tax fields found in this document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_name": {"type": "string", "description": "Canonical field name from the allowed list"},
                        "value": {"type": "string", "description": "The dollar amount, as a plain number string"},
                        "source_page": {"type": "integer", "description": "1-indexed page this value was found on"},
                        "source_text_snippet": {
                            "type": "string",
                            "description": "The raw text snippet this value was read from",
                        },
                    },
                    "required": ["field_name", "value", "source_page"],
                },
            }
        },
        "required": ["fields"],
    },
}


@dataclass
class StructuredFieldCandidate:
    field_name: str
    value: str
    source_page: int
    source_text_snippet: str | None


def structure_fields(extraction: RawExtraction, document_type: DocumentType) -> list[StructuredFieldCandidate]:
    """Ask Claude to map raw AcroForm values / page text onto our canonical field
    names, carrying forward the page/snippet so each value keeps its provenance."""
    allowed_fields = CANONICAL_FIELDS_BY_DOC_TYPE.get(document_type)
    if not allowed_fields:
        return []

    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)

    pages_text = "\n\n".join(f"--- Page {p.page_number} ---\n{p.text}" for p in extraction.pages)
    acroform_text = "\n".join(f"{k}: {v}" for k, v in extraction.acroform_fields.items())
    field_descriptions = "\n".join(
        f"- {name}" + (f" ({_FIELD_HINTS[name]})" if name in _FIELD_HINTS else "")
        for name in allowed_fields
    )

    prompt = (
        f"This is a {document_type.value} tax document. Extract only these canonical "
        f"fields if present:\n{field_descriptions}\n\n"
        f"AcroForm field values found:\n{acroform_text or '(none)'}\n\n"
        f"Page text:\n{pages_text}\n\n"
        "For each field you find, record its value, the page number, and the exact "
        "text snippet it came from. Only record a field if you are confident in the "
        "value - do not guess."
    )

    response = client.messages.create(
        model=settings.claude_model_id,
        max_tokens=1024,
        tools=[_RECORD_FIELDS_TOOL],
        tool_choice={"type": "tool", "name": "record_extracted_fields"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_extracted_fields":
            raw_fields = block.input.get("fields", [])
            return [
                StructuredFieldCandidate(
                    field_name=f["field_name"],
                    value=f["value"],
                    source_page=f["source_page"],
                    source_text_snippet=f.get("source_text_snippet"),
                )
                for f in raw_fields
                if f["field_name"] in allowed_fields
            ]

    return []
