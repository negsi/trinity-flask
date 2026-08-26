"""Agent Datasources Endpoints."""

from flask import Blueprint, jsonify, request
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.knowledge import DatasourceService

bp = Blueprint("datasources", __name__, url_prefix="/api/v1/agents/<agent_id>/datasources")


@bp.route("", methods=["POST"])
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

    # Ensure target agent exists (raises error if missing)
    agent_service.get_agent(agent_id)

    display_name = request.form.get("name")

    new_datasource = datasource_service.process_and_save_file(
        file=file,
        display_name=display_name,
        agent_id=agent_id
    )

    return jsonify(new_datasource.to_dict()), 201


@bp.route("/<datasource_id>", methods=["DELETE"])
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
