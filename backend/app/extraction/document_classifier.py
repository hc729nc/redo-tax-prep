from app.domain.enums import DocumentType
from app.extraction.pypdf_extractor import RawExtraction

_KEYWORD_RULES: list[tuple[DocumentType, list[str]]] = [
    (DocumentType.PRIOR_YEAR_1040, ["form 1040", "u.s. individual income tax return"]),
    (DocumentType.FORM_1099_NEC, ["1099-nec", "nonemployee compensation"]),
    (DocumentType.FORM_1099_INT, ["1099-int", "interest income"]),
    (DocumentType.FORM_1099_DIV, ["1099-div", "dividends and distributions"]),
    (DocumentType.FORM_1098, ["1098", "mortgage interest statement"]),
    (DocumentType.W2, ["w-2", "wage and tax statement"]),
]


def classify_document(extraction: RawExtraction) -> DocumentType:
    """Cheap keyword heuristic over the extracted text. Good enough for the common
    case where these are genuine payroll/IRS-issued PDFs with predictable headers -
    ambiguous documents fall back to OTHER_UNRECOGNIZED rather than guessing."""
    combined_text = " ".join(p.text for p in extraction.pages).lower()

    for doc_type, keywords in _KEYWORD_RULES:
        if any(keyword in combined_text for keyword in keywords):
            return doc_type

    return DocumentType.OTHER_UNRECOGNIZED
