"""
SQLAlchemy Message Repository Implementation.

Handles persistence, retrieval, and mapping of Message domain entities in the database.
"""

from typing import List, Optional

from app.domain.repositories.message_repository import MessageRepository
from app.domain.models.message import Message, ActorType
from app.domain.models.message_attachment import MessageAttachment
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models.message import MessageModel
from app.storage.sqlalchemy.models.message_attachment import MessageAttachmentModel


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy implementation of the MessageRepository interface."""

    def _to_domain(self, model: MessageModel) -> Message:
        """
        Maps a database ORM instance to a clean domain entity.

        Args:
            model (MessageModel): SQLAlchemy message model.

        Returns:
            Message: Mapped domain model instance.
        """
        attachments = [
            MessageAttachment(
                id=att_model.id,
                name=att_model.name,
                filename=att_model.filename,
                file_path=att_model.file_path,
                mime_type=att_model.mime_type,
                file_size=att_model.file_size,
                message_id=att_model.message_id
            )
            for att_model in getattr(model, "attachments", [])
        ]

        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            sender_id=model.sender_id,
            sender_type=ActorType(model.sender_type),
            sender_name=model.sender_name,
            text=model.text,
            recipient_id=model.recipient_id,
            attachments=attachments,
            timestamp=model.timestamp
        )

    def save(self, message: Message) -> Message:
        """Saves or updates a message domain entity in the database."""
        model = MessageModel.query.get(message.id) if message.id else None

        if not model:
            model = MessageModel(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_id=message.sender_id,
                sender_type=message.sender_type.value,
                sender_name=message.sender_name,
                text=message.text,
                recipient_id=message.recipient_id,
                timestamp=message.timestamp
            )
            db.session.add(model)
        else:
            model.conversation_id = message.conversation_id
            model.sender_id = message.sender_id
            model.sender_type = message.sender_type.value
            model.sender_name = message.sender_name
            model.text = message.text
            model.recipient_id = message.recipient_id
            model.timestamp = message.timestamp

        # Synchronize attached files (analog zu agent.datasources)
        model.attachments = [
            MessageAttachmentModel.query.get(att.id) or MessageAttachmentModel(
                id=att.id,
                name=att.name,
                filename=att.filename,
                file_path=att.file_path,
                mime_type=att.mime_type,
                file_size=att.file_size,
                message_id=model.id
            )
            for att in message.attachments
        ]

        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Fetches a message entity by its primary key ID."""
        model = MessageModel.query.get(message_id)
        if not model:
            return None
        return self._to_domain(model)

    def get_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """Fetches all messages belonging to a specific conversation, ordered chronologically."""
        models = (
            MessageModel.query
            .filter_by(conversation_id=conversation_id)
            .order_by(MessageModel.timestamp.asc())
            .all()
        )
        return [self._to_domain(m) for m in models]