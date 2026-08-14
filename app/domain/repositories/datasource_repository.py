"""Datasource Repository Interface Module.

Defines the abstract interface for managing knowledge base Datasource persistence.
"""

from abc import ABC, abstractmethod

from app.domain.models.datasource import Datasource


class DatasourceRepository(ABC):
    """Abstract Base Class for managing Datasource domain models."""

    @abstractmethod
    def save(self, datasource: Datasource) -> Datasource:
        """Persists or updates a Datasource entity.

        Args:
            datasource (Datasource): The datasource entity to persist.

        Returns:
            Datasource: The persisted entity.

        Raises:
            StorageError: If database persistence fails.
        """
        pass

    @abstractmethod
    def get_by_id(self, datasource_id: str) -> Datasource | None:
        """Retrieves a Datasource by its unique ID.

        Args:
            datasource_id (str): Datasource UUID.

        Returns:
            Datasource | None: The datasource model if found, else None.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_by_agent_id(self, agent_id: str) -> list[Datasource]:
        """Retrieves all datasources associated with an Agent.

        Args:
            agent_id (str): The owning Agent's UUID.

        Returns:
            list[Datasource]: List of associated datasources.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def delete(self, datasource_id: str) -> bool:
        """Deletes a Datasource record by its ID.

        Args:
            datasource_id (str): UUID of the datasource.

        Returns:
            bool: True if the record was removed, False otherwise.

        Raises:
            StorageError: If the deletion fails.
        """
        pass
