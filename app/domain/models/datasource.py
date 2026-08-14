"""Datasource Domain Model Module.

Represents an uploaded document or knowledge resource associated with an agent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.errors import ValidationError


@dataclass(slots=True)
class Datasource:
    """Domain model representing an external document attached to an Agent as knowledge.

    Attributes:
        name (str): Human-readable display name of the document.
        filename (str): Unique physical storage filename on disk.
        file_path (str): Absolute file system path to the stored document.
        mime_type (str): MIME type specification (e.g., 'application/pdf').
        file_size (int): Size of the file in bytes.
        id (str): Unique UUID identifier of the datasource entity.
        agent_id (str | None): Optional foreign UUID reference to the associated Agent.
        created_at (datetime): Timestamp when the datasource entity was created.
    """

    name: str
    filename: str
    file_path: str
    mime_type: str
    file_size: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates internal domain invariants upon entity instantiation.

        Raises:
            ValidationError: If required fields are blank or invalid.
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Datasource name cannot be empty.")
        if not self.filename or not self.filename.strip():
            raise ValidationError("Datasource filename cannot be empty.")
        if not self.file_path or not self.file_path.strip():
            raise ValidationError("Datasource file path cannot be empty.")
        if self.file_size < 0:
            raise ValidationError("Datasource file size cannot be negative.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the datasource entity to a standard dictionary format.

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
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
        }
