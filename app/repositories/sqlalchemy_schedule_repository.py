"""SQLAlchemy implementation of the ScheduleRepository interface."""

from datetime import datetime, timezone
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.schedule import Schedule, ScheduleExecution
from app.domain.repositories.schedule_repository import ScheduleRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models.schedule import (
    ScheduleExecutionModel,
    ScheduleModel,
)

logger = logging.getLogger(__name__)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensures a datetime object is timezone-aware in UTC (handles SQLite naive timestamps)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SQLAlchemyScheduleRepository(ScheduleRepository):
    """SQLAlchemy-backed implementation of the ScheduleRepository domain interface."""

    def _to_domain(self, model: ScheduleModel) -> Schedule:
        return Schedule(
            id=model.id,
            agent_id=model.agent_id,
            name=model.name,
            prompt=model.prompt,
            is_active=model.is_active,
            trigger_type=model.trigger_type,
            cron_expression=model.cron_expression,
            scheduled_at=_ensure_utc(model.scheduled_at),
            next_run_at=_ensure_utc(model.next_run_at),
            last_run_at=_ensure_utc(model.last_run_at),
            created_at=_ensure_utc(model.created_at) or datetime.now(timezone.utc),
            updated_at=_ensure_utc(model.updated_at) or datetime.now(timezone.utc),
        )

    def _execution_to_domain(
        self, model: ScheduleExecutionModel
    ) -> ScheduleExecution:
        return ScheduleExecution(
            id=model.id,
            schedule_id=model.schedule_id,
            conversation_id=model.conversation_id,
            status=model.status,
            resolved_prompt=model.resolved_prompt,
            error_message=model.error_message,
            started_at=_ensure_utc(model.started_at) or datetime.now(timezone.utc),
            finished_at=_ensure_utc(model.finished_at),
        )

    def save(self, schedule: Schedule) -> Schedule:
        try:
            model = db.session.get(ScheduleModel, schedule.id)
            now = datetime.now(timezone.utc)
            if not model:
                model = ScheduleModel(
                    id=schedule.id,
                    agent_id=schedule.agent_id,
                    name=schedule.name,
                    prompt=schedule.prompt,
                    is_active=schedule.is_active,
                    trigger_type=schedule.trigger_type,
                    cron_expression=schedule.cron_expression,
                    scheduled_at=schedule.scheduled_at,
                    next_run_at=schedule.next_run_at,
                    last_run_at=schedule.last_run_at,
                    created_at=schedule.created_at or now,
                    updated_at=now,
                )
                db.session.add(model)
            else:
                model.name = schedule.name
                model.prompt = schedule.prompt
                model.is_active = schedule.is_active
                model.trigger_type = schedule.trigger_type
                model.cron_expression = schedule.cron_expression
                model.scheduled_at = schedule.scheduled_at
                model.next_run_at = schedule.next_run_at
                model.last_run_at = schedule.last_run_at
                model.updated_at = now

            db.session.commit()
            return self._to_domain(model)
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error(
                "Error saving Schedule '%s': %s", schedule.id, exc, exc_info=True
            )
            raise StorageError(
                f"Database error saving Schedule '{schedule.id}': {exc}"
            ) from exc

    def get_by_id(self, schedule_id: str) -> Schedule | None:
        try:
            model = db.session.get(ScheduleModel, schedule_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error(
                "Error retrieving Schedule '%s': %s", schedule_id, exc, exc_info=True
            )
            raise StorageError(
                f"Database error retrieving Schedule '{schedule_id}': {exc}"
            ) from exc

    def get_all(self) -> list[Schedule]:
        try:
            models = (
                db.session.query(ScheduleModel)
                .order_by(ScheduleModel.created_at.desc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving all Schedules: %s", exc, exc_info=True)
            raise StorageError(
                f"Database error retrieving all Schedules: {exc}"
            ) from exc

    def get_by_agent_id(self, agent_id: str) -> list[Schedule]:
        try:
            models = (
                db.session.query(ScheduleModel)
                .filter(ScheduleModel.agent_id == agent_id)
                .order_by(ScheduleModel.created_at.desc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error(
                "Error retrieving Schedules for agent '%s': %s",
                agent_id,
                exc,
                exc_info=True,
            )
            raise StorageError(
                f"Database error retrieving Schedules for agent '{agent_id}': {exc}"
            ) from exc

    def get_due_schedules(self, now: datetime) -> list[Schedule]:
        try:
            models = (
                db.session.query(ScheduleModel)
                .filter(
                    ScheduleModel.is_active.is_(True),
                    ScheduleModel.next_run_at.isnot(None),
                    ScheduleModel.next_run_at <= now,
                )
                .order_by(ScheduleModel.next_run_at.asc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error querying due Schedules: %s", exc, exc_info=True)
            raise StorageError(
                f"Database error querying due Schedules: {exc}"
            ) from exc

    def delete(self, schedule_id: str) -> bool:
        try:
            model = db.session.get(ScheduleModel, schedule_id)
            if not model:
                return False
            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error(
                "Error deleting Schedule '%s': %s", schedule_id, exc, exc_info=True
            )
            raise StorageError(
                f"Database error deleting Schedule '{schedule_id}': {exc}"
            ) from exc

    def save_execution(self, execution: ScheduleExecution) -> ScheduleExecution:
        try:
            model = db.session.get(ScheduleExecutionModel, execution.id)
            if not model:
                model = ScheduleExecutionModel(
                    id=execution.id,
                    schedule_id=execution.schedule_id,
                    conversation_id=execution.conversation_id,
                    status=execution.status,
                    resolved_prompt=execution.resolved_prompt,
                    error_message=execution.error_message,
                    started_at=execution.started_at,
                    finished_at=execution.finished_at,
                )
                db.session.add(model)
            else:
                model.conversation_id = execution.conversation_id
                model.status = execution.status
                model.resolved_prompt = execution.resolved_prompt
                model.error_message = execution.error_message
                model.finished_at = execution.finished_at

            db.session.commit()
            return self._execution_to_domain(model)
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error(
                "Error saving ScheduleExecution '%s': %s",
                execution.id,
                exc,
                exc_info=True,
            )
            raise StorageError(
                f"Database error saving ScheduleExecution '{execution.id}': {exc}"
            ) from exc

    def get_executions_by_schedule_id(
        self, schedule_id: str, limit: int = 50
    ) -> list[ScheduleExecution]:
        try:
            models = (
                db.session.query(ScheduleExecutionModel)
                .filter(ScheduleExecutionModel.schedule_id == schedule_id)
                .order_by(ScheduleExecutionModel.started_at.desc())
                .limit(limit)
                .all()
            )
            return [self._execution_to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error(
                "Error retrieving executions for Schedule '%s': %s",
                schedule_id,
                exc,
                exc_info=True,
            )
            raise StorageError(
                f"Database error retrieving executions for Schedule '{schedule_id}': {exc}"
            ) from exc
