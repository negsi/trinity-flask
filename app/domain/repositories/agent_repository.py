"""
Agent Repository Interface Module.

Defines abstract CRUD operations for persisting Agent domain entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.agent import Agent


class AgentRepository(ABC):
    """Abstract repository contract for Agent domain entities."""

    @abstractmethod
    def save(self, agent: Agent) -> Agent:
        """Persists or updates an Agent domain model."""
        pass

    @abstractmethod
    def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Retrieves an Agent entity by its unique ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Agent]:
        """Retrieves all stored Agent entities."""
        pass

    @abstractmethod
    def delete(self, agent_id: str) -> None:
        """Deletes an Agent entity by its unique ID."""
        pass
