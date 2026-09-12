# Synthia

A conversational AI tax-filing assistant for individual Form 1040.

Users describe their life/finances in free text; the app determines what's tax-relevant, asks for
the right documents, extracts structured data from uploads, and produces a filled, reviewable
1040 (+ schedules) PDF. See [`docs/mvp-scope.md`](docs/mvp-scope.md) for the MVP boundary.

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
