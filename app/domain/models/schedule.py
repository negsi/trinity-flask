"""Domain models for Agent Schedules and Schedule Executions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.enums import ScheduleExecutionStatus, ScheduleTriggerType
from app.domain.errors import ValidationError


@dataclass(slots=True)
class ScheduleExecution:
    """Domain model representing a single historical run of a schedule."""

    schedule_id: str
    resolved_prompt: str
    status: ScheduleExecutionStatus = ScheduleExecutionStatus.RUNNING
    conversation_id: str | None = None
    error_message: str | None = None
    finished_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.schedule_id or not self.schedule_id.strip():
            raise ValidationError("Schedule ID cannot be empty.")
        if not self.resolved_prompt or not self.resolved_prompt.strip():
            raise ValidationError("Resolved prompt cannot be empty.")

        if isinstance(self.status, str):
            try:
                object.__setattr__(
                    self, "status", ScheduleExecutionStatus(self.status)
                )
            except ValueError as exc:
                raise ValidationError(
                    f"Invalid schedule execution status: '{self.status}'."
                ) from exc

    def to_dict(self) -> dict[str, Any]:
        """Serializes the schedule execution domain entity to a dictionary."""
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "conversation_id": self.conversation_id,
            "status": self.status.value,
            "resolved_prompt": self.resolved_prompt,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


@dataclass(slots=True)
class Schedule:
    """Domain model representing a scheduled prompt execution plan for an agent."""

    agent_id: str
    name: str
    prompt: str
    trigger_type: ScheduleTriggerType = ScheduleTriggerType.CRON
    is_active: bool = True
    cron_expression: str | None = None
    scheduled_at: datetime | None = None
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.agent_id or not self.agent_id.strip():
            raise ValidationError("Agent ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise ValidationError("Schedule name cannot be empty.")
        if not self.prompt or not self.prompt.strip():
            raise ValidationError("Schedule prompt cannot be empty.")

        if isinstance(self.trigger_type, str):
            try:
                object.__setattr__(
                    self, "trigger_type", ScheduleTriggerType(self.trigger_type)
                )
            except ValueError as exc:
                raise ValidationError(
                    f"Invalid schedule trigger type: '{self.trigger_type}'."
                ) from exc

        if self.trigger_type == ScheduleTriggerType.CRON:
            if not self.cron_expression or not self.cron_expression.strip():
                raise ValidationError(
                    "Cron expression is required when trigger_type is 'cron'."
                )
        elif self.trigger_type == ScheduleTriggerType.ONCE:
            if self.scheduled_at is None:
                raise ValidationError(
                    "scheduled_at timestamp is required when trigger_type is 'once'."
                )

    def to_dict(self) -> dict[str, Any]:
        """Serializes the schedule domain entity to a dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "prompt": self.prompt,
            "is_active": self.is_active,
            "trigger_type": self.trigger_type.value,
            "cron_expression": self.cron_expression,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
