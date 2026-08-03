"""
Conversation Repository Interface Module.

Defines abstract operations for persisting Conversation domain entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.conversation import Conversation


class ConversationRepository(ABC):
    """Abstract repository contract for Conversation entities."""

    @abstractmethod
    def save(self, conversation: Conversation) -> Conversation:
        """Persists or updates a Conversation model."""
        pass

    @abstractmethod
    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieves a Conversation by its ID."""
        pass

    @abstractmethod
    def list_all(self) -> List[Conversation]:
        """Lists all existing Conversations."""
        pass
