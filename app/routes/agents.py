"""
Agent Management HTTP Endpoints.

Provides RESTful endpoints for CRUD operations on agents and datasource file uploads.
"""

import json
from typing import Generator
from flask import Blueprint, jsonify, request, Response, stream_with_context
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.knowledge import DatasourceService
from app.services.messaging import MessagingService
from app.services.agent.agent_orchestrator import AgentOrchestrator
from app.services.infrastructure.security_context import SecurityContextService
from app.routes.decorators import validate_json
from app.routes.schemas import CreateAgentRequest
from app.domain.errors import ValidationError

agents_bp = Blueprint("agents", __name__, url_prefix="/api/v1/agents")


@agents_bp.route("", methods=["POST"])
@validate_json(CreateAgentRequest)
@inject
def create_agent(
    dto: CreateAgentRequest,
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Creates a new agent entity in the system."""
    new_agent = agent_service.create_agent(
        name=dto.name,
        system_prompt=dto.system_prompt,
        description=dto.description,
        memory_enabled=dto.memory_enabled,
        memory_mode=dto.memory_mode,
        memory_limit_type=dto.memory_limit_type,
        memory_message_count=dto.memory_message_count
    )

    return jsonify(new_agent.to_dict()), 201


@agents_bp.route("/<agent_id>", methods=["PUT"])
@validate_json(CreateAgentRequest)
@inject
def update_agent(
    dto: CreateAgentRequest,
    *,
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Updates metadata and memory configurations for an existing agent."""
    updated_agent = agent_service.update_agent(
        agent_id=agent_id,
        name=dto.name,
        system_prompt=dto.system_prompt,
        description=dto.description,
        memory_enabled=dto.memory_enabled,
        memory_mode=dto.memory_mode,
        memory_limit_type=dto.memory_limit_type,
        memory_message_count=dto.memory_message_count
    )

    return jsonify(updated_agent.to_dict()), 200


@agents_bp.route("/<agent_id>/datasources", methods=["POST"])
@inject
def upload_datasource(
    agent_id: str,
    datasource_service: DatasourceService = Provide[Container.datasource_service],
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Uploads a file via multipart/form-data and links it as a datasource to the specified agent."""
    if "file" not in request.files:
        return jsonify({"error": "NO_FILE_PART"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "NO_SELECTED_FILE"}), 400

    # Ensure target agent exists (raises NotFoundError if missing)
    agent_service.get_agent(agent_id)

    display_name = request.form.get("name") 

    new_datasource = datasource_service.process_and_save_file(
        file=file,
        display_name=display_name,
        agent_id=agent_id
    )

    return jsonify(new_datasource.to_dict()), 201


@agents_bp.route("", methods=["GET"])
@inject
def get_all_agents(
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Retrieves all registered agents."""
    agents = agent_service.get_all_agents()
    return jsonify([agent.to_dict() for agent in agents]), 200


@agents_bp.route("/<agent_id>", methods=["DELETE"])
@inject
def delete_agent(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Permanently deletes an agent from the system."""
    agent_service.delete_agent(agent_id)
    return "", 204


@agents_bp.route("/<agent_id>/datasources/<datasource_id>", methods=["DELETE"])
@inject
def delete_datasource(
    agent_id: str,
    datasource_id: str,
    datasource_service: DatasourceService = Provide[Container.datasource_service],
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Deletes a datasource associated with an agent."""
    agent_service.get_agent(agent_id)
    datasource_service.delete_datasource(datasource_id=datasource_id, agent_id=agent_id)

    return jsonify({"message": "Datasource successfully deleted", "id": datasource_id}), 200


@agents_bp.route("/<agent_id>/conversations", methods=["GET"])
@inject
def get_agent_conversations(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves all conversations associated with a specific agent."""
    # Ensure agent exists (raises 404 if missing)
    agent_service.get_agent(agent_id)

    conversations = messaging_service.get_conversations_by_agent(agent_id)
    return jsonify([conv.to_dict() for conv in conversations]), 200


@agents_bp.route("/<agent_id>/conversations/<conversation_id>/history", methods=["GET"])
@inject
def get_conversation_history(
    agent_id: str,
    conversation_id: str,
    limit: int = 50,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves message history for a specific agent conversation."""
    agent_service.get_agent(agent_id)

    messages = messaging_service.get_conversation_history(
        conversation_id=conversation_id, limit=limit
    )
    return jsonify([msg.to_dict() for msg in messages]), 200


@agents_bp.route("/<agent_id>/conversations/<conversation_id>", methods=["DELETE"])
@inject
def delete_conversation(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Deletes a specific conversation for an agent."""
    # Sicherstellen, dass der Agent existiert (wirft 404 falls nicht vorhanden)
    agent_service.get_agent(agent_id)

    messaging_service.delete_conversation(conversation_id)
    return "", 204


@agents_bp.route("/<agent_id>/stream", methods=["POST"])
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
    Persists an incoming user message (and optional attachments) and streams 
    the agent's real-time LLM execution via Server-Sent Events (SSE).
    """
    # 1. Agent validieren
    agent = agent_service.get_agent(agent_id)

    # 2. Payload und Dateien extrahieren
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

    # 3. Kontext des aktuellen Nutzers bestimmen
    current_actor = security_context.get_current_actor()

    # 4. User-Nachricht direkt vor dem Stream persistieren (recipient_id ist die agent_id)
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

    # 5. Live SSE Generator initialisieren
    raw_stream = orchestrator.stream_agent_response(
        user_text=text,
        conversation_id=resolved_conversation_id,
        agent_id=agent_id,
        agent_name=agent.name,
        user_id=current_actor["id"],
    )

    def sse_formatter(generator: Generator[str, None, None]) -> Generator[str, None, None]:
        """Format text chunks into W3C compliant Server-Sent Events (SSE)."""
        # Initiales Event mit generierter conversation_id & user_message_id senden
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