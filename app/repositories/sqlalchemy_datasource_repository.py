"""SQLAlchemy Datasource Repository Implementation Module.

Handles persistence, retrieval, and deletion of knowledge base Datasource domain entities.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.datasource import Datasource
from app.domain.repositories.datasource_repository import DatasourceRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import DatasourceModel

logger = logging.getLogger(__name__)


class SQLAlchemyDatasourceRepository(DatasourceRepository):
    """SQLAlchemy storage backend for managing knowledge base Datasources."""

    def _to_domain(self, model: DatasourceModel) -> Datasource:
        """Converts an ORM DatasourceModel instance into a clean Datasource domain entity.

        Args:
            model (DatasourceModel): SQLAlchemy model.

        Returns:
            Datasource: Domain model entity.
        """
        return Datasource(
            id=model.id,
            name=model.name,
            filename=model.filename,
            file_path=model.file_path,
            mime_type=model.mime_type,
            file_size=model.file_size,
            agent_id=model.agent_id,
            created_at=model.created_at,
        )

    def save(self, datasource: Datasource) -> Datasource:
        """Persists or updates a Datasource record in database storage.

        Args:
            datasource (Datasource): The datasource domain model to save.

        Returns:
            Datasource: The persisted datasource domain entity.

        Raises:
            StorageError: If database persistence fails.
        """
        try:
            model: DatasourceModel | None = None
            if datasource.id:
                model = db.session.get(DatasourceModel, datasource.id)

            if not model:
                model = DatasourceModel(
                    id=datasource.id,
                    name=datasource.name,
                    filename=datasource.filename,
                    file_path=datasource.file_path,
                    mime_type=datasource.mime_type,
                    file_size=datasource.file_size,
                    agent_id=datasource.agent_id,
                    created_at=datasource.created_at,
                )
                db.session.add(model)
            else:
                model.name = datasource.name
                model.filename = datasource.filename
                model.file_path = datasource.file_path
                model.mime_type = datasource.mime_type
                model.file_size = datasource.file_size
                model.agent_id = datasource.agent_id

            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Datasource '%s': %s", datasource.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Datasource '{datasource.id}': {exc}") from exc

    def get_by_id(self, datasource_id: str) -> Datasource | None:
        """Retrieves a single Datasource by its unique ID.

        Args:
            datasource_id (str): Unique UUID.

        Returns:
            Datasource | None: The domain model if resolved, else None.

        Raises:
            StorageError: If the query fails.
        """
        try:
            model = db.session.get(DatasourceModel, datasource_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Datasource '%s': %s", datasource_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Datasource '{datasource_id}': {exc}") from exc

    def get_by_agent_id(self, agent_id: str) -> list[Datasource]:
        """Retrieves all datasources associated with an Agent ID.

        Args:
            agent_id (str): Agent UUID.

        Returns:
            list[Datasource]: List of associated domain entities.

        Raises:
            StorageError: If querying fails.
        """
        try:
            models = (
                DatasourceModel.query.filter(DatasourceModel.agent_id == agent_id)
                .order_by(DatasourceModel.created_at.desc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving datasources for Agent '%s': %s", agent_id, exc, exc_info=True)
            raise StorageError(f"Database error fetching datasources for Agent '{agent_id}': {exc}") from exc

    def delete(self, datasource_id: str) -> bool:
        """Deletes a Datasource record from the database.

        Args:
            datasource_id (str): Target Datasource UUID.

        Returns:
            bool: True if removed, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        try:
            model = db.session.get(DatasourceModel, datasource_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Datasource '%s': %s", datasource_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Datasource '{datasource_id}': {exc}") from exc
