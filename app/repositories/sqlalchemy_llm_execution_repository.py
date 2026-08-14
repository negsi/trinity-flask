"""SQLAlchemy LLM Execution Repository Implementation Module.

Handles persistence and query operations for ReAct task chain execution records and step states.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.domain.enums import ExecutionStepStatus, ResponseType
from app.domain.errors import StorageError
from app.domain.models.llm_execution import ExecutionStep, LLMExecution
from app.domain.repositories.llm_execution_repository import LLMExecutionRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import LLMExecutionModel

logger = logging.getLogger(__name__)


class SQLAlchemyLLMExecutionRepository(LLMExecutionRepository):
    """SQLAlchemy implementation of the LLMExecutionRepository interface."""

    def _to_domain(self, model: LLMExecutionModel) -> LLMExecution:
        """Maps an LLMExecutionModel ORM instance to an LLMExecution domain model.

        Args:
            model (LLMExecutionModel): ORM model.

        Returns:
            LLMExecution: Domain entity.
        """
        steps = [
            ExecutionStep(
                step_number=s.get("step", 0),
                description=s.get("description", ""),
                tool_name=s.get("tool"),
                parameters=s.get("parameters", {}),
                status=ExecutionStepStatus(s.get("status", ExecutionStepStatus.PENDING.value)),
                result=s.get("result"),
            )
            for s in (model.steps or [])
            if isinstance(s, dict)
        ]

        return LLMExecution(
            id=model.id,
            conversation_id=model.conversation_id,
            message_id=model.message_id,
            response_type=ResponseType(model.response_type),
            summary_or_content=model.summary_or_content,
            is_complete=model.is_complete,
            steps=steps,
            created_at=model.created_at,
        )

    def save(self, execution: LLMExecution) -> LLMExecution:
        """Persists or updates an LLMExecution state in the database.

        Args:
            execution (LLMExecution): Entity to persist.

        Returns:
            LLMExecution: Persisted domain entity.

        Raises:
            StorageError: If database persistence fails.
        """
        try:
            model: LLMExecutionModel | None = None
            if execution.id:
                model = db.session.get(LLMExecutionModel, execution.id)

            steps_json = [s.to_dict() for s in execution.steps]

            if not model:
                model = LLMExecutionModel(
                    id=execution.id,
                    conversation_id=execution.conversation_id,
                    message_id=execution.message_id,
                    response_type=execution.response_type,
                    summary_or_content=execution.summary_or_content,
                    is_complete=execution.is_complete,
                    steps=steps_json,
                    created_at=execution.created_at,
                )
                db.session.add(model)
            else:
                model.conversation_id = execution.conversation_id
                model.message_id = execution.message_id
                model.response_type = execution.response_type
                model.summary_or_content = execution.summary_or_content
                model.is_complete = execution.is_complete
                model.steps = steps_json

            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save LLMExecution '%s': %s", execution.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving LLMExecution '{execution.id}': {exc}") from exc

    def get_by_id(self, execution_id: str) -> LLMExecution | None:
        """Retrieves an execution record by its unique ID.

        Args:
            execution_id (str): Unique UUID.

        Returns:
            LLMExecution | None: Domain entity if found, else None.

        Raises:
            StorageError: If query execution fails.
        """
        try:
            model = db.session.get(LLMExecutionModel, execution_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving LLMExecution '%s': %s", execution_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving LLMExecution '{execution_id}': {exc}") from exc

    def get_by_message_id(self, message_id: str) -> list[LLMExecution]:
        """Retrieves execution records associated with a message ID.

        Args:
            message_id (str): Message UUID.

        Returns:
            list[LLMExecution]: List of matching domain executions.

        Raises:
            StorageError: If query execution fails.
        """
        try:
            models = (
                LLMExecutionModel.query.filter(LLMExecutionModel.message_id == message_id)
                .order_by(LLMExecutionModel.created_at.asc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving executions for Message '%s': %s", message_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving executions for Message '{message_id}': {exc}") from exc

    def get_by_conversation_id(self, conversation_id: str) -> list[LLMExecution]:
        """Retrieves all executions for a conversation ordered descending by timestamp.

        Args:
            conversation_id (str): Target conversation UUID.

        Returns:
            list[LLMExecution]: Chronologically sorted execution records.

        Raises:
            StorageError: If query execution fails.
        """
        try:
            models = (
                LLMExecutionModel.query.filter(LLMExecutionModel.conversation_id == conversation_id)
                .order_by(LLMExecutionModel.created_at.desc())
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving executions for Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error fetching executions for Conversation '{conversation_id}': {exc}") from exc

    def delete(self, execution_id: str) -> bool:
        """Deletes an execution record by its unique ID.

        Args:
            execution_id (str): Target UUID.

        Returns:
            bool: True if removed, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        try:
            model = db.session.get(LLMExecutionModel, execution_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting LLMExecution '%s': %s", execution_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting LLMExecution '{execution_id}': {exc}") from exc
