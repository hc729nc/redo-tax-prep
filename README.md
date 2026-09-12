# Synthia

A conversational AI tax-filing assistant for individual Form 1040.

Users describe their life/finances in free text; the app determines what's tax-relevant, asks for
the right documents, extracts structured data from uploads, and produces a filled, reviewable
1040 (+ schedules) PDF. See [`docs/mvp-scope.md`](docs/mvp-scope.md) for the MVP boundary.

## Features
- Conversational chat interface (streaming replies) that figures out what's tax-relevant and asks
  for the right documents
- Upload W-2s, 1099-INT/DIV/NEC/B, and 1098s anytime - fields are extracted automatically with full
  provenance (source document, page, and exact text snippet), and you confirm or correct each one
- Form 1040 with standard or itemized deduction (Schedule A - mortgage interest & cash charitable
  gifts), wages, interest/dividends (Schedule B), self-employment income (Schedule C + SE), and
  capital gains/losses (Schedule D, aggregate totals - see scope doc for what that means)
- Ask "where did this come from?" at any time and get the exact source, document, and page
- Upload a prior-year return to pre-populate this year's answers (as drafts you confirm, never
  silently carried over) and get a plain-language year-over-year comparison
- Generates a real, filled IRS Form 1040 (+ attached schedules) as a downloadable PDF

## Stack
- **Backend**: Python, FastAPI, SQLAlchemy (SQLite for now), `pypdf` for document extraction/PDF
  generation, [Strands Agents SDK](https://strandsagents.com/) with the Anthropic model provider
  (Claude API) for the conversational agent.
- **Frontend**: React + TypeScript (Vite).

## Development

### Backend
```
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
cp .env.example .env          # fill in ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```
cd frontend
npm install
npm run dev
```

## Tax math

All dollar calculations are performed by a deterministic Python engine in
`backend/app/taxcalc/` — the Claude-powered agent never computes tax amounts itself, only calls
into this engine and reports its output.
