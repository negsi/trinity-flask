"""Conversation Domain Model Module.

Defines the Conversation entity representing a sequence of chat interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.errors import ValidationError


@dataclass(slots=True)
class Conversation:
    """Domain model representing a multi-turn conversation session.

    Attributes:
        title (str): Title or topic summary of the conversation.
        agent_id (str | None): Identifier of the agent assigned to this conversation.
        id (str): Unique UUID identifier of the conversation.
        created_at (datetime): Timestamp when the conversation was initiated.
    """

    title: str = "Neue Konversation"
    agent_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates conversation attributes upon entity creation.

        Raises:
            ValidationError: If the title is blank.
        """
        if not self.title or not self.title.strip():
            raise ValidationError("Conversation title cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the conversation entity into a standard dictionary.

        Returns:
            dict[str, Any]: Serialized conversation dictionary.
        """
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
        }
