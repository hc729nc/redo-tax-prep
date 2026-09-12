"""Real accounts + the cross-user ownership fix. These exist because a public
deployment with shared mock auth would mean every visitor sees the same tax data -
these tests prove that's no longer true."""

from fastapi.testclient import TestClient

from app.main import app


def test_signup_creates_account_and_logs_in(client):
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "test-user@example.com"


def test_duplicate_signup_email_rejected(client):
    resp = client.post(
        "/api/auth/signup",
        json={"email": "test-user@example.com", "password": "anotherpassword", "display_name": "Dup"},
    )
    assert resp.status_code == 409


def test_login_with_wrong_password_rejected(client):
    resp = client.post(
        "/api/auth/login", json={"email": "test-user@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401


def test_logout_clears_session(client):
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_unauthenticated_requests_are_rejected(client):
    # A fresh TestClient sharing the same app (and so the same isolated test DB
    # and dependency overrides) but with no login at all.
    anon = TestClient(app)
    assert anon.get("/api/returns").status_code == 401


def _second_logged_in_client() -> TestClient:
    other = TestClient(app)
    resp = other.post(
        "/api/auth/signup",
        json={"email": "other-user@example.com", "password": "otherpassword123", "display_name": "Other User"},
    )
    assert resp.status_code == 200, resp.text
    return other


def test_user_cannot_read_another_users_return(client):
    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    other = _second_logged_in_client()
    resp = other.get(f"/api/returns/{my_return_id}")
    assert resp.status_code == 404


def test_user_cannot_compute_or_download_pdf_for_another_users_return(client):
    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    other = _second_logged_in_client()
    assert other.post(f"/api/returns/{my_return_id}/compute").status_code == 404
    assert other.get(f"/api/returns/{my_return_id}/pdf").status_code == 404


def test_user_cannot_list_or_upload_documents_for_another_users_return(client):
    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    other = _second_logged_in_client()
    assert other.get(f"/api/documents?tax_return_id={my_return_id}").status_code == 404
    assert other.get(f"/api/documents/fields?tax_return_id={my_return_id}").status_code == 404


def test_user_cannot_confirm_another_users_extracted_field(client, monkeypatch):
    # Plant a field directly (bypassing real extraction, which needs the live
    # Claude API) so this test doesn't need ANTHROPIC_API_KEY.
    from datetime import datetime, timezone
    from uuid import uuid4

    from app.db.session import SessionLocal
    from app.domain.entities import ExtractedField
    from app.domain.enums import FieldSourceType
    from app.repositories.sqlite_impl import SqlAlchemyExtractedFieldRepository

    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    db = SessionLocal()
    field_repo = SqlAlchemyExtractedFieldRepository(db)
    field = field_repo.add(
        ExtractedField(
            id=uuid4(),
            tax_return_id=my_return_id,
            document_id=None,
            field_name="w2.box1_wages",
            value="50000",
            source_type=FieldSourceType.CONVERSATION_DERIVED,
            confirmed_by_user=False,
            source_page=None,
            source_acroform_field_name=None,
            source_text_snippet=None,
            source_conversation_message_id=None,
            superseded_by_field_id=None,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.close()

    other = _second_logged_in_client()
    resp = other.patch(f"/api/documents/fields/{field.id}/confirm")
    assert resp.status_code == 404


def test_user_cannot_create_chat_session_for_another_users_return(client):
    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    other = _second_logged_in_client()
    resp = other.post("/api/chat/sessions", json={"tax_return_id": my_return_id})
    assert resp.status_code == 404


def test_user_cannot_upload_prior_year_for_another_users_return(client):
    mine = client.post("/api/returns", json={"tax_year": 2025, "filing_status": "single"})
    my_return_id = mine.json()["id"]

    other = _second_logged_in_client()
    resp = other.get(f"/api/prior-year/compare?current_return_id={my_return_id}")
    assert resp.status_code == 404
