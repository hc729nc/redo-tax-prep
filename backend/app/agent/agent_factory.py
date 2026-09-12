from pathlib import Path
from uuid import UUID

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.session.file_session_manager import FileSessionManager

from app.agent.persona import SYNTHIA_SYSTEM_PROMPT
from app.agent.tools import build_tools_for_return
from app.config import get_settings


def build_agent(conversation_session_id: UUID, tax_return_id: UUID) -> Agent:
    """Build a fresh Agent for one request, rehydrating history via FileSessionManager.

    Strands' SessionManager persists conversation history to disk and restores it when
    an Agent with a matching session_id is constructed - so we never hold a long-lived
    Agent in memory between requests, we just rebuild cheaply each call.
    """
    settings = get_settings()

    model = AnthropicModel(
        client_args={"api_key": settings.anthropic_api_key},
        model_id=settings.claude_model_id,
        max_tokens=1024,
    )

    sessions_dir = Path(settings.storage_root) / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_manager = FileSessionManager(
        session_id=str(conversation_session_id), storage_dir=str(sessions_dir)
    )

    return Agent(
        model=model,
        system_prompt=SYNTHIA_SYSTEM_PROMPT,
        tools=build_tools_for_return(tax_return_id),
        session_manager=session_manager,
    )
