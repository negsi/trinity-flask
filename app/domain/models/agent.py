"""
Agent Domain Model.

Represents an AI agent entity, its core instructions, and attached knowledge datasources.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.errors import ValidationError
from app.domain.models.datasource import Datasource


@dataclass
class Agent:
    """Domain model representing an AI agent instance."""
    name: str
    system_prompt: str = None
    description: Optional[str] = None
    datasources: List[Datasource] = field(default_factory=list)
    id: Optional[str] = None

    def to_dict(self) -> dict:
        """Converts the agent domain model to a dictionary structure for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "datasources": [ds.to_dict() for ds in self.datasources]
        }

    def __post_init__(self):
        """Validates agent parameters after initialization."""
        if not self.name or not self.name.strip():
            raise ValidationError("NAME_REQUIRED")

    def add_datasource(self, datasource: Datasource):
        """Attaches a new datasource to the agent if not already present."""
        if any(ds.id == datasource.id for ds in self.datasources):
            return
        self.datasources.append(datasource)

    def remove_datasource(self, datasource_id: str):
        """Removes an attached datasource by its ID."""
        self.datasources = [ds for ds in self.datasources if ds.id != datasource_id]
