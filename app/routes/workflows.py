"""Workflow CRUD Endpoints."""

from flask import Blueprint, jsonify
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.routes.decorators import validate_json
from app.routes.schemas import SaveWorkflowRequest
from app.services.workflow.workflow_service import WorkflowService

bp = Blueprint("workflows", __name__, url_prefix="/api/v1/workflows")


@bp.route("", methods=["GET"])
@inject
def get_all_workflows(
    workflow_service: WorkflowService = Provide[Container.workflow_service],
):
    """Retrieves all saved workflows."""
    workflows = workflow_service.get_all_workflows()
    return jsonify([w.to_dict() for w in workflows]), 200


@bp.route("/<workflow_id>", methods=["GET"])
@inject
def get_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Provide[Container.workflow_service],
):
    """Retrieves a specific workflow by its ID."""
    workflow = workflow_service.get_workflow(workflow_id)
    return jsonify(workflow.to_dict()), 200


@bp.route("", methods=["POST"])
@validate_json(SaveWorkflowRequest)
@inject
def create_or_save_workflow(
    dto: SaveWorkflowRequest,
    workflow_service: WorkflowService = Provide[Container.workflow_service],
):
    """Creates or upserts a workflow."""
    saved = workflow_service.save_workflow(
        workflow_id=dto.id,
        name=dto.name,
        description=dto.description,
        nodes_data=[n.model_dump() for n in dto.nodes],
        edges_data=[e.model_dump() for e in dto.edges],
    )
    return jsonify(saved.to_dict()), 201


@bp.route("/<workflow_id>", methods=["PUT"])
@validate_json(SaveWorkflowRequest)
@inject
def update_workflow(
    dto: SaveWorkflowRequest,
    *,
    workflow_id: str,
    workflow_service: WorkflowService = Provide[Container.workflow_service],
):
    """Updates an existing workflow by ID."""
    saved = workflow_service.save_workflow(
        workflow_id=workflow_id,
        name=dto.name,
        description=dto.description,
        nodes_data=[n.model_dump() for n in dto.nodes],
        edges_data=[e.model_dump() for e in dto.edges],
    )
    return jsonify(saved.to_dict()), 200


@bp.route("/<workflow_id>", methods=["DELETE"])
@inject
def delete_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Provide[Container.workflow_service],
):
    """Deletes a workflow by ID."""
    workflow_service.delete_workflow(workflow_id)
    return "", 204