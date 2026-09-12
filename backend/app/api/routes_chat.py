from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.agent_factory import build_agent
from app.agent.streaming import stream_agent_response
from app.deps import get_auth_provider, get_conversation_session_repo, get_tax_return_repo
from app.repositories.interfaces import (
    AuthProvider,
    ConversationSessionRepository,
    TaxReturnRepository,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    tax_return_id: UUID


class SessionOut(BaseModel):
    id: UUID
    tax_return_id: UUID


class MessageRequest(BaseModel):
    text: str


@router.post("/sessions", response_model=SessionOut)
def create_session(
    body: CreateSessionRequest,
    request: Request,
    auth: AuthProvider = Depends(get_auth_provider),
    return_repo: TaxReturnRepository = Depends(get_tax_return_repo),
    session_repo: ConversationSessionRepository = Depends(get_conversation_session_repo),
) -> SessionOut:
    user = auth.get_current_user(request)
    tax_return = return_repo.get(body.tax_return_id)
    if tax_return is None:
        raise HTTPException(status_code=404, detail="Tax return not found")

    session = session_repo.create(tax_return_id=tax_return.id, user_id=user.id)
    return SessionOut(id=session.id, tax_return_id=session.tax_return_id)


@router.post("/sessions/{session_id}/messages/stream")
def stream_message(
    session_id: UUID,
    body: MessageRequest,
    session_repo: ConversationSessionRepository = Depends(get_conversation_session_repo),
) -> StreamingResponse:
    session = session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    session_repo.touch(session_id)
    agent = build_agent(conversation_session_id=session.id, tax_return_id=session.tax_return_id)
    return StreamingResponse(
        stream_agent_response(agent, body.text), media_type="text/event-stream"
    )
