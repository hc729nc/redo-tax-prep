"""Targets the known strands-agents/FastAPI streaming regression (see M1 in the
project plan): a prior version silently buffered the whole reply into one chunk
instead of streaming incrementally. This test fails loudly if that regresses.

Deliberately spins up a REAL uvicorn subprocess rather than using any in-process
ASGI test harness: both httpx's sync TestClient (blocking portal) and its async
ASGITransport were tried and both buffer the whole response before handing it to
the caller, even when the app is genuinely streaming - they're not a faithful
stand-in for a real server process for this specific check. A real subprocess,
hit over a real socket, is what actually reproduces the regression class this
test exists to catch.
"""

import os
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

import httpx
import pytest

from app.config import get_settings
from tests.integration.conftest import requires_api_key

BACKEND_ROOT = Path(__file__).parent.parent.parent


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server(tmp_path):
    port = _free_port()
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'live_test.db'}",
        "STORAGE_ROOT": str(tmp_path / "uploads"),
        "ANTHROPIC_API_KEY": get_settings().anthropic_api_key,
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=str(BACKEND_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                if httpx.get(f"{base_url}/api/health", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.2)
        else:
            proc.terminate()
            raise RuntimeError("Live test server did not become healthy in time")

        yield base_url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@requires_api_key
def test_chat_reply_streams_incrementally_not_as_one_blob(live_server):
    return_resp = httpx.post(
        f"{live_server}/api/returns", json={"tax_year": 2025, "filing_status": "single"}
    )
    return_id = return_resp.json()["id"]

    session_resp = httpx.post(
        f"{live_server}/api/chat/sessions", json={"tax_return_id": return_id}
    )
    session_id = session_resp.json()["id"]

    chunk_arrival_times = []
    start = time.monotonic()

    # A deliberately open-ended prompt - short/terse replies can stream in just a
    # couple of chunks, which makes the "incremental" check flaky regardless of
    # whether streaming actually works, so ask for enough text to get a robust
    # sample of chunks.
    prompt = (
        "In 2-3 sentences, explain what you'll help me do with my taxes this year, "
        "and mention when the filing deadline is."
    )
    with httpx.stream(
        "POST",
        f"{live_server}/api/chat/sessions/{session_id}/messages/stream",
        json={"text": prompt},
        timeout=30,
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data:"):
                chunk_arrival_times.append(time.monotonic() - start)

    assert len(chunk_arrival_times) >= 10, (
        "Expected many incremental chunks for a multi-sentence reply, got "
        f"{len(chunk_arrival_times)} - streaming may be buffering into one blob again"
    )
    # If everything arrived in one blob, every timestamp would be ~identical (all
    # captured in the same instant after the full response completed).
    spread = chunk_arrival_times[-1] - chunk_arrival_times[0]
    assert spread > 0.2, f"All chunks arrived within {spread:.3f}s - looks non-incremental"
