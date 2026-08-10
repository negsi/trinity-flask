"""
SQLAlchemy Message Repository Implementation.

Handles persistence and query operations for chat messages and their attachments.
"""

from app.domain.enums import ActorType
from app.domain.models.message import Message
from app.domain.models.message_attachment import MessageAttachment
from app.domain.repositories.message_repository import MessageRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models.message import MessageModel
from app.storage.sqlalchemy.models.message_attachment import MessageAttachmentModel


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy database implementation for chat message operations."""

    def _to_domain(self, db_msg: MessageModel) -> Message:
        """Converts an ORM model instance into a domain Message entity."""
        attachments = [
            MessageAttachment(
                id=att_model.id,
                name=att_model.name,
                filename=att_model.filename,
                file_path=att_model.file_path,
                mime_type=att_model.mime_type,
                file_size=att_model.file_size,
                message_id=att_model.message_id,
            )
            for att_model in getattr(db_msg, "attachments", [])
        ]

        raw_sender_type = (
            db_msg.sender_type.value
            if isinstance(db_msg.sender_type, ActorType)
            else db_msg.sender_type
        )

        return Message(
            id=db_msg.id,
            conversation_id=db_msg.conversation_id,
            sender_id=db_msg.sender_id,
            sender_type=ActorType(raw_sender_type),
            sender_name=db_msg.sender_name,
            text=db_msg.text,
            recipient_id=db_msg.recipient_id,
            attachments=attachments,
            timestamp=db_msg.timestamp,
        )

    def save(self, message: Message) -> Message:
        """Persists or updates a message record along with attached files."""
        db_msg = db.session.get(MessageModel, message.id) if message.id else None

        sender_type_val = (
            message.sender_type.value
            if isinstance(message.sender_type, ActorType)
            else message.sender_type
        )

        if not db_msg:
            db_msg = MessageModel(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_id=message.sender_id,
                sender_type=sender_type_val,
                sender_name=message.sender_name,
                text=message.text,
                recipient_id=message.recipient_id,
                timestamp=message.timestamp,
            )
            db.session.add(db_msg)
        else:
            db_msg.conversation_id = message.conversation_id
            db_msg.sender_id = message.sender_id
            db_msg.sender_type = sender_type_val
            db_msg.sender_name = message.sender_name
            db_msg.text = message.text
            db_msg.recipient_id = message.recipient_id
            db_msg.timestamp = message.timestamp

        # Synchronize message attachments with ORM models
        db_msg.attachments = [
            db.session.get(MessageAttachmentModel, att.id)
            or MessageAttachmentModel(
                id=att.id,
                name=att.name,
                filename=att.filename,
                file_path=att.file_path,
                mime_type=att.mime_type,
                file_size=att.file_size,
                message_id=db_msg.id,
            )
            for att in message.attachments
        ]

        db.session.commit()
        return self._to_domain(db_msg)

    def get_by_id(self, message_id: str) -> Message | None:
        """Fetches a message by ID."""
        db_msg = db.session.get(MessageModel, message_id)
        return self._to_domain(db_msg) if db_msg else None

    def get_by_conversation(
        self, conversation_id: str, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        """
        Fetches recent message history for a conversation ID.
        Calculates offset dynamically to retrieve the most recent limit of messages if offset is unassigned.
        """
        total = self.count_by_conversation(conversation_id)
        calculated_offset = offset if offset > 0 else max(0, total - limit)

        db_messages = (
            MessageModel.query.filter(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.timestamp.asc())
            .offset(calculated_offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in db_messages]

    def count_by_conversation(self, conversation_id: str) -> int:
        """Returns total message count for a given conversation."""
        return MessageModel.query.filter(
            MessageModel.conversation_id == conversation_id
        ).count()
