# File: app/services/messaging_service.py
"""
Messaging Application Service Module.

Handles message dispatching, listener notifications, attachment linking,
and conversation lifecycle management.
"""

import logging
from typing import Callable, List, Optional
import uuid
from werkzeug.datastructures import FileStorage

from app.domain.enums import ActorType
from app.domain.errors import ConversationNotFoundError, MessageNotFoundError
from app.domain.models.conversation import Conversation
from app.domain.models.message import Message
from app.domain.models.message_attachment import MessageAttachment
from app.domain.repositories.conversation_repository import ConversationRepository
from app.domain.repositories.message_repository import MessageRepository
from app.services.message_attachment_service import MessageAttachmentService

logger = logging.getLogger(__name__)


class MessagingService:
    """Service managing conversations, messages, attachments, and event subscriptions."""

    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        attachment_service: Optional[MessageAttachmentService] = None,
    ) -> None:
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.attachment_service = attachment_service
        self._message_listeners: List[Callable[[Message], None]] = []

    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """Registers an observer callback for incoming message events."""
        self._message_listeners.append(callback)

    def send_message(
        self,
        conversation_id: Optional[str],
        sender_id: str,
        sender_type: ActorType,
        sender_name: str,
        text: str,
        recipient_id: Optional[str] = None,
        files: Optional[List[FileStorage]] = None,
    ) -> Message:
        """
        Persists a message and its optional file attachments, then triggers observers.

        Args:
            conversation_id (Optional[str]): Existing conversation ID or None.
            sender_id (str): Author entity ID.
            sender_type (ActorType): Message sender category.
            sender_name (str): Author display name.
            text (str): Message text payload.
            recipient_id (Optional[str]): Recipient entity ID.
            files (Optional[List[FileStorage]]): List of uploaded files.

        Returns:
            Message: The persisted message model.
        """
        existing_conv = (
            self.conversation_repo.get_by_id(conversation_id)
            if conversation_id
            else None
        )

        if not existing_conv:
            new_conv = Conversation(
                id=conversation_id or str(uuid.uuid4()),
                agent_id=recipient_id,
                title=f"Chat gestartet von {sender_name}",
            )
            saved_conv = self.conversation_repo.save(new_conv)
            conversation_id = saved_conv.id

        attachments: List[MessageAttachment] = []
        if files and self.attachment_service:
            for file in files:
                if file and file.filename:
                    attachment = self.attachment_service.save_attachment_file(file)
                    attachments.append(attachment)

        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            sender_name=sender_name,
            text=text,
            recipient_id=recipient_id,
            attachments=attachments,
        )

        saved_message = self.message_repo.save(message)

        if sender_type != ActorType.SYSTEM:
            self._notify_listeners(saved_message)

        return saved_message

    def get_conversations_by_agent(self, agent_id: str) -> List[Conversation]:
        """
        Retrieves all conversations associated with a specific agent ID.

        Args:
            agent_id (str): Agent identifier.

        Returns:
            List[Conversation]: Matching conversation models.
        """
        return self.conversation_repo.get_by_agent_id(agent_id)

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> List[Message]:
        """Retrieves messages for a conversation up to the given limit."""
        return self.message_repo.get_by_conversation(conversation_id, limit=limit)

    def get_latest_user_attachments(
        self,
        conversation_id: str,
    ) -> List[MessageAttachment]:
        """Retrieves attachments from the most recent user message in a conversation."""
        if not conversation_id:
            return []
        try:
            messages = self.message_repo.get_by_conversation(conversation_id)
            user_messages = [m for m in messages if m.sender_type == ActorType.USER]
            if user_messages:
                return user_messages[-1].attachments or []
        except Exception as e:
            logger.error(
                "Error fetching attachments for conversation '%s': %s",
                conversation_id,
                e,
                exc_info=True,
            )
        return []

    def update_message_text(
        self,
        message_id: str,
        text: str,
    ) -> Message:
        """
        Updates the text content of an existing message.

        Raises:
            MessageNotFoundError: If the message ID does not exist.
        """
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(f"Message with ID '{message_id}' not found.")

        message.text = text
        return self.message_repo.save(message)

    def _notify_listeners(self, message: Message) -> None:
        """Notifies all registered listener callbacks of a new message."""
        for listener in self._message_listeners:
            try:
                listener(message)
            except Exception as e:
                logger.error("Error notifying message listener: %s", e, exc_info=True)

    def create_conversation(
        self,
        agent_id: str,
        title: Optional[str] = None,
    ) -> Conversation:
        """Creates and persists a new conversation associated with an agent."""
        conv_title = title or "Neue Konversation"
        new_conv = Conversation(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            title=conv_title,
        )
        return self.conversation_repo.save(new_conv)

    def get_conversation_by_id(
        self,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """Retrieves a conversation by ID."""
        return self.conversation_repo.get_by_id(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deletes a conversation entity by its ID.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ConversationNotFoundError(
                f"Conversation with ID '{conversation_id}' was not found."
            )

        self.conversation_repo.delete(conversation_id)
        logger.info("Successfully deleted conversation: %s", conversation_id)
        return True
