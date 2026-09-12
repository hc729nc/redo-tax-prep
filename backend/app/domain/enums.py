from enum import Enum


class FilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class ReturnStatus(str, Enum):
    DRAFT = "draft"
    COMPUTED = "computed"
    FINALIZED = "finalized"


class DocumentType(str, Enum):
    W2 = "w2"
    FORM_1099_INT = "1099_int"
    FORM_1099_DIV = "1099_div"
    FORM_1099_NEC = "1099_nec"
    FORM_1098 = "1098"
    FORM_1099_B = "1099_b"
    PRIOR_YEAR_1040 = "prior_year_1040"
    OTHER_UNRECOGNIZED = "other_unrecognized"


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    EXTRACTION_FAILED_NO_TEXT_LAYER = "extraction_failed_no_text_layer"
    NEEDS_REVIEW = "needs_review"


class FieldSourceType(str, Enum):
    ACROFORM_FIELD = "acroform_field"
    TEXT_LAYER_SNIPPET = "text_layer_snippet"
    USER_MANUAL_ENTRY = "user_manual_entry"
    CONVERSATION_DERIVED = "conversation_derived"
