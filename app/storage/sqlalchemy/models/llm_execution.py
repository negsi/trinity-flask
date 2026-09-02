"""SQLAlchemy ORM models for LLM task executions and step progress."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.domain.enums import ExecutionStepStatus, ResponseType
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LLMExecutionModel(db.Model):
    """SQLAlchemy ORM entity for persisting ReAct task execution states in `llm_executions`."""

    __tablename__ = "llm_executions"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    response_type = Column(SQLEnum(ResponseType), nullable=False)
    summary_or_content = Column(Text, nullable=False)
    is_complete = Column(Boolean, nullable=False, default=True)
    payloads = Column(JSON, nullable=False, default=dict)  # <-- NEU für Issue #20

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="executions")
    steps = relationship(
        "LLMExecutionStepModel",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="LLMExecutionStepModel.step_number",
    )

    def __repr__(self) -> str:
        return f"<LLMExecutionModel id='{self.id}' response_type='{self.response_type}'>"


class LLMExecutionStepModel(db.Model):
    """SQLAlchemy ORM entity for individual execution steps in `llm_execution_steps`."""

    __tablename__ = "llm_execution_steps"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    execution_id = Column(
        String(36),
        ForeignKey("llm_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    tool_name = Column(String(255), nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    status = Column(
        SQLEnum(ExecutionStepStatus),
        nullable=False,
        default=ExecutionStepStatus.PENDING,
    )
    result = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    # Relationships
    execution = relationship("LLMExecutionModel", back_populates="steps")

    def __repr__(self) -> str:
        return (
            f"<LLMExecutionStepModel id='{self.id}' execution_id='{self.execution_id}' "
            f"step_number={self.step_number} status='{self.status}'>"
        )
