"""Agent Repository Interface Module.

Defines the abstract data access contract for persisting and querying Agent domain entities.
"""

from abc import ABC, abstractmethod

from app.domain.models.agent import Agent


class AgentRepository(ABC):
    """Abstract Base Class for managing Agent domain persistence."""

    @abstractmethod
    def save(self, agent: Agent) -> Agent:
        """Persists or updates an Agent domain entity.

        Args:
            agent (Agent): The domain entity to persist.

        Returns:
            Agent: The persisted and updated domain entity.

        Raises:
            StorageError: If the persistence operation fails.
        """
        pass

    @abstractmethod
    def get_by_id(self, agent_id: str) -> Agent | None:
        """Retrieves an Agent entity by its unique ID.

        Args:
            agent_id (str): Unique UUID of the agent.

        Returns:
            Agent | None: The found agent entity, or None if not found.

        Raises:
            StorageError: If database access encounters an error.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Agent]:
        """Retrieves all registered Agent entities, ordered by recent activity.

        Returns:
            list[Agent]: List of all agent domain entities.

        Raises:
            StorageError: If querying entities fails.
        """
        pass

    @abstractmethod
    def delete(self, agent_id: str) -> bool:
        """Deletes an Agent entity by its unique identifier.

        Args:
            agent_id (str): Unique UUID of the agent to delete.

        Returns:
            bool: True if the agent was found and deleted, False otherwise.

        Raises:
            StorageError: If the delete operation encounters a database error.
        """
        pass
