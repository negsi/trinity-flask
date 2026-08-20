"""
Chat and Execution HTTP API Routes.

Exposes endpoints for messaging operations, conversation histories,
and real-time streaming LLM agent responses via Server-Sent Events (SSE).
"""

import os
from typing import Generator
from flask import (
    Blueprint,
    jsonify,
    Response,
    request,
    stream_with_context,
    send_from_directory,
    current_app,
    abort,
)
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.messaging import MessagingService
from app.services.agent import AgentOrchestrator
from app.services.agent import AgentService
from app.services.infrastructure import SecurityContextService
from app.routes.schemas import SendMessageRequest
from app.domain.errors import ValidationError

chat_bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


@chat_bp.route("/messages", methods=["POST"])
@inject
def send_message(
    messaging_service: MessagingService = Provide[Container.messaging_service],
    security_context: SecurityContextService = Provide[
        Container.security_context_service
    ],
):
    """
    Persist a chat message in a conversation with optional file attachments.

    Accepts both 'application/json' and 'multipart/form-data' payloads.
    """
    current_actor = security_context.get_current_actor()

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

    dto = SendMessageRequest(**payload)

    saved_message = messaging_service.send_message(
        conversation_id=dto.conversation_id,
        sender_id=current_actor["id"],
        sender_type=current_actor["type"],
        sender_name=current_actor["name"],
        text=dto.text,
        recipient_id=dto.recipient_id,
        files=files,
    )

    return jsonify(saved_message.to_dict()), 201


def sse_formatter(
    generator: Generator[str, None, None],
) -> Generator[str, None, None]:
    """
    Format text chunks into W3C compliant Server-Sent Events (SSE).
    """
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


@chat_bp.route("/stream", methods=["POST"])
@inject
def stream_chat(
    orchestrator: AgentOrchestrator = Provide[Container.agent_orchestrator],
    agent_service: AgentService = Provide[Container.agent_service],
    security_context: SecurityContextService = Provide[
        Container.security_context_service
    ],
):
    """Stream an LLM agent's response live using Server-Sent Events (SSE)."""
    data = request.get_json(silent=True) or {}
    user_text = data.get("message", "Hallo!")
    conversation_id = data.get("conversation_id")
    agent_id = data.get("agent_id") or conversation_id

    if not agent_id:
        raise ValidationError("MISSING_AGENT_ID")

    current_actor = security_context.get_current_actor()
    user_id = current_actor["id"]

    agent = agent_service.get_agent(agent_id)
    agent_name = agent.name

    print("=== [1] ROUTE stream_chat HIT! ===", flush=True)
    raw_stream = orchestrator.stream_agent_response(
        user_text=user_text,
        conversation_id=conversation_id,
        agent_id=agent_id,
        agent_name=agent_name,
        user_id=user_id,
    )
    print("=== [2] ORCHESTRATOR GENERATOR CREATED ===", flush=True)

    return Response(
        stream_with_context(sse_formatter(raw_stream)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@chat_bp.route("/conversations/<conversation_id>/files/<path:filename>", methods=["GET"])
def get_conversation_file(
    conversation_id: str,
    filename: str,
):
    """Serves files directly from the conversation sandbox folder."""
    conversations_dir = current_app.config.get(
        "CONVERSATIONS_FOLDER",
        os.path.join(current_app.root_path, "..", "instance", "conversations"),
    )

    target_folder = os.path.abspath(os.path.join(conversations_dir, conversation_id))

    return send_from_directory(
        directory=target_folder,
        path=filename,
        as_attachment=True,
    )
