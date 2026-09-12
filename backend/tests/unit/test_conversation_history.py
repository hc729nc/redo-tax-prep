import json
from uuid import uuid4

from app.agent.history import load_conversation_history


def _write_message(messages_dir, index, role, content):
    messages_dir.mkdir(parents=True, exist_ok=True)
    path = messages_dir / f"message_{index}.json"
    path.write_text(
        json.dumps(
            {
                "message": {"role": role, "content": content},
                "message_id": index,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )


def test_loads_text_turns_in_order(tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "storage_root", str(tmp_path))
    session_id = uuid4()
    messages_dir = tmp_path / "sessions" / f"session_{session_id}" / "agents" / "agent_default" / "messages"

    _write_message(messages_dir, 0, "user", [{"text": "Hi there"}])
    _write_message(messages_dir, 1, "assistant", [{"text": "Hello! "}, {"toolUse": {"name": "get_filing_deadline"}}])
    _write_message(messages_dir, 2, "user", [{"toolResult": {"status": "success"}}])  # tool result, not real text
    _write_message(messages_dir, 3, "assistant", [{"text": "The deadline is April 15."}])
    # message_10 should sort AFTER message_2, not between message_1 and message_2 (string sort would get this wrong)
    _write_message(messages_dir, 10, "user", [{"text": "tenth message"}])

    history = load_conversation_history(session_id)

    assert history == [
        {"role": "user", "text": "Hi there"},
        {"role": "assistant", "text": "Hello! "},
        {"role": "assistant", "text": "The deadline is April 15."},
        {"role": "user", "text": "tenth message"},
    ]


def test_returns_empty_list_for_unknown_session(tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "storage_root", str(tmp_path))
    assert load_conversation_history(uuid4()) == []
