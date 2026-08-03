"""
SQLAlchemy LLM Execution Repository.

Stores ReAct task chain execution states and history in the database.
"""

from typing import Optional, List
from app.domain.models.llm_execution import LLMExecution, ExecutionStep, ResponseType
from app.storage.sqlalchemy.models.llm_execution import LLMExecutionModel
from app.storage.sqlalchemy.db import db


class SQLAlchemyLLMExecutionRepository:
    """Repository handling SQL persistence for LLM executions."""

    def _to_domain(self, model: LLMExecutionModel) -> LLMExecution:
        """Maps an execution ORM model back into a domain object."""
        steps = [
            ExecutionStep(
                step_number=s.get("step", 0),
                description=s.get("description", ""),
                tool_name=s.get("tool"),
                parameters=s.get("parameters", {}),
                status=s.get("status", "pending"),
                result=s.get("result")
            )
            for s in (model.steps or [])
        ]

        return LLMExecution(
            id=model.id,
            conversation_id=model.conversation_id,
            message_id=model.message_id,
            response_type=ResponseType(model.response_type),
            summary_or_content=model.summary_or_content,
            is_complete=getattr(model, "is_complete", True),
            steps=steps,
            created_at=model.created_at
        )

    def save(self, execution: LLMExecution) -> LLMExecution:
        """Saves an execution log or updates existing step states in the database."""
        model = None
        if execution.id:
            model = LLMExecutionModel.query.get(execution.id)

        steps_json = [
            {
                "step": s.step_number,
                "description": s.description,
                "tool": s.tool_name,
                "parameters": s.parameters,
                "status": s.status,
                "result": s.result
            }
            for s in execution.steps
        ]

        if not model:
            model = LLMExecutionModel(
                conversation_id=execution.conversation_id,
                message_id=execution.message_id,
                response_type=execution.response_type.value,
                summary_or_content=execution.summary_or_content,
                is_complete=execution.is_complete,
                steps=steps_json
            )
            if execution.id:
                model.id = execution.id
            db.session.add(model)
        else:
            model.response_type = execution.response_type.value
            model.summary_or_content = execution.summary_or_content
            model.is_complete = execution.is_complete
            model.steps = steps_json

        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, execution_id: str) -> Optional[LLMExecution]:
        """Fetches an execution by ID."""
        model = LLMExecutionModel.query.get(execution_id)
        return self._to_domain(model) if model else None

    def get_by_conversation(self, conversation_id: str) -> List[LLMExecution]:
        """Fetches all executions for a conversation ordered descending by timestamp."""
        models = (
            LLMExecutionModel.query
            .filter_by(conversation_id=conversation_id)
            .order_by(LLMExecutionModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]
