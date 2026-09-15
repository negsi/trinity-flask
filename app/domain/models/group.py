"""Group Domain Model Module."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.errors import ValidationError


@dataclass(slots=True)
class Group:
    """Domain model representing an Agent Group."""

    name: str
    description: str | None = None
    agent_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Group name cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_count": self.agent_count,
            "created_at": self.created_at.isoformat(),
        }