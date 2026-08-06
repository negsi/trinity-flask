"""
Chat and Execution HTTP API Routes.

This module exposes endpoints for messaging operations within conversations, retrieving
historical message records, and streaming real-time LLM agent responses via Server-Sent Events (SSE).
"""

from flask import Blueprint, jsonify, Response, request, current_app, stream_with_context
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.messaging_service import MessagingService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.security_context import SecurityContextService
from app.services.agent_service import AgentService
from app.routes.decorators import validate_json
from app.routes.schemas import SendMessageRequest
from app.domain.models.message import ActorType

# Create a Flask Blueprint for chat endpoints under the prefix '/api/v1/chat'
chat_bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


@chat_bp.route("/messages", methods=["POST"])
@validate_json(SendMessageRequest)
@inject
def send_message(
    dto: SendMessageRequest,
    messaging_service: MessagingService = Provide[Container.messaging_service],
    security_context: SecurityContextService = Provide[Container.security_context_service]
):
    """
    Persist a chat message in a conversation.

    Validates the input JSON payload against the SendMessageRequest schema, converts the sender type
    to an ActorType domain enum, saves the message, and notifies subscribed listeners (e.g., triggering agents).

    Args:
        dto (SendMessageRequest): Validated Data Transfer Object containing request parameters.
        messaging_service (MessagingService): Injected messaging domain service.

    Returns:
        tuple[Response, int]: JSON representation of the saved Message domain entity and HTTP 201 Created status,
                              or HTTP 400 Bad Request if the sender_type is invalid.
    """
    current_actor = security_context.get_current_actor()

    # 2. Persist message via MessagingService (creates conversation if conversation_id is None)
    saved_message = messaging_service.send_message(
        conversation_id=dto.conversation_id,
        sender_id=current_actor["id"],
        sender_type=current_actor["type"],
        sender_name=current_actor["name"],
        text=dto.text,
        recipient_id=dto.recipient_id
    )

    # 3. Return serialized message with HTTP 201 Created status
    return jsonify(saved_message.to_dict()), 201


@chat_bp.route("/conversations/<conversation_id>/messages", methods=["GET"])
@inject
def get_conversation_history(
    conversation_id: str,
    messaging_service: MessagingService = Provide[Container.messaging_service]
):
    """
    Retrieve historical messages for a specific conversation.

    Fetches up to the most recent 50 messages registered under the provided conversation ID,
    ordered chronologically.

    Args:
        conversation_id (str): Unique identifier of the conversation thread.
        messaging_service (MessagingService): Injected messaging service.

    Returns:
        tuple[Response, int]: JSON list of serialized Message entities and HTTP 200 OK status code.
    """
    # Query repository for conversation messages
    history = messaging_service.message_repo.get_by_conversation(conversation_id)
    
    # Serialize domain objects into JSON array response
    return jsonify([msg.to_dict() for msg in history]), 200


def sse_formatter(generator):
    """
    Format raw text chunks into W3C compliant Server-Sent Events (SSE).

    Splits incoming text chunks containing newlines into distinct 'data:' lines
    to ensure inner newline characters do not corrupt the SSE event delimiter (\n\n).

    Args:
        generator (Generator[str, None, None]): Yielded raw text tokens or strings.

    Yields:
        Generator[str, None, None]: SSE-formatted stream frames ready for HTTP response.
    """
    for chunk in generator:
        if not chunk:
            continue
        lines = chunk.split('\n')
        for line in lines:
            yield f"data: {line}\n"
        yield "\n"  # Finalize the SSE event frame with trailing newline


@chat_bp.route('/stream', methods=['POST'])
@inject
def stream_chat(
    orchestrator: AgentOrchestrator = Provide[Container.agent_orchestrator],
    agent_service: AgentService = Provide[Container.agent_service],
    security_context: SecurityContextService = Provide[Container.security_context_service],
):
    """
    Stream an LLM agent's response live using Server-Sent Events (SSE).

    Processes the user's prompt through the AgentOrchestrator. Handles ReAct multi-turn loops,
    executes structured tool tasks (e.g., fetch_url), and streams generated text token-by-token.

    Expected JSON Payload:
        - message (str, optional): User prompt text. Defaults to "Hallo!".
        - conversation_id (str, optional): Conversation thread context ID.
        - agent_id (str, optional): Target Agent ID (defaults to conversation_id).
        - agent_name (str, optional): Display name of agent (defaults to "Agent").
        - user_id (str, optional): ID of triggering user (defaults to "user-default").

    Args:
        orchestrator (AgentOrchestrator): Injected orchestrator handling ReAct loops and streaming.

    Returns:
        Response: Flask HTTP Response object configured with mimetype 'text/event-stream'
                  and wrapped in stream_with_context to keep the application context active.
    """
    # 1. Safely extract JSON payload data from incoming request
    data = request.get_json(silent=True) or {}
    user_text = data.get("message", "Hallo!")
    conversation_id = data.get("conversation_id")
    agent_id = data.get("agent_id") or conversation_id

    if not agent_id:
        return jsonify({"error": "MISSING_AGENT_ID"}), 400

    current_actor = security_context.get_current_actor()
    user_id = current_actor["id"]

    agent = agent_service.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "AGENT_NOT_FOUND"}), 404

    agent_name = agent.name

    raw_stream = orchestrator.stream_agent_response(
        user_text=user_text,
        conversation_id=conversation_id,
        agent_id=agent_id,
        agent_name=agent_name,
        user_id=user_id,
    )

    # 2. Return SSE event-stream response using Flask's context streaming wrapper
    return Response(
        stream_with_context(sse_formatter(raw_stream)),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  
            'Connection': 'keep-alive',
        }
    )
