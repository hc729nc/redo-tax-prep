import json
from pathlib import Path
from uuid import UUID

from app.config import get_settings


def load_conversation_history(conversation_session_id: UUID) -> list[dict]:
    """Read back the plain-text turns of a conversation from Strands'
    FileSessionManager storage (see agent_factory.py) - used to let the frontend
    re-display history after a page reload, since we never keep an Agent alive
    in memory between requests.

    Tool-call/tool-result-only messages (no "text" content block) are skipped -
    those are the agent's internal tool-use mechanics, not something to show as
    a chat bubble.
    """
    settings = get_settings()
    messages_dir = (
        Path(settings.storage_root)
        / "sessions"
        / f"session_{conversation_session_id}"
        / "agents"
        / "agent_default"
        / "messages"
    )
    if not messages_dir.is_dir():
        return []

    def _message_index(path: Path) -> int:
        return int(path.stem.removeprefix("message_"))

    message_files = sorted(messages_dir.glob("message_*.json"), key=_message_index)

    history = []
    for path in message_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        message = data["message"]
        text = "".join(block["text"] for block in message["content"] if "text" in block)
        if not text:
            continue
        history.append({"role": message["role"], "text": text})
    return history
