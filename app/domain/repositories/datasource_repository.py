"""
Datasource Repository Interface Module.

Defines abstract CRUD operations for managing Datasource domain models.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.datasource import Datasource


class DatasourceRepository(ABC):
    """Abstract repository contract for Datasource entities."""

    @abstractmethod
    def save(self, datasource: Datasource) -> Datasource:
        """Persists or updates a Datasource record."""
        pass

    @abstractmethod
    def get_by_id(self, datasource_id: str) -> Optional[Datasource]:
        """Retrieves a Datasource by its unique ID."""
        pass

    @abstractmethod
    def delete(self, datasource_id: str) -> None:
        """Deletes a Datasource record by ID."""
        pass
