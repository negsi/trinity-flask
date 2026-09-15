"""SQLAlchemy Group Repository Implementation Module."""

import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.group import Group
from app.domain.repositories.group_repository import GroupRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import GroupModel, agent_groups

logger = logging.getLogger(__name__)


class SQLAlchemyGroupRepository(GroupRepository):
    """SQLAlchemy-backed GroupRepository implementation."""

    def _to_domain(self, model: GroupModel, agent_count: int = 0) -> Group:
        return Group(
            id=model.id,
            name=model.name,
            description=model.description,
            agent_count=agent_count if agent_count else len(model.agents or []),
            created_at=model.created_at,
        )

    def save(self, group: Group) -> Group:
        try:
            model = db.session.get(GroupModel, group.id) if group.id else None
            if not model:
                model = GroupModel(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    created_at=group.created_at,
                )
                db.session.add(model)
            else:
                model.name = group.name
                model.description = group.description

            db.session.commit()
            return self._to_domain(model)
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Group '%s': %s", group.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Group '{group.id}': {exc}") from exc

    def get_by_id(self, group_id: str) -> Group | None:
        try:
            model = db.session.get(GroupModel, group_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Group '%s': %s", group_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Group '{group_id}': {exc}") from exc

    def get_all(self) -> list[Group]:
        try:
            results = (
                db.session.query(
                    GroupModel,
                    func.count(agent_groups.c.agent_id).label("agent_count"),
                )
                .outerjoin(agent_groups, GroupModel.id == agent_groups.c.group_id)
                .group_by(GroupModel.id)
                .order_by(GroupModel.name.asc())
                .all()
            )
            return [self._to_domain(model, count) for model, count in results]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving all groups: %s", exc, exc_info=True)
            raise StorageError(f"Database error retrieving groups: {exc}") from exc

    def delete(self, group_id: str) -> bool:
        try:
            model = db.session.get(GroupModel, group_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Group '%s': %s", group_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Group '{group_id}': {exc}") from exc