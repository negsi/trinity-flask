"""
Agent Management HTTP Endpoints.

Provides RESTful endpoints for CRUD operations on agents and datasource file uploads.
"""

from flask import Blueprint, jsonify, request  
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent_service import AgentService
from app.services.datasource_service import DatasourceService
from app.services.messaging_service import MessagingService
from app.routes.decorators import validate_json
from app.routes.schemas import CreateAgentRequest

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
        description=dto.description
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
    """Updates metadata for an existing agent."""
    updated_agent = agent_service.update_agent(
        agent_id=agent_id,
        name=dto.name,
        system_prompt=dto.system_prompt,
        description=dto.description
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