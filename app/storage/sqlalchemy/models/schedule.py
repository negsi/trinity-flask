"""SQLAlchemy ORM models for Schedule and ScheduleExecution entities."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.domain.enums import ScheduleExecutionStatus, ScheduleTriggerType
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ScheduleModel(db.Model):
    """SQLAlchemy ORM entity representing the `schedules` table."""

    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    trigger_type = Column(
        SQLEnum(ScheduleTriggerType),
        default=ScheduleTriggerType.CRON,
        nullable=False,
    )
    cron_expression = Column(String(100), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    # Relationships
    agent = relationship("AgentModel", back_populates="schedules")
    executions = relationship(
        "ScheduleExecutionModel",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="desc(ScheduleExecutionModel.started_at)",
    )

    def __repr__(self) -> str:
        return f"<ScheduleModel id='{self.id}' name='{self.name}' agent_id='{self.agent_id}'>"


class ScheduleExecutionModel(db.Model):
    """SQLAlchemy ORM entity representing the `schedule_executions` table."""

    __tablename__ = "schedule_executions"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    schedule_id = Column(
        String(36),
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        SQLEnum(ScheduleExecutionStatus),
        default=ScheduleExecutionStatus.RUNNING,
        nullable=False,
        index=True,
    )
    resolved_prompt = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    schedule = relationship("ScheduleModel", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ScheduleExecutionModel id='{self.id}' schedule_id='{self.schedule_id}' status='{self.status}'>"
