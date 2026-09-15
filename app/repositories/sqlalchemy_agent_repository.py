"""SQLAlchemy Agent Repository Implementation Module."""

import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.agent import Agent
from app.domain.models.datasource import Datasource
from app.domain.repositories.agent_repository import AgentRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import AgentModel, DatasourceModel, GroupModel, MessageModel

logger = logging.getLogger(__name__)


class SQLAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy-backed implementation of the AgentRepository domain interface."""

    def _to_domain(self, model: AgentModel) -> Agent:
        datasources = [
            Datasource(
                id=ds.id,
                name=ds.name,
                filename=ds.filename,
                file_path=ds.file_path,
                mime_type=ds.mime_type,
                file_size=ds.file_size,
                agent_id=ds.agent_id,
                created_at=ds.created_at,
            )
            for ds in (model.datasources or [])
        ]

        group_ids = [g.id for g in (model.groups or [])]

        return Agent(
            id=model.id,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            memory_enabled=model.memory_enabled,
            memory_mode=model.memory_mode,
            memory_limit_type=model.memory_limit_type,
            memory_message_count=model.memory_message_count,
            datasources=datasources,
            groups=group_ids,
            created_at=model.created_at,
        )

    def save(self, agent: Agent) -> Agent:
        try:
            model: AgentModel | None = None
            if agent.id:
                model = db.session.get(AgentModel, agent.id)

            if not model:
                model = AgentModel(
                    id=agent.id,
                    name=agent.name,
                    description=agent.description,
                    system_prompt=agent.system_prompt,
                    memory_enabled=agent.memory_enabled,
                    memory_mode=agent.memory_mode,
                    memory_limit_type=agent.memory_limit_type,
                    memory_message_count=agent.memory_message_count,
                    created_at=agent.created_at,
                )
                db.session.add(model)
            else:
                model.name = agent.name
                model.description = agent.description
                model.system_prompt = agent.system_prompt
                model.memory_enabled = agent.memory_enabled
                model.memory_mode = agent.memory_mode
                model.memory_limit_type = agent.memory_limit_type
                model.memory_message_count = agent.memory_message_count

            # Synchronize Groups Many-to-Many
            if agent.groups is not None:
                matched_groups = (
                    db.session.query(GroupModel).filter(GroupModel.id.in_(agent.groups)).all()
                    if agent.groups
                    else []
                )
                model.groups = matched_groups

            # Synchronize Datasources
            synced_datasources: list[DatasourceModel] = []
            for ds in agent.datasources:
                ds_model = db.session.get(DatasourceModel, ds.id)
                if ds_model:
                    ds_model.name = ds.name
                    ds_model.filename = ds.filename
                    ds_model.file_path = ds.file_path
                    ds_model.mime_type = ds.mime_type
                    ds_model.file_size = ds.file_size
                    ds_model.agent_id = model.id
                else:
                    ds_model = DatasourceModel(
                        id=ds.id,
                        name=ds.name,
                        filename=ds.filename,
                        file_path=ds.file_path,
                        mime_type=ds.mime_type,
                        file_size=ds.file_size,
                        agent_id=model.id,
                        created_at=ds.created_at,
                    )
                synced_datasources.append(ds_model)

            model.datasources = synced_datasources
            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Agent '%s': %s", agent.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Agent '{agent.id}': {exc}") from exc

    def get_by_id(self, agent_id: str) -> Agent | None:
        try:
            model = db.session.get(AgentModel, agent_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Agent '%s': %s", agent_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Agent '{agent_id}': {exc}") from exc

    def get_all(self) -> list[Agent]:
        try:
            models = (
                AgentModel.query.outerjoin(
                    MessageModel,
                    (AgentModel.id == MessageModel.sender_id)
                    | (AgentModel.id == MessageModel.recipient_id),
                )
                .group_by(AgentModel.id)
                .order_by(func.max(MessageModel.timestamp).desc().nulls_last())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving all agents: %s", exc, exc_info=True)
            raise StorageError(f"Database error retrieving agents: {exc}") from exc

    def delete(self, agent_id: str) -> bool:
        try:
            model = db.session.get(AgentModel, agent_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Agent '%s': %s", agent_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Agent '{agent_id}': {exc}") from exc

    def update_group_assignments(self, group_id: str, agent_ids: list[str]) -> None:
        """Synchronizes agent assignments for a specific group directly in SQLAlchemy."""
        try:
            group_model = db.session.get(GroupModel, group_id)
            if not group_model:
                raise StorageError(f"Group with ID '{group_id}' does not exist.")

            assigned_agents = (
                db.session.query(AgentModel).filter(AgentModel.id.in_(agent_ids)).all()
                if agent_ids
                else []
            )

            group_model.agents = assigned_agents
            db.session.commit()

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to update agents for group '%s': %s", group_id, exc, exc_info=True)
            raise StorageError(f"Database error updating agents for group '{group_id}': {exc}") from exc