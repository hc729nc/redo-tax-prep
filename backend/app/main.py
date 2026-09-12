from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_prior_year import router as prior_year_router
from app.api.routes_returns import router as returns_router
from app.db.session import init_db

app = FastAPI(title="Synthia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
