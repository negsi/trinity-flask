"""
Messaging Application Service.

Handles message dispatching, listener notifications, attachment processing, and conversation creation logic.
"""

from typing import Callable, List, Optional
from werkzeug.datastructures import FileStorage

from app.domain.models.message import Message, ActorType
from app.domain.models.conversation import Conversation
from app.domain.repositories.message_repository import MessageRepository
from app.domain.repositories.conversation_repository import ConversationRepository
from app.services.message_attachment_service import MessageAttachmentService


class MessagingService:
    """Service managing message creation, database storage, and event distribution."""

    def __init__(
        self, 
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        attachment_service: Optional[MessageAttachmentService] = None
    ):
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
            files: Optional[List[FileStorage]] = None
        ) -> Message:
        """
        Persists a message and its optional file attachments in storage and triggers observer notifications.

        Args:
            conversation_id (Optional[str]): Existing conversation ID or None.
            sender_id (str): Author entity ID.
            sender_type (ActorType): Message sender category.
            sender_name (str): Author display name.
            text (str): Message text payload.
            recipient_id (str, optional): Recipient entity ID.
            files (List[FileStorage], optional): List of uploaded file objects.

        Returns:
            Message: The saved message model.
        """
        if not conversation_id:
            new_conv = Conversation(title=f"Chat started by {sender_name}")
            self.conversation_repo.save(new_conv)
            conversation_id = new_conv.id
        
        attachments = []
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
            attachments=attachments
        )

        saved_message = self.message_repo.save(message)
        
        if sender_type != ActorType.SYSTEM:
            self._notify_listeners(saved_message)
            
        return saved_message

    def update_message_text(self, message_id: str, text: str) -> Optional[Message]:
        """Updates the text content of an existing message in the database."""
        message = self.message_repo.get_by_id(message_id)
        if not message:
            print(f"[MessagingService] Message with ID {message_id} not found.")
            return None

        message.text = text
        return self.message_repo.save(message)

    def _notify_listeners(self, message: Message) -> None:
        """Notifies registered listener callbacks."""
        for listener in self._message_listeners:
            try:
                listener(message)
            except Exception as e:
                print(f"ERROR notifying message listener: {e}")
                