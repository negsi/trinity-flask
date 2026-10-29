"""Abstract repository interface for Schedule and ScheduleExecution persistence."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.schedule import Schedule, ScheduleExecution


class ScheduleRepository(ABC):
    """Abstract Base Class for Schedule persistence."""

    @abstractmethod
    def save(self, schedule: Schedule) -> Schedule:
        pass

    @abstractmethod
    def get_by_id(self, schedule_id: str) -> Schedule | None:
        pass

    @abstractmethod
    def get_all(self) -> list[Schedule]:
        pass

    @abstractmethod
    def get_by_agent_id(self, agent_id: str) -> list[Schedule]:
        pass

    @abstractmethod
    def get_due_schedules(self, now: datetime) -> list[Schedule]:
        pass

    @abstractmethod
    def delete(self, schedule_id: str) -> bool:
        pass

    @abstractmethod
    def save_execution(self, execution: ScheduleExecution) -> ScheduleExecution:
        pass

    @abstractmethod
    def get_executions_by_schedule_id(
        self, schedule_id: str, limit: int = 50
    ) -> list[ScheduleExecution]:
        pass
