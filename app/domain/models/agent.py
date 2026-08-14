"""Agent Domain Model Module.

Defines the Agent domain entity, encapsulating identity, system prompts,
memory retention policies, and associated knowledge base datasources.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.enums import MemoryLimitType, MemoryMode
from app.domain.errors import ValidationError
from app.domain.models.datasource import Datasource


@dataclass(slots=True)
class Agent:
    """Domain model representing an autonomous AI agent instance.

    Attributes:
        name (str): Descriptive name of the agent.
        system_prompt (str | None): Base prompt guiding the agent's behavior.
        description (str | None): Short textual summary of the agent's purpose.
        datasources (list[Datasource]): Collection of attached knowledge base documents.
        memory_enabled (bool): Flag indicating whether conversation history is fed back.
        memory_mode (MemoryMode): Scope of retained messages ('user_only' or 'all').
        memory_limit_type (MemoryLimitType): Boundary strategy ('all' or 'message_count').
        memory_message_count (int | None): Max message count when limit type is 'message_count'.
        id: (str): Unique UUID string identifying the agent.
        created_at (datetime): Timestamp when the agent entity was created.
    """

    name: str
    system_prompt: str | None = None
    description: str | None = None
    datasources: list[Datasource] = field(default_factory=list)
    memory_enabled: bool = False
    memory_mode: MemoryMode = MemoryMode.USER_ONLY
    memory_limit_type: MemoryLimitType = MemoryLimitType.ALL
    memory_message_count: int | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates agent configuration rules and memory parameters.

        Raises:
            ValidationError: If configuration constraints are violated.
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Agent name cannot be empty.")

        # Normalize string inputs to proper domain enums
        if isinstance(self.memory_mode, str):
            try:
                object.__setattr__(self, "memory_mode", MemoryMode(self.memory_mode))
            except ValueError:
                raise ValidationError(f"Invalid memory mode '{self.memory_mode}'.")

        if isinstance(self.memory_limit_type, str):
            try:
                object.__setattr__(self, "memory_limit_type", MemoryLimitType(self.memory_limit_type))
            except ValueError:
                raise ValidationError(f"Invalid memory limit type '{self.memory_limit_type}'.")

        # Invariant: If bounded by message_count, count must be positive
        if self.memory_enabled and self.memory_limit_type == MemoryLimitType.MESSAGE_COUNT:
            if self.memory_message_count is None or self.memory_message_count <= 0:
                raise ValidationError("A positive memory_message_count is required when limit type is 'message_count'.")

    def attach_datasource(self, datasource: Datasource) -> None:
        """Associates a new knowledge base datasource to this agent.

        Args:
            datasource (Datasource): The datasource entity to associate.
        """
        datasource.agent_id = self.id
        self.datasources.append(datasource)

    def remove_datasource(self, datasource_id: str) -> bool:
        """Removes an associated knowledge base datasource by its ID.

        Args:
            datasource_id (str): The unique ID of the datasource to decouple.

        Returns:
            bool: True if removed, False if not present.
        """
        initial_len = len(self.datasources)
        self.datasources = [ds for ds in self.datasources if ds.id != datasource_id]
        return len(self.datasources) < initial_len

    def to_dict(self) -> dict[str, Any]:
        """Serializes the agent entity and its datasources into a dictionary representation.

        Returns:
            dict[str, Any]: Serialized dictionary payload.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "memory_enabled": self.memory_enabled,
            "memory_mode": self.memory_mode.value,
            "memory_limit_type": self.memory_limit_type.value,
            "memory_message_count": self.memory_message_count,
            "datasources": [ds.to_dict() for ds in self.datasources],
            "created_at": self.created_at.isoformat(),
        }
