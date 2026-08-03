"""
Conversation Domain Model.

Represents a chat conversation thread grouping related messages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class Conversation:
    """Domain entity representing a chat conversation thread."""
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
