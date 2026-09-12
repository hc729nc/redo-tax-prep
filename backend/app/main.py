from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_prior_year import router as prior_year_router
from app.api.routes_returns import router as returns_router
from app.config import get_settings
from app.db.session import init_db

app = FastAPI(title="Synthia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(auth_router)
app.include_router(returns_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(prior_year_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# In a single-service deployment, the built frontend lives alongside the backend
# and is served directly from here - no separate frontend host, no CORS to manage.
# Local dev is unaffected: the frontend is normally run via `npm run dev`
# (Vite) instead, and this directory won't exist, so nothing mounts.
_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
