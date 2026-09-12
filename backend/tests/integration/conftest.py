import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.deps import get_blob_store
from app.main import app
from app.repositories.filesystem_blob_store import LocalFilesystemBlobStore

requires_api_key = pytest.mark.skipif(
    not get_settings().anthropic_api_key,
    reason="ANTHROPIC_API_KEY not set - these tests call the real Claude API",
)


def _install_isolated_overrides(tmp_path, monkeypatch):
    """Point the app at an isolated temp SQLite DB and upload directory - never
    touches the real dev database or uploads folder."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    from app.db import models  # noqa: F401  (register models on Base before create_all)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_blob_store():
        return LocalFilesystemBlobStore(str(tmp_path / "uploads"))

    # Agent tools call SessionLocal() directly (they run outside FastAPI's Depends),
    # so patch the module-level SessionLocal too - otherwise they'd hit the real db.
    monkeypatch.setattr("app.db.session.SessionLocal", TestSessionLocal)
    monkeypatch.setattr("app.agent.tools.SessionLocal", TestSessionLocal)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_blob_store] = override_get_blob_store


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Sync TestClient for correctness checks, pre-authenticated as a fresh test
    user (TestClient persists cookies across requests like a browser, so every
    subsequent call in a test is already logged in). NOT suitable for verifying
    real incremental streaming timing - its blocking portal (and httpx's
    ASGITransport, also tried) both drain the whole async response before handing
    it back, even for a genuinely-streaming app. See test_chat_streaming_smoke.py,
    which uses a real uvicorn subprocess instead for that specific check."""
    _install_isolated_overrides(tmp_path, monkeypatch)
    with TestClient(app) as test_client:
        signup_resp = test_client.post(
            "/api/auth/signup",
            json={"email": "test-user@example.com", "password": "testpassword123", "display_name": "Test User"},
        )
        assert signup_resp.status_code == 200, signup_resp.text
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def return_id(client):
    resp = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    assert resp.status_code == 200
    return resp.json()["id"]
