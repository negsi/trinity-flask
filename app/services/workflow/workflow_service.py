"""Workflow Application Service Module."""

import logging
from typing import Any
import uuid

from app.domain.errors import ValidationError
from app.domain.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from app.domain.repositories.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service managing Workflow lifecycle and persistence."""

    def __init__(self, workflow_repo: WorkflowRepository) -> None:
        self.workflow_repo = workflow_repo

    def save_workflow(
        self,
        name: str,
        nodes_data: list[dict[str, Any]],
        edges_data: list[dict[str, Any]],
        workflow_id: str | None = None,
        description: str | None = None,
    ) -> Workflow:
        """Creates or updates (upserts) a workflow along with its nodes and edges."""
        nodes = [
            WorkflowNode(
                id=n.get("id") or str(uuid.uuid4()),
                agent_id=n["agentId"],
                agent_name=n["agentName"],
                agent_description=n.get("agentDescription"),
                x=float(n.get("x", 0.0)),
                y=float(n.get("y", 0.0)),
                prompt=n.get("prompt", ""),
            )
            for n in nodes_data
        ]

        node_ids = {node.id for node in nodes}
        edges = [
            WorkflowEdge(
                id=e.get("id") or str(uuid.uuid4()),
                source_node_id=e["sourceNodeId"],
                target_node_id=e["targetNodeId"],
            )
            for e in edges_data
            if e.get("sourceNodeId") in node_ids and e.get("targetNodeId") in node_ids
        ]

        workflow = Workflow(
            id=workflow_id or str(uuid.uuid4()),
            name=name.strip() if name else "Unbenannter Workflow",
            description=description,
            nodes=nodes,
            edges=edges,
        )

        saved = self.workflow_repo.save(workflow)
        logger.info("Saved Workflow '%s' (ID: '%s')", saved.name, saved.id)
        return saved

    def get_workflow(self, workflow_id: str) -> Workflow:
        """Retrieves a single workflow by ID or raises ValidationError."""
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise ValidationError(f"Workflow with ID '{workflow_id}' was not found.")
        return workflow

    def get_all_workflows(self) -> list[Workflow]:
        """Retrieves all workflows."""
        return self.workflow_repo.get_all()

    def delete_workflow(self, workflow_id: str) -> None:
        """Deletes an existing workflow."""
        self.get_workflow(workflow_id)
        self.workflow_repo.delete(workflow_id)
        logger.info("Deleted Workflow with ID '%s'", workflow_id)