"""SQLAlchemy Agent Repository Implementation Module.

Handles persistence, retrieval, mapping, and transaction management for Agent domain entities.
"""

import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.agent import Agent
from app.domain.models.datasource import Datasource
from app.domain.repositories.agent_repository import AgentRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import AgentModel, DatasourceModel, MessageModel

logger = logging.getLogger(__name__)


class SQLAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy-backed implementation of the AgentRepository domain interface."""

    def _to_domain(self, model: AgentModel) -> Agent:
        """Converts an AgentModel ORM instance into an Agent domain entity.

        Args:
            model (AgentModel): SQLAlchemy ORM model instance.

        Returns:
            Agent: Fully mapped domain entity.
        """
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
            created_at=model.created_at,
        )

    def save(self, agent: Agent) -> Agent:
        """Persists or updates an Agent entity in the database.

        Args:
            agent (Agent): Domain entity to persist.

        Returns:
            Agent: Mapped domain entity after persistence.

        Raises:
            StorageError: If database persistence or synchronization fails.
        """
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

            # Synchronize attached datasources
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
        """Retrieves an Agent domain entity by its primary key UUID.

        Args:
            agent_id (str): Unique UUID of the agent.

        Returns:
            Agent | None: The found agent entity, or None if missing.

        Raises:
            StorageError: If database querying encounters an error.
        """
        try:
            model = db.session.get(AgentModel, agent_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Agent '%s': %s", agent_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Agent '{agent_id}': {exc}") from exc

    def get_all(self) -> list[Agent]:
        """Retrieves all registered agents ordered descending by their latest message activity.

        Returns:
            list[Agent]: List of all agent domain entities.

        Raises:
            StorageError: If querying entities fails.
        """
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
        """Permanently removes an Agent from persistence.

        Args:
            agent_id (str): Target Agent UUID.

        Returns:
            bool: True if found and deleted, False otherwise.

        Raises:
            StorageError: If the deletion transaction fails.
        """
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
