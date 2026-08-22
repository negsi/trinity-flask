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
