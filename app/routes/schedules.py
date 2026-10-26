"""REST API endpoints for managing Agent Schedules and Execution History."""

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, jsonify

from app.containers import Container
from app.routes.decorators import validate_json
from app.routes.schemas import CreateScheduleRequest, UpdateScheduleRequest
from app.services.schedule.schedule_service import ScheduleService

bp = Blueprint("schedules", __name__, url_prefix="/api/v1")


@bp.route("/agents/<agent_id>/schedules", methods=["GET"])
@inject
def list_agent_schedules(
    agent_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Lists all schedules configured for a specific agent."""
    schedules = schedule_service.get_schedules_for_agent(agent_id=agent_id)
    return jsonify([s.to_dict() for s in schedules]), 200


@bp.route("/agents/<agent_id>/schedules", methods=["POST"])
@validate_json(CreateScheduleRequest)
@inject
def create_agent_schedule(
    dto: CreateScheduleRequest,
    *,
    agent_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Creates a new schedule for a specific agent."""
    created = schedule_service.create_schedule(
        agent_id=agent_id,
        name=dto.name,
        prompt=dto.prompt,
        trigger_type=dto.trigger_type,
        is_active=dto.is_active,
        cron_expression=dto.cron_expression,
        scheduled_at=dto.scheduled_at,
    )
    return jsonify(created.to_dict()), 201


@bp.route("/schedules/<schedule_id>", methods=["GET"])
@inject
def get_schedule(
    schedule_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Retrieves details of a single schedule by ID."""
    schedule = schedule_service.get_schedule(schedule_id=schedule_id)
    return jsonify(schedule.to_dict()), 200


@bp.route("/schedules/<schedule_id>", methods=["PUT"])
@validate_json(UpdateScheduleRequest)
@inject
def update_schedule(
    dto: UpdateScheduleRequest,
    *,
    schedule_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Updates an existing schedule."""
    updated = schedule_service.update_schedule(
        schedule_id=schedule_id,
        name=dto.name,
        prompt=dto.prompt,
        trigger_type=dto.trigger_type,
        is_active=dto.is_active,
        cron_expression=dto.cron_expression,
        scheduled_at=dto.scheduled_at,
    )
    return jsonify(updated.to_dict()), 200


@bp.route("/schedules/<schedule_id>", methods=["DELETE"])
@inject
def delete_schedule(
    schedule_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Deletes an existing schedule."""
    schedule_service.delete_schedule(schedule_id=schedule_id)
    return "", 204


@bp.route("/schedules/<schedule_id>/run", methods=["POST"])
@inject
def run_schedule_now(
    schedule_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Triggers an immediate manual test execution ('Run Now') of a schedule."""
    execution = schedule_service.execute_schedule(
        schedule_id=schedule_id,
        manual_trigger=True,
    )
    return jsonify(execution.to_dict()), 201


@bp.route("/schedules/<schedule_id>/executions", methods=["GET"])
@inject
def list_schedule_executions(
    schedule_id: str,
    schedule_service: ScheduleService = Provide[Container.schedule_service],
):
    """Retrieves the execution history for a specific schedule."""
    executions = schedule_service.get_executions(schedule_id=schedule_id)
    return jsonify([e.to_dict() for e in executions]), 200
