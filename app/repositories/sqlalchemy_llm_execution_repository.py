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
from app.storage.sqlalchemy.models import LLMExecutionModel, LLMExecutionStepModel

logger = logging.getLogger(__name__)


class SQLAlchemyLLMExecutionRepository(LLMExecutionRepository):
    """SQLAlchemy implementation of the LLMExecutionRepository interface."""

    def _to_domain(self, model: LLMExecutionModel) -> LLMExecution:
        """Maps an LLMExecutionModel ORM instance to an LLMExecution domain model."""
        steps = []
        if model.steps:
            for s in model.steps:
                status_val = s.status
                if isinstance(status_val, str):
                    status_val = ExecutionStepStatus(status_val)

                steps.append(
                    ExecutionStep(
                        id=s.id,
                        execution_id=s.execution_id,
                        step_number=s.step_number,
                        description=s.description,
                        tool_name=s.tool_name,
                        parameters=s.parameters or {},
                        status=status_val,
                        result=s.result,
                    )
                )

        steps.sort(key=lambda x: x.step_number)

        return LLMExecution(
            id=model.id,
            conversation_id=model.conversation_id,
            message_id=model.message_id,
            response_type=ResponseType(model.response_type),
            summary_or_content=model.summary_or_content,
            is_complete=model.is_complete,
            steps=steps,
            payloads=model.payloads or {},
            created_at=model.created_at,
        )

    def save(self, execution: LLMExecution) -> LLMExecution:
        """Persists or updates an LLMExecution state and its associated steps in the database."""
        try:
            model: LLMExecutionModel | None = None
            if execution.id:
                model = db.session.get(LLMExecutionModel, execution.id)

            if not model:
                model = LLMExecutionModel(
                    id=execution.id,
                    conversation_id=execution.conversation_id,
                    message_id=execution.message_id,
                    response_type=execution.response_type,
                    summary_or_content=execution.summary_or_content,
                    is_complete=execution.is_complete,
                    payloads=execution.payloads or {},
                    created_at=execution.created_at,
                )
                db.session.add(model)
            else:
                model.conversation_id = execution.conversation_id
                model.message_id = execution.message_id
                model.response_type = execution.response_type
                model.summary_or_content = execution.summary_or_content
                model.is_complete = execution.is_complete
                model.payloads = execution.payloads or {}

            existing_steps = {step_model.step_number: step_model for step_model in model.steps}

            for step in execution.steps:
                status_val = step.status if isinstance(step.status, ExecutionStepStatus) else ExecutionStepStatus(step.status)

                if step.step_number in existing_steps:
                    step_model = existing_steps[step.step_number]
                    step_model.description = step.description
                    step_model.tool_name = step.tool_name
                    step_model.parameters = step.parameters
                    step_model.status = status_val
                    step_model.result = step.result
                else:
                    new_step_model = LLMExecutionStepModel(
                        id=step.id,
                        execution_id=execution.id,
                        step_number=step.step_number,
                        description=step.description,
                        tool_name=step.tool_name,
                        parameters=step.parameters,
                        status=status_val,
                        result=step.result,
                    )
                    model.steps.append(new_step_model)

            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save LLMExecution '%s': %s", execution.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving LLMExecution '{execution.id}': {exc}") from exc

    def update_step(
        self,
        execution_id: str,
        step_number: int,
        status: ExecutionStepStatus | str,
        result: str | None = None,
    ) -> bool:
        """Selectively updates the status and result of an individual execution step row.

        Args:
            execution_id (str): Target LLMExecution UUID.
            step_number (int): Order index of the step.
            status (ExecutionStepStatus | str): New step execution state.
            result (str | None): Optional execution output string.

        Returns:
            bool: True if row updated, False if step not found.

        Raises:
            StorageError: If database update fails.
        """
        try:
            status_enum = status if isinstance(status, ExecutionStepStatus) else ExecutionStepStatus(status)

            step_model = (
                LLMExecutionStepModel.query.filter(
                    LLMExecutionStepModel.execution_id == execution_id,
                    LLMExecutionStepModel.step_number == step_number,
                ).first()
            )

            if not step_model:
                logger.warning(
                    "Attempted to update non-existent step %d for execution '%s'.",
                    step_number,
                    execution_id,
                )
                return False

            step_model.status = status_enum
            if result is not None:
                step_model.result = result

            db.session.commit()
            return True

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error(
                "Failed to update step %d for execution '%s': %s",
                step_number,
                execution_id,
                exc,
                exc_info=True,
            )
            raise StorageError(f"Database error updating step {step_number} for execution '{execution_id}': {exc}") from exc

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
