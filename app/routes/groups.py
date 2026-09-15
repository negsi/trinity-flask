"""Group CRUD Endpoints."""

from flask import Blueprint, jsonify
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.routes.decorators import validate_json
from app.routes.schemas import GroupRequest, AssignAgentsRequest
from app.services.group.group_service import GroupService

bp = Blueprint("groups", __name__, url_prefix="/api/v1/groups")


@bp.route("", methods=["POST"])
@validate_json(GroupRequest)
@inject
def create_group(
    dto: GroupRequest,
    group_service: GroupService = Provide[Container.group_service],
):
    """Creates a new group."""
    group = group_service.create_group(name=dto.name, description=dto.description)
    return jsonify(group.to_dict()), 201


@bp.route("", methods=["GET"])
@inject
def get_all_groups(
    group_service: GroupService = Provide[Container.group_service],
):
    """Retrieves all groups with agent count."""
    groups = group_service.get_all_groups()
    return jsonify([g.to_dict() for g in groups]), 200


@bp.route("/<group_id>", methods=["PUT"])
@validate_json(GroupRequest)
@inject
def update_group(
    dto: GroupRequest,
    group_id: str,
    group_service: GroupService = Provide[Container.group_service],
):
    """Updates an existing group."""
    updated = group_service.update_group(group_id=group_id, name=dto.name, description=dto.description)
    return jsonify(updated.to_dict()), 200


@bp.route("/<group_id>", methods=["DELETE"])
@inject
def delete_group(
    group_id: str,
    group_service: GroupService = Provide[Container.group_service],
):
    """Deletes a group. Only the association to agents is removed."""
    group_service.delete_group(group_id)
    return "", 204

@bp.route("/<group_id>/agents", methods=["PUT"])
@validate_json(AssignAgentsRequest)
@inject
def update_group_agents(
    dto: AssignAgentsRequest,
    group_id: str,
    group_service: GroupService = Provide[Container.group_service],
):
    """Updates the list of agents assigned to a specific group."""
    group_service.update_group_agents(group_id=group_id, agent_ids=dto.agent_ids)
    return "", 200