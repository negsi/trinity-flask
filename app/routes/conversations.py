"""Agent Conversations Endpoints."""

from flask import Blueprint, jsonify
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.messaging import MessagingService

bp = Blueprint("conversations", __name__, url_prefix="/api/v1/agents/<agent_id>/conversations")


@bp.route("", methods=["GET"])
@inject
def get_agent_conversations(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves all conversations associated with a specific agent."""
    agent_service.get_agent(agent_id)
    conversations = messaging_service.get_conversations_by_agent(agent_id)
    return jsonify([conv.to_dict() for conv in conversations]), 200


@bp.route("/<conversation_id>/history", methods=["GET"])
@inject
def get_conversation_history(
    agent_id: str,
    conversation_id: str,
    limit: int = 50,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves message history for a specific conversation."""
    agent_service.get_agent(agent_id)
    messages = messaging_service.get_conversation_history(
        conversation_id=conversation_id, limit=limit
    )
    return jsonify([msg.to_dict() for msg in messages]), 200


@bp.route("/<conversation_id>", methods=["DELETE"])
@inject
def delete_conversation(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Deletes a specific conversation for an agent."""
    agent_service.get_agent(agent_id)
    messaging_service.delete_conversation(conversation_id)
    return "", 204
