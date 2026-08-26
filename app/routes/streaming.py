"""Agent SSE Real-Time Streaming Endpoints."""

import json
from typing import Generator
from flask import Blueprint, request, Response, stream_with_context
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.messaging import MessagingService
from app.services.agent.agent_orchestrator import AgentOrchestrator
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
        meta_payload = {
            "conversation_id": resolved_conversation_id,
            "user_message_id": saved_message.id,
        }
        yield f"data: {json.dumps({'type': 'meta', 'data': meta_payload})}\n\n"

        try:
            while True:
                chunk = next(generator)
                if not chunk:
                    continue
                lines = chunk.split("\n")
                for line in lines:
                    yield f"data: {line}\n"
                yield "\n"
        except StopIteration:
            pass

    return Response(
        stream_with_context(sse_formatter(raw_stream)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
