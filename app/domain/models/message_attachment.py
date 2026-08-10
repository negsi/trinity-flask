"""
MessageAttachment Domain Model.

Represents an uploaded file attached to a specific chat message.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class MessageAttachment:
    """Domain entity representing a file attached to a chat message."""
    name: str              # Display name (z. B. "quartalszahlen.pdf")
    filename: str          # Systemname auf Disk mit UUID-Präfix
    file_path: str         # Absoluter oder relativer Pfad auf Disk
    mime_type: str         # MIME-Type (z. B. "application/pdf")
    file_size: int         # Dateigröße in Bytes
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serializes the attachment entity to a standard dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "message_id": self.message_id
        }