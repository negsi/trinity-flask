"""Message Repository Interface Module.

Defines the abstract contract for storing, querying, and paginating chat messages and attachments.
"""

from abc import ABC, abstractmethod

from app.domain.models.message import Message


class MessageRepository(ABC):
    """Abstract Base Class for Message domain model persistence."""

    @abstractmethod
    def save(self, message: Message) -> Message:
        """Persists or updates a chat message entity along with its attachments.

        Args:
            message (Message): The message domain model.

        Returns:
            Message: The persisted message entity.

        Raises:
            StorageError: If persistence encounters a database error.
        """
        pass

    @abstractmethod
    def get_by_id(self, message_id: str) -> Message | None:
        """Retrieves a message by its unique ID.

        Args:
            message_id (str): UUID identifier.

        Returns:
            Message | None: The domain message if resolved, else None.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Retrieves messages for a conversation ordered chronologically ascending.

        Args:
            conversation_id (str): UUID identifier of the conversation.
            limit (int): Max number of messages to return.
            offset (int): Starting record offset.

        Returns:
            list[Message]: List of retrieved message domain models.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def count_by_conversation(self, conversation_id: str) -> int:
        """Returns the total number of messages recorded for a conversation.

        Args:
            conversation_id (str): Conversation UUID identifier.

        Returns:
            int: Message count.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def delete(self, message_id: str) -> bool:
        """Deletes a message record by its unique ID.

        Args:
            message_id (str): Target message UUID.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        pass
