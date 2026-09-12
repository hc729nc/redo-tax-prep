import json
from collections.abc import AsyncIterator

from strands import Agent


async def stream_agent_response(agent: Agent, prompt: str) -> AsyncIterator[str]:
    """Adapt agent.stream_async() to Server-Sent Events for FastAPI's StreamingResponse.

    Emits one `data:` line per text token as it streams in, so the chat UI can render
    incrementally rather than waiting for the full reply.
    """
    async for event in agent.stream_async(prompt):
        text = event.get("data")
        if isinstance(text, str) and text:
            yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
