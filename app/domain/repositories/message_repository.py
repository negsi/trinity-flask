"""
Message Repository Interface Module.

Defines abstract operations for storing and fetching chat messages.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.message import Message


class MessageRepository(ABC):
    """Abstract repository contract for chat Message objects."""

    @abstractmethod
    def save(self, message: Message) -> Message:
        """Saves or updates a Message model."""
        pass

    @abstractmethod
    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Retrieves a Message by its unique ID."""
        pass

    @abstractmethod
    def get_by_conversation(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Retrieves messages for a given conversation ID up to the specified limit."""
        pass
