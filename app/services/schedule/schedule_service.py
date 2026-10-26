"""Schedule Service Module.

Manages agent schedule lifecycle, cron expression validation, next run calculation,
and scheduled task execution via Conversation and AgentOrchestrator.
"""

from datetime import datetime, timezone
import logging

from croniter import CroniterBadCronError, croniter

from app.domain.enums import (
    ActorType,
    ScheduleExecutionStatus,
    ScheduleTriggerType,
)
from app.domain.errors import NotFoundError, ValidationError
from app.domain.models.schedule import Schedule, ScheduleExecution
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.schedule_repository import ScheduleRepository
from app.services.agent.agent_orchestrator import AgentOrchestrator
from app.services.messaging.messaging_service import MessagingService

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service orchestrating schedule CRUD operations and prompt executions."""

    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        agent_repo: AgentRepository,
        messaging_service: MessagingService,
        agent_orchestrator: AgentOrchestrator,
    ) -> None:
        self.schedule_repo = schedule_repo
        self.agent_repo = agent_repo
        self.messaging_service = messaging_service
        self.agent_orchestrator = agent_orchestrator

    @staticmethod
    def calculate_next_run(
        trigger_type: ScheduleTriggerType,
        cron_expression: str | None,
        scheduled_at: datetime | None,
        is_active: bool,
        base_time: datetime | None = None,
    ) -> datetime | None:
        """Calculates the next UTC execution timestamp based on trigger settings."""
        if not is_active:
            return None

        now = base_time or datetime.now(timezone.utc)

        if trigger_type == ScheduleTriggerType.CRON:
            if not cron_expression or not cron_expression.strip():
                raise ValidationError(
                    "Cron expression is required for trigger_type 'cron'."
                )
            try:
                itr = croniter(cron_expression.strip(), now)
                next_dt = itr.get_next(datetime)
                if next_dt.tzinfo is None:
                    next_dt = next_dt.replace(tzinfo=timezone.utc)
                return next_dt.astimezone(timezone.utc)
            except (CroniterBadCronError, ValueError, KeyError) as exc:
                raise ValidationError(
                    f"Invalid cron expression '{cron_expression}': {exc}"
                ) from exc

        if trigger_type == ScheduleTriggerType.ONCE:
            if scheduled_at is None:
                raise ValidationError(
                    "scheduled_at is required for trigger_type 'once'."
                )
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            return scheduled_at.astimezone(timezone.utc)

        return None

    def create_schedule(
        self,
        agent_id: str,
        name: str,
        prompt: str,
        trigger_type: str | ScheduleTriggerType = ScheduleTriggerType.CRON,
        is_active: bool = True,
        cron_expression: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> Schedule:
        """Creates and persists a new schedule for an agent."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        parsed_trigger = (
            ScheduleTriggerType(trigger_type)
            if isinstance(trigger_type, str)
            else trigger_type
        )

        next_run_at = self.calculate_next_run(
            trigger_type=parsed_trigger,
            cron_expression=cron_expression,
            scheduled_at=scheduled_at,
            is_active=is_active,
        )

        schedule = Schedule(
            agent_id=agent_id,
            name=name,
            prompt=prompt,
            trigger_type=parsed_trigger,
            is_active=is_active,
            cron_expression=cron_expression.strip() if cron_expression else None,
            scheduled_at=scheduled_at,
            next_run_at=next_run_at,
        )
        return self.schedule_repo.save(schedule)

    def get_schedule(self, schedule_id: str) -> Schedule:
        """Retrieves a single schedule by ID."""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise NotFoundError(f"Schedule with ID '{schedule_id}' not found.")
        return schedule

    def get_schedules_for_agent(self, agent_id: str) -> list[Schedule]:
        """Retrieves all schedules configured for a specific agent."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")
        return self.schedule_repo.get_by_agent_id(agent_id)

    def update_schedule(
        self,
        schedule_id: str,
        name: str | None = None,
        prompt: str | None = None,
        trigger_type: str | ScheduleTriggerType | None = None,
        is_active: bool | None = None,
        cron_expression: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> Schedule:
        """Updates an existing schedule and recalculates its next execution time."""
        schedule = self.get_schedule(schedule_id)

        new_name = name if name is not None else schedule.name
        new_prompt = prompt if prompt is not None else schedule.prompt
        new_is_active = is_active if is_active is not None else schedule.is_active

        if trigger_type is not None:
            new_trigger_type = (
                ScheduleTriggerType(trigger_type)
                if isinstance(trigger_type, str)
                else trigger_type
            )
        else:
            new_trigger_type = schedule.trigger_type

        new_cron = (
            cron_expression.strip()
            if cron_expression is not None
            else schedule.cron_expression
        )
        new_scheduled_at = (
            scheduled_at if scheduled_at is not None else schedule.scheduled_at
        )

        if new_trigger_type == ScheduleTriggerType.ONCE:
            new_cron = None
        elif new_trigger_type == ScheduleTriggerType.CRON:
            new_scheduled_at = None

        next_run_at = self.calculate_next_run(
            trigger_type=new_trigger_type,
            cron_expression=new_cron,
            scheduled_at=new_scheduled_at,
            is_active=new_is_active,
        )

        updated_schedule = Schedule(
            id=schedule.id,
            agent_id=schedule.agent_id,
            name=new_name,
            prompt=new_prompt,
            trigger_type=new_trigger_type,
            is_active=new_is_active,
            cron_expression=new_cron,
            scheduled_at=new_scheduled_at,
            next_run_at=next_run_at,
            last_run_at=schedule.last_run_at,
            created_at=schedule.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        return self.schedule_repo.save(updated_schedule)

    def delete_schedule(self, schedule_id: str) -> None:
        """Deletes a schedule by ID."""
        deleted = self.schedule_repo.delete(schedule_id)
        if not deleted:
            raise NotFoundError(f"Schedule with ID '{schedule_id}' not found.")

    def get_executions(
        self, schedule_id: str, limit: int = 50
    ) -> list[ScheduleExecution]:
        """Returns the execution history for a given schedule."""
        self.get_schedule(schedule_id)
        return self.schedule_repo.get_executions_by_schedule_id(
            schedule_id=schedule_id, limit=limit
        )

    def execute_schedule(
        self, schedule_id: str, manual_trigger: bool = False
    ) -> ScheduleExecution:
        """Executes a schedule by creating a new conversation and invoking the AgentOrchestrator."""
        schedule = self.get_schedule(schedule_id)
        agent = self.agent_repo.get_by_id(schedule.agent_id)
        if not agent:
            raise NotFoundError(
                f"Target Agent '{schedule.agent_id}' for Schedule '{schedule.id}' not found."
            )

        now = datetime.now(timezone.utc)
        resolved_prompt = schedule.prompt

        # Advance schedule timestamps before running to avoid duplicate triggers
        schedule.last_run_at = now
        if not manual_trigger:
            if schedule.trigger_type == ScheduleTriggerType.ONCE:
                schedule.is_active = False
                schedule.next_run_at = None
            elif schedule.trigger_type == ScheduleTriggerType.CRON:
                schedule.next_run_at = self.calculate_next_run(
                    trigger_type=schedule.trigger_type,
                    cron_expression=schedule.cron_expression,
                    scheduled_at=schedule.scheduled_at,
                    is_active=schedule.is_active,
                    base_time=now,
                )
        self.schedule_repo.save(schedule)

        # Create initial execution log entry
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            resolved_prompt=resolved_prompt,
            status=ScheduleExecutionStatus.RUNNING,
            started_at=now,
        )
        execution = self.schedule_repo.save_execution(execution)

        try:
            # 1. Create a dedicated conversation for this scheduled run
            timestamp_label = now.strftime("%Y-%m-%d %H:%M UTC")
            conversation_title = f"[Schedule] {schedule.name} ({timestamp_label})"

            conversation = self.messaging_service.create_conversation(
                agent_id=agent.id,
                title=conversation_title,
            )
            execution.conversation_id = conversation.id
            self.schedule_repo.save_execution(execution)

            # 2. Persist the initial user/schedule prompt message in the conversation
            self.messaging_service.send_message(
                conversation_id=conversation.id,
                sender_id="scheduler",
                sender_type=ActorType.USER,
                sender_name="Scheduler",
                text=resolved_prompt,
                recipient_id=agent.id,
            )

            # 3. Run the full AgentOrchestrator ReAct & Task-Chain stream to completion
            stream_gen = self.agent_orchestrator.stream_agent_response(
                user_text=resolved_prompt,
                conversation_id=conversation.id,
                agent_id=agent.id,
                agent_name=agent.name,
                user_id="scheduler",
                call_depth=0,
            )
            for _ in stream_gen:
                pass

            execution.status = ScheduleExecutionStatus.SUCCESS
            execution.finished_at = datetime.now(timezone.utc)
            return self.schedule_repo.save_execution(execution)

        except Exception as exc:
            logger.error(
                "Scheduled execution failed for schedule '%s': %s",
                schedule.id,
                exc,
                exc_info=True,
            )
            execution.status = ScheduleExecutionStatus.FAILED
            execution.error_message = str(exc)
            execution.finished_at = datetime.now(timezone.utc)
            return self.schedule_repo.save_execution(execution)
