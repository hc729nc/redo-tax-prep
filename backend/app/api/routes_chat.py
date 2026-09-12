from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agent.agent_factory import build_agent
from app.agent.history import load_conversation_history
from app.agent.streaming import stream_agent_response
from app.api.security import require_owned_return
from app.db.session import get_db
from app.deps import get_auth_provider, get_conversation_session_repo, get_tax_return_repo
from app.repositories.interfaces import (
    AuthProvider,
    ConversationSessionRepository,
    TaxReturnRepository,
)
from app.services.rate_limit_service import RateLimitExceededError, check_and_increment_chat_usage

router = APIRouter(prefix="/api/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    tax_return_id: UUID


class SessionOut(BaseModel):
    id: UUID
    tax_return_id: UUID


class MessageRequest(BaseModel):
    text: str


class HistoryMessageOut(BaseModel):
    role: str
    text: str


@router.post("/sessions", response_model=SessionOut)
def create_or_resume_session(
    body: CreateSessionRequest,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    session_repo: ConversationSessionRepository = Depends(get_conversation_session_repo),
) -> SessionOut:
    """Reuses the most recent conversation session for this tax return if one
    exists, rather than always starting a fresh one - otherwise every page reload
    would "forget" the conversation even though it's still saved on disk."""
    user = auth.get_current_user(request)
    tax_return = require_owned_return(body.tax_return_id, user, return_repo)

    existing = session_repo.get_latest_for_return(tax_return.id)
    if existing is not None:
        return SessionOut(id=existing.id, tax_return_id=existing.tax_return_id)

    session = session_repo.create(tax_return_id=tax_return.id, user_id=user.id)
    return SessionOut(id=session.id, tax_return_id=session.tax_return_id)


@router.get("/sessions/{session_id}/history", response_model=list[HistoryMessageOut])
def get_session_history(
    session_id: UUID,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    session_repo: ConversationSessionRepository = Depends(get_conversation_session_repo),
) -> list[HistoryMessageOut]:
    user = auth.get_current_user(request)
    session = session_repo.get(session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    return [HistoryMessageOut(**m) for m in load_conversation_history(session_id)]


@router.post("/sessions/{session_id}/messages/stream")
def stream_message(
    session_id: UUID,
    body: MessageRequest,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    session_repo: ConversationSessionRepository = Depends(get_conversation_session_repo),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    user = auth.get_current_user(request)
    session = session_repo.get(session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    try:
        check_and_increment_chat_usage(db, user.id)
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=429,
            detail=f"You've reached today's limit of {e.limit} chat messages. Please try again tomorrow.",
        )

    session_repo.touch(session_id)
    agent = build_agent(conversation_session_id=session.id, tax_return_id=session.tax_return_id)
    return StreamingResponse(
        stream_agent_response(agent, body.text), media_type="text/event-stream"
    )
