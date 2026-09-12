"""Proves the bug a user actually hit: reloading the page used to start a brand
new chat session every time, even though the conversation was already saved to
disk - so it looked like "my conversation isn't saved" when really it just was
never reloaded."""

from tests.integration.conftest import requires_api_key


@requires_api_key
def test_reopening_the_same_return_resumes_the_same_session_with_history(client, return_id):
    first = client.post("/api/chat/sessions", json={"tax_return_id": return_id})
    session_id = first.json()["id"]

    with client.stream(
        "POST",
        f"/api/chat/sessions/{session_id}/messages/stream",
        json={"text": "When is the filing deadline?"},
        timeout=30,
    ) as response:
        assert response.status_code == 200
        for _ in response.iter_lines():
            pass  # drain the stream so the message is fully persisted

    # Simulates the user reloading the page - a second "create session" call for
    # the same tax return must resume the same session, not start a fresh one.
    second = client.post("/api/chat/sessions", json={"tax_return_id": return_id})
    assert second.json()["id"] == session_id

    history = client.get(f"/api/chat/sessions/{session_id}/history").json()
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert "deadline" in history[0]["text"].lower()
    assert any(m["role"] == "assistant" for m in history)
