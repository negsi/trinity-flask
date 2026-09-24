"""Agent SSE Real-Time Streaming Endpoints."""

import json
from typing import Generator
from flask import Blueprint, request, Response, stream_with_context
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.messaging import MessagingService
from app.services.agent.agent_orchestrator import AgentOrchestrator
from app.services.agent.constants import PROTOCOL_THOUGHT
from app.services.infrastructure.security_context import SecurityContextService
from app.domain.errors import ValidationError

bp = Blueprint("streaming", __name__, url_prefix="/api/v1/agents/<agent_id>")


@bp.route("/stream", methods=["POST"])
@inject
def stream_agent_execution(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
    orchestrator: AgentOrchestrator = Provide[Container.agent_orchestrator],
    security_context: SecurityContextService = Provide[
        Container.security_context_service
    ],
):
    """
    Persists an incoming user message and streams the agent's real-time 
    LLM execution via Server-Sent Events (SSE).
    """
    # 1. Validate agent existence
    agent = agent_service.get_agent(agent_id)

    # 2. Extract payload and file attachments
    if request.is_json:
        payload = request.get_json() or {}
        files = []
    else:
        payload = request.form.to_dict()
        files = (
            request.files.getlist("files")
            or request.files.getlist("files[]")
            or request.files.getlist("file")
        )

    text = payload.get("text") or payload.get("message") or ""
    conversation_id = payload.get("conversation_id")

    if not text.strip() and not files:
        raise ValidationError("EMPTY_MESSAGE_PAYLOAD")

    # 3. Retrieve security actor context
    current_actor = security_context.get_current_actor()

    # 4. Persist user message before initializing the stream
    saved_message = messaging_service.send_message(
        conversation_id=conversation_id,
        sender_id=current_actor["id"],
        sender_type=current_actor["type"],
        sender_name=current_actor["name"],
        text=text,
        recipient_id=agent_id,
        files=files,
    )

    resolved_conversation_id = saved_message.conversation_id

    # 5. Initialize SSE execution stream
    raw_stream = orchestrator.stream_agent_response(
        user_text=text,
        conversation_id=resolved_conversation_id,
        agent_id=agent_id,
        agent_name=agent.name,
        user_id=current_actor["id"],
    )

    def sse_formatter(generator: Generator[str, None, None]) -> Generator[str, None, None]:
        """Format raw text chunks into W3C-compliant Server-Sent Events (SSE)."""
        # Always comment source code in English
        meta_payload = {
            "conversation_id": resolved_conversation_id,
            "user_message_id": saved_message.id,
        }
        yield f"data: {json.dumps({'type': 'meta', 'data': meta_payload})}\n\n"

        try:
            for chunk in generator:
                if not chunk:
                    continue

                # 1. Handle explicit PROTOCOL_THOUGHT markers
                if PROTOCOL_THOUGHT in chunk:
                    idx = chunk.find(PROTOCOL_THOUGHT)
                    thought_content = chunk[idx + len(PROTOCOL_THOUGHT):].strip()
                    try:
                        parsed = json.loads(thought_content)
                        delta = parsed.get("content", "") or parsed.get("delta", "")
                    except Exception:
                        delta = thought_content
                    thought_event = {"type": "thought", "content": delta, "delta": delta}
                    yield f"data: {json.dumps(thought_event)}\n\n"
                    continue

                # 2. Pass through pre-formatted JSON thought strings directly
                stripped = chunk.strip()
                if stripped.startswith('{"type": "thought"') or stripped.startswith('{"type":"thought"'):
                    yield f"data: {stripped}\n\n"
                    continue

                # 3. Format standard LLM text chunks as structured JSON SSE payloads
                content_event = {
                    "type": "content",
                    "delta": chunk,
                    "content": chunk,
                }
                yield f"data: {json.dumps(content_event)}\n\n"

        except StopIteration:
            pass

    return Response(
        stream_with_context(sse_formatter(raw_stream)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )