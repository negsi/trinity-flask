"""
SQLAlchemy Agent Repository Implementation.

Handles persistence, retrieval, mapping, and ordering of Agent domain entities in the database.
"""

from typing import List, Optional
from sqlalchemy import func

from app.domain.repositories.agent_repository import AgentRepository
from app.domain.models.agent import Agent
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models.agent import AgentModel
from app.domain.models.datasource import Datasource
from app.storage.sqlalchemy.models.datasource import DatasourceModel
from app.storage.sqlalchemy.models.message import MessageModel


class SQLAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy implementation of the AgentRepository interface."""

    def _to_domain(self, model: AgentModel) -> Agent:
        """
        Maps a database ORM instance to a clean domain entity.

        Args:
            model (AgentModel): SQLAlchemy agent model.

        Returns:
            Agent: Mapped domain model instance.
        """
        datasources = [
            Datasource(
                id=ds_model.id,
                name=ds_model.name,
                filename=ds_model.filename,
                file_path=ds_model.file_path,
                mime_type=ds_model.mime_type,
                file_size=ds_model.file_size,
                agent_id=ds_model.agent_id,
            )
            for ds_model in model.datasources
        ]

        return Agent(
            id=model.id,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            datasources=datasources,
        )

    def save(self, agent: Agent) -> Agent:
        """Saves or updates an agent domain entity in the database."""
        model = None
        if agent.id:
            model = db.session.get(AgentModel, agent.id)

        # 1. Update metadata
        if not model:
            model = AgentModel(
                name=agent.name,
                description=agent.description,
                system_prompt=agent.system_prompt,
            )
            if agent.id:
                model.id = agent.id
            db.session.add(model)
        else:
            model.name = agent.name
            model.description = agent.description
            model.system_prompt = agent.system_prompt

        # 2. Synchronize attached datasources
        model.datasources = [
            db.session.get(DatasourceModel, ds.id)
            or DatasourceModel(
                id=ds.id,
                name=ds.name,
                filename=ds.filename,
                file_path=ds.file_path,
                mime_type=ds.mime_type,
                file_size=ds.file_size,
                agent_id=model.id,
            )
            for ds in agent.datasources
        ]

        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Fetches an agent entity by its primary key ID."""
        model = db.session.get(AgentModel, agent_id)
        if not model:
            return None
        return self._to_domain(model)

    def get_all(self) -> List[Agent]:
        """
        Fetches all agents ordered descending by their latest message timestamp.
        Agents without messages remain in the output, sorted toward the end.
        """
        models = (
            AgentModel.query.outerjoin(
                MessageModel,
                (AgentModel.id == MessageModel.sender_id)
                | (AgentModel.id == MessageModel.recipient_id),
            )
            .group_by(AgentModel.id)
            .order_by(func.max(MessageModel.timestamp).desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def delete(self, agent_id: str) -> None:
        """Removes an agent from the database by ID."""
        model = db.session.get(AgentModel, agent_id)
        if model:
            db.session.delete(model)
            db.session.commit()
