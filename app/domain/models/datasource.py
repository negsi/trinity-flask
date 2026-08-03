"""
Datasource Domain Model.

Represents an uploaded document or external knowledge resource associated with an agent.
"""

import uuid
from typing import Optional


class Datasource:
    """Domain entity representing an uploaded knowledge file for agent context context injection."""

    def __init__(
        self,
        name: str,
        filename: str,
        file_path: str,
        mime_type: str,
        file_size: int,
        id: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name            # Display name in UI (e.g. "User Manual V1")
        self.filename = filename    # Disk filename with UUID prefix
        self.file_path = file_path  # Absolute storage path on disk
        self.mime_type = mime_type  # E.g. "application/pdf"
        self.file_size = file_size  # Size in Bytes
        self.agent_id = agent_id    # Associated agent ID

    def to_dict(self) -> dict:
        """Serializes the datasource entity to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "agent_id": self.agent_id
        }
