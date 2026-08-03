"""
SQLAlchemy Datasource Repository Implementation.

Persists and removes Datasource records from the database.
"""

from typing import Optional
from app.domain.models.datasource import Datasource
from app.domain.repositories.datasource_repository import DatasourceRepository
from app.storage.sqlalchemy.models.datasource import DatasourceModel
from app.storage.sqlalchemy.db import db


class SQLAlchemyDatasourceRepository(DatasourceRepository):
    """SQLAlchemy storage backend for managing agent datasources."""

    def save(self, datasource: Datasource) -> Datasource:
        """Saves or updates a datasource record in SQL storage."""
        model = DatasourceModel.query.get(datasource.id)
        if model:
            model.name = datasource.name
            model.agent_id = datasource.agent_id
        else:
            model = DatasourceModel(
                id=datasource.id,
                name=datasource.name,
                filename=datasource.filename,
                file_path=datasource.file_path,
                mime_type=datasource.mime_type,
                file_size=datasource.file_size,
                agent_id=datasource.agent_id
            )
            db.session.add(model)
        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, datasource_id: str) -> Optional[Datasource]:
        """Retrieves a datasource by ID."""
        model = DatasourceModel.query.get(datasource_id)
        return self._to_domain(model) if model else None

    def delete(self, datasource_id: str) -> None:
        """Deletes a datasource record from the database."""
        model = DatasourceModel.query.get(datasource_id)
        if model:
            db.session.delete(model)
            db.session.commit()

    def _to_domain(self, model: DatasourceModel) -> Datasource:
        """Maps ORM model to domain entity."""
        return Datasource(
            id=model.id,
            name=model.name,
            filename=model.filename,
            file_path=model.file_path,
            mime_type=model.mime_type,
            file_size=model.file_size,
            agent_id=model.agent_id
        )
