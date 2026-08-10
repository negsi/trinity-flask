"""
Message Domain Model.

Represents an individual chat message exchanged between users, agents, or system components.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from app.domain.models.message_attachment import MessageAttachment


class ActorType(str, Enum):
    """Enumeration of message sender entity types."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Message:
    """Domain model representing a chat message entry."""
    conversation_id: str
    sender_id: str
    sender_type: ActorType
    sender_name: str
    text: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: Optional[str] = None
    attachments: list[MessageAttachment] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serializes the message entity to a standard dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type.value,
            "sender_name": self.sender_name,
            "text": self.text,
            "recipient_id": self.recipient_id,
            "attachments": [att.to_dict() for att in self.attachments],
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        }
