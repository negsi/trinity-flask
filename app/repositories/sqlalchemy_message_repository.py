"""
SQLAlchemy Message Repository Implementation.

Handles persistence and query operations for chat messages.
"""

from typing import List, Optional
from app.storage.sqlalchemy.db import db
from app.domain.models.message import Message
from app.domain.repositories.message_repository import MessageRepository
from app.storage.sqlalchemy.models.message import MessageModel


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy database implementation for chat message operations."""

    def _to_domain(self, db_msg: MessageModel) -> Message:
        """Converts an ORM model instance into a domain Message entity."""
        return Message(
            id=db_msg.id,
            conversation_id=db_msg.conversation_id,
            sender_id=db_msg.sender_id,
            sender_type=db_msg.sender_type,
            sender_name=db_msg.sender_name,
            text=db_msg.text,
            recipient_id=db_msg.recipient_id,
            timestamp=db_msg.timestamp
        )

    def save(self, message: Message) -> Message:
        """Persists or updates a message record."""
        db_msg = None
        if message.id:
            db_msg = MessageModel.query.get(message.id)

        if not db_msg:
            db_msg = MessageModel(
                conversation_id=message.conversation_id,
                sender_id=message.sender_id,
                sender_type=message.sender_type,
                sender_name=message.sender_name,
                text=message.text,
                recipient_id=message.recipient_id,
                timestamp=message.timestamp
            )
            if message.id:
                db_msg.id = message.id
            db.session.add(db_msg)
        else:
            db_msg.conversation_id = message.conversation_id
            db_msg.sender_id = message.sender_id
            db_msg.sender_type = message.sender_type
            db_msg.sender_name = message.sender_name
            db_msg.text = message.text
            db_msg.recipient_id = message.recipient_id
            db_msg.timestamp = message.timestamp

        db.session.commit()
        return self._to_domain(db_msg)

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Fetches a message by ID."""
        db_msg = MessageModel.query.get(message_id)
        return self._to_domain(db_msg) if db_msg else None

    def get_by_conversation(
        self, 
        conversation_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Message]:
        """
        Fetches the recent message history for a conversation ID.
        Calculates offset dynamically to retrieve the most recent limit of messages.
        """
        total = self.count_by_conversation(conversation_id)
        offset = max(0, total - 50)
        
        db_messages = (
            MessageModel.query
            .filter(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.timestamp.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in db_messages]

    def count_by_conversation(self, conversation_id: str) -> int:
        """Returns total message count for a given conversation."""
        return MessageModel.query.filter(MessageModel.conversation_id == conversation_id).count()
