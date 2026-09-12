# MVP Scope

## In scope
- Form 1040, standard or itemized deduction (Schedule A - mortgage interest and cash
  charitable contributions only)
- W-2 wage income
- 1099-INT / 1099-DIV -> Schedule B when interest + dividends exceed the $1,500 threshold
- 1099-NEC / self-employment -> Schedule C + Schedule SE (business expenses supported
  as a single aggregate total, not itemized by category)
- 1099-B / capital gains -> Schedule D, **aggregate totals only**: the user (or the
  document) provides a net short-term and/or net long-term gain/loss figure, not
  individual transactions. Form 8949 (transaction-by-transaction detail) is NOT
  generated. The preferential long-term capital gains rate (0%/15%/20%) is computed
  correctly via a simplified Schedule D Tax Worksheet, but: qualified dividends are
  not modeled as eligible for the preferential rate (all dividends are treated as
  ordinary), and the rarer 25%/28% rates (unrecaptured Section 1250 gain, collectibles)
  are not implemented. A net capital loss is capped at the real $3,000/year limit
  against ordinary income; loss carryover to future years is NOT tracked (no
  persistent multi-year state).
- PDF generation only: fills the official IRS fillable PDFs, no e-filing
- Document extraction via `pypdf` (text layer + AcroForm fields) - no OCR, no scanned-image support
- Local mock auth + SQLite + local filesystem storage, behind swappable repository interfaces
- Prior-year 1040 upload -> extraction -> freeform-conversation pre-population of current year -> year-over-year comparison

## Explicitly out of scope for v1
- IRS e-file / MeF integration
- OCR or vision-based extraction of scanned/image-only documents
- Form 8949 (per-transaction capital gains detail) - see Schedule D note above
- Rental income (Schedule E)
- K-1 partnership/S-corp income
- Real identity provider (OAuth/Cognito) and real cloud storage (S3/Postgres) - designed for later swap, not built now
- Multi-user concurrency/tenancy, state tax forms, AMT
- Credits beyond what's needed to complete the core 1040 lines (EITC/CTC are stretch, not core MVP)
