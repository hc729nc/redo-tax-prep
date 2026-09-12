# MVP Scope

## In scope
- Form 1040, standard or itemized deduction (Schedule A)
- W-2 wage income
- 1099-INT / 1099-DIV -> Schedule B when interest + dividends exceed the $1,500 threshold
- 1099-NEC / self-employment -> Schedule C + Schedule SE
- PDF generation only: fills the official IRS fillable PDFs, no e-filing
- Document extraction via `pypdf` (text layer + AcroForm fields) - no OCR, no scanned-image support
- Local mock auth + SQLite + local filesystem storage, behind swappable repository interfaces
- Prior-year 1040 upload -> extraction -> freeform-conversation pre-population of current year -> year-over-year comparison

## Explicitly out of scope for v1
- IRS e-file / MeF integration
- OCR or vision-based extraction of scanned/image-only documents
- Capital gains/losses (Schedule D, Form 8949)
- Rental income (Schedule E)
- K-1 partnership/S-corp income
- Real identity provider (OAuth/Cognito) and real cloud storage (S3/Postgres) - designed for later swap, not built now
- Multi-user concurrency/tenancy, state tax forms, AMT
- Credits beyond what's needed to complete the core 1040 lines (EITC/CTC are stretch, not core MVP)
