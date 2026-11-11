"""Abstract repository interface for Workflow persistence."""

from abc import ABC, abstractmethod
from app.domain.models.workflow import Workflow


class WorkflowRepository(ABC):
    """Abstract Base Class for Workflow persistence."""

    @abstractmethod
    def save(self, workflow: Workflow) -> Workflow:
        """Persists (creates or updates) a workflow entity."""
        pass

    @abstractmethod
    def get_by_id(self, workflow_id: str) -> Workflow | None:
        """Retrieves a workflow by its unique identifier."""
        pass

    @abstractmethod
    def get_all(self) -> list[Workflow]:
        """Retrieves all stored workflows ordered by last update."""
        pass

    @abstractmethod
    def delete(self, workflow_id: str) -> bool:
        """Deletes a workflow by its unique identifier."""
        pass