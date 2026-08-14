"""Message and MessageAttachment Domain Models Module.

Defines chat messages, sender identities, and associated binary attachments.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.enums import ActorType
from app.domain.errors import ValidationError


@dataclass(slots=True)
class MessageAttachment:
    """Domain model representing a file attached to a chat message.

    Attributes:
        name (str): Original display name of the uploaded attachment.
        filename (str): Sanitized storage filename on disk.
        file_path (str): Absolute path to the physical file.
        mime_type (str): MIME type of the attachment payload.
        file_size (int): Size in bytes.
        id (str): Unique UUID identifier.
        message_id (str | None): ID of the parent message.
        created_at (datetime): Attachment creation timestamp.
    """

    name: str
    filename: str
    file_path: str
    mime_type: str
    file_size: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates attachment attributes.

        Raises:
            ValidationError: If attributes fail boundary checks.
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Attachment name cannot be empty.")
        if not self.filename or not self.filename.strip():
            raise ValidationError("Attachment filename cannot be empty.")
        if not self.file_path or not self.file_path.strip():
            raise ValidationError("Attachment file path cannot be empty.")
        if self.file_size < 0:
            raise ValidationError("Attachment file size cannot be negative.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the attachment model to a dictionary.

        Returns:
            dict[str, Any]: Serialized dictionary representation.
        """
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "message_id": self.message_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class Message:
    """Domain model representing an individual chat message entry.

    Attributes:
        conversation_id (str): UUID of the parent conversation.
        sender_id (str): Identifier of the sending actor.
        sender_type (ActorType): Category of the sending actor (USER, AGENT, SYSTEM).
        sender_name (str): Display name of the sender.
        text (str): Text body of the message.
        id (str): Unique UUID message identifier.
        recipient_id (str | None): Optional identifier of the targeted recipient.
        attachments (list[MessageAttachment]): Associated file attachments.
        timestamp (datetime): UTC creation timestamp.
    """

    conversation_id: str
    sender_id: str
    sender_type: ActorType
    sender_name: str
    text: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: str | None = None
    attachments: list[MessageAttachment] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates message domain constraints.

        Raises:
            ValidationError: If constraints are violated.
        """
        if not self.conversation_id or not self.conversation_id.strip():
            raise ValidationError("Message conversation_id cannot be empty.")
        if not self.sender_id or not self.sender_id.strip():
            raise ValidationError("Message sender_id cannot be empty.")
        if not self.sender_name or not self.sender_name.strip():
            raise ValidationError("Message sender_name cannot be empty.")

        if isinstance(self.sender_type, str):
            try:
                object.__setattr__(self, "sender_type", ActorType(self.sender_type))
            except ValueError:
                raise ValidationError(f"Invalid sender_type '{self.sender_type}'.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the message entity and its attachments into a dictionary.

        Returns:
            dict[str, Any]: Serialized message dictionary.
        """
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type.value,
            "sender_name": self.sender_name,
            "text": self.text,
            "recipient_id": self.recipient_id,
            "attachments": [att.to_dict() for att in self.attachments],
            "timestamp": self.timestamp.isoformat(),
        }
