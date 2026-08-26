"""Agent CRUD Endpoints."""

from flask import Blueprint, jsonify
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.routes.decorators import validate_json
from app.routes.schemas import CreateAgentRequest

bp = Blueprint("agents", __name__, url_prefix="/api/v1/agents")


@bp.route("", methods=["POST"])
@validate_json(CreateAgentRequest)
@inject
def create_agent(
    dto: CreateAgentRequest,
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Creates a new agent entity."""
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


@bp.route("", methods=["GET"])
@inject
def get_all_agents(
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Retrieves all registered agents."""
    agents = agent_service.get_all_agents()
    return jsonify([agent.to_dict() for agent in agents]), 200


@bp.route("/<agent_id>", methods=["PUT"])
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


@bp.route("/<agent_id>", methods=["DELETE"])
@inject
def delete_agent(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service]
):
    """Permanently deletes an agent."""
    agent_service.delete_agent(agent_id)
    return "", 204