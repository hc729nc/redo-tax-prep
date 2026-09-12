from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class RawExtraction:
    acroform_fields: dict[str, str]
    pages: list[ExtractedPage]
    has_text: bool


def extract_raw_content(pdf_bytes: bytes) -> RawExtraction:
    """Pull whatever structured signal pypdf can get from an uploaded PDF: AcroForm
    field values (if the PDF is a genuine fillable form) and the text layer per page
    (as a fallback/cross-check). Returns has_text=False if both are empty - this is
    the signal for 'scanned image, no text layer' (pypdf does no OCR), which callers
    must surface to the user rather than silently failing.
    """
    from io import BytesIO

    reader = PdfReader(BytesIO(pdf_bytes))

    acroform_fields: dict[str, str] = {}
    fields = reader.get_fields()
    if fields:
        for name, f in fields.items():
            value = f.get("/V")
            if value:
                acroform_fields[name] = str(value)

    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(ExtractedPage(page_number=i + 1, text=text))

    has_text = bool(acroform_fields) or any(p.text.strip() for p in pages)

    return RawExtraction(acroform_fields=acroform_fields, pages=pages, has_text=has_text)
