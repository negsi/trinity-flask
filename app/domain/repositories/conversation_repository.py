"""Conversation Repository Interface Module.

Defines the abstract contract for Conversation storage and retrieval operations.
"""

from abc import ABC, abstractmethod

from app.domain.models.conversation import Conversation


class ConversationRepository(ABC):
    """Abstract Base Class for Conversation domain entity persistence."""

    @abstractmethod
    def save(self, conversation: Conversation) -> Conversation:
        """Persists or updates a Conversation entity.

        Args:
            conversation (Conversation): Entity to persist.

        Returns:
            Conversation: The persisted conversation entity.

        Raises:
            StorageError: If the persistence operation fails.
        """
        pass

    @abstractmethod
    def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Retrieves a conversation by its unique ID.

        Args:
            conversation_id (str): UUID identifier.

        Returns:
            Conversation | None: The domain model if resolved, else None.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_by_agent_id(self, agent_id: str) -> list[Conversation]:
        """Retrieves all conversations assigned to a given Agent, sorted chronologically descending.

        Args:
            agent_id (str): Associated Agent UUID.

        Returns:
            list[Conversation]: List of associated conversations.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def list_all(self) -> list[Conversation]:
        """Lists all conversations ordered by creation date descending.

        Returns:
            list[Conversation]: Ordered list of all conversation records.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def delete(self, conversation_id: str) -> bool:
        """Deletes a conversation by its unique ID.

        Args:
            conversation_id (str): Target conversation UUID.

        Returns:
            bool: True if deleted, False if no entity was found.

        Raises:
            StorageError: If deletion encounters an error.
        """
        pass
