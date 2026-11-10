"""SQLAlchemy implementation of the WorkflowRepository interface."""

from datetime import datetime, timezone
import logging
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from app.domain.repositories.workflow_repository import WorkflowRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models.workflow import (
    WorkflowEdgeModel,
    WorkflowModel,
    WorkflowNodeModel,
)

logger = logging.getLogger(__name__)


class SQLAlchemyWorkflowRepository(WorkflowRepository):
    """SQLAlchemy-backed implementation of the WorkflowRepository domain interface."""

    def _to_domain(self, model: WorkflowModel) -> Workflow:
        nodes = [
            WorkflowNode(
                id=n.id,
                agent_id=n.agent_id,
                agent_name=n.agent_name,
                agent_description=n.agent_description,
                x=n.x,
                y=n.y,
                prompt=n.prompt or "",
            )
            for n in (model.nodes or [])
        ]
        edges = [
            WorkflowEdge(
                id=e.id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
            )
            for e in (model.edges or [])
        ]
        return Workflow(
            id=model.id,
            name=model.name,
            description=model.description,
            nodes=nodes,
            edges=edges,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def save(self, workflow: Workflow) -> Workflow:
        try:
            model = db.session.get(WorkflowModel, workflow.id)
            now = datetime.now(timezone.utc)

            if not model:
                model = WorkflowModel(
                    id=workflow.id,
                    name=workflow.name,
                    description=workflow.description,
                    created_at=workflow.created_at or now,
                    updated_at=now,
                )
                db.session.add(model)
            else:
                model.name = workflow.name
                model.description = workflow.description
                model.updated_at = now
                model.nodes.clear()
                model.edges.clear()
                db.session.flush()

            for node in workflow.nodes:
                model.nodes.append(
                    WorkflowNodeModel(
                        id=node.id,
                        workflow_id=workflow.id,
                        agent_id=node.agent_id,
                        agent_name=node.agent_name,
                        agent_description=node.agent_description,
                        x=node.x,
                        y=node.y,
                        prompt=node.prompt,
                    )
                )

            for edge in workflow.edges:
                model.edges.append(
                    WorkflowEdgeModel(
                        id=edge.id,
                        workflow_id=workflow.id,
                        source_node_id=edge.source_node_id,
                        target_node_id=edge.target_node_id,
                    )
                )

            db.session.commit()
            return self._to_domain(model)
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error saving Workflow '%s': %s", workflow.id, exc, exc_info=True)
            raise StorageError(f"Database error saving Workflow '{workflow.id}': {exc}") from exc

    def get_by_id(self, workflow_id: str) -> Workflow | None:
        try:
            model = db.session.get(WorkflowModel, workflow_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Workflow '%s': %s", workflow_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Workflow '{workflow_id}': {exc}") from exc

    def get_all(self) -> list[Workflow]:
        try:
            models = (
                db.session.query(WorkflowModel)
                .order_by(WorkflowModel.updated_at.desc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving all Workflows: %s", exc, exc_info=True)
            raise StorageError(f"Database error retrieving all Workflows: {exc}") from exc

    def delete(self, workflow_id: str) -> bool:
        try:
            model = db.session.get(WorkflowModel, workflow_id)
            if not model:
                return False
            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Workflow '%s': %s", workflow_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Workflow '{workflow_id}': {exc}") from exc