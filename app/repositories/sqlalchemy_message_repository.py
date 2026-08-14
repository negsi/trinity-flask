"""SQLAlchemy Message Repository Implementation Module.

Handles persistence, query operations, dynamic pagination, and attachment synchronization
for Message domain models.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.domain.enums import ActorType
from app.domain.errors import StorageError
from app.domain.models.message import Message, MessageAttachment
from app.domain.repositories.message_repository import MessageRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import MessageAttachmentModel, MessageModel

logger = logging.getLogger(__name__)


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy-backed implementation of the MessageRepository interface."""

    def _to_domain(self, model: MessageModel) -> Message:
        """Maps an ORM MessageModel instance to a Message domain entity.

        Args:
            model (MessageModel): SQLAlchemy message model.

        Returns:
            Message: Clean domain entity.
        """
        attachments = [
            MessageAttachment(
                id=att.id,
                name=att.name,
                filename=att.filename,
                file_path=att.file_path,
                mime_type=att.mime_type,
                file_size=att.file_size,
                message_id=att.message_id,
                created_at=att.created_at,
            )
            for att in (model.attachments or [])
        ]

        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            sender_id=model.sender_id,
            sender_type=model.sender_type,
            sender_name=model.sender_name,
            text=model.text,
            recipient_id=model.recipient_id,
            attachments=attachments,
            timestamp=model.timestamp,
        )

    def save(self, message: Message) -> Message:
        """Persists or updates a message along with its attached files in the database.

        Args:
            message (Message): The message domain model.

        Returns:
            Message: The saved domain entity.

        Raises:
            StorageError: If persistence encounters a database error.
        """
        try:
            model: MessageModel | None = None
            if message.id:
                model = db.session.get(MessageModel, message.id)

            if not model:
                model = MessageModel(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    sender_id=message.sender_id,
                    sender_type=message.sender_type,
                    sender_name=message.sender_name,
                    text=message.text,
                    recipient_id=message.recipient_id,
                    timestamp=message.timestamp,
                )
                db.session.add(model)
            else:
                model.conversation_id = message.conversation_id
                model.sender_id = message.sender_id
                model.sender_type = message.sender_type
                model.sender_name = message.sender_name
                model.text = message.text
                model.recipient_id = message.recipient_id
                model.timestamp = message.timestamp

            # Synchronize message attachments
            synced_attachments: list[MessageAttachmentModel] = []
            for att in message.attachments:
                att_model = db.session.get(MessageAttachmentModel, att.id)
                if att_model:
                    att_model.name = att.name
                    att_model.filename = att.filename
                    att_model.file_path = att.file_path
                    att_model.mime_type = att.mime_type
                    att_model.file_size = att.file_size
                    att_model.message_id = model.id
                else:
                    att_model = MessageAttachmentModel(
                        id=att.id,
                        name=att.name,
                        filename=att.filename,
                        file_path=att.file_path,
                        mime_type=att.mime_type,
                        file_size=att.file_size,
                        message_id=model.id,
                        created_at=att.created_at,
                    )
                synced_attachments.append(att_model)

            model.attachments = synced_attachments
            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Message '%s': %s", message.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Message '{message.id}': {exc}") from exc

    def get_by_id(self, message_id: str) -> Message | None:
        """Retrieves a message by its unique primary key ID.

        Args:
            message_id (str): UUID identifier.

        Returns:
            Message | None: Domain entity if found, else None.

        Raises:
            StorageError: If database retrieval fails.
        """
        try:
            model = db.session.get(MessageModel, message_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Message '%s': %s", message_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Message '{message_id}': {exc}") from exc

    def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Fetches messages for a conversation ordered chronologically ascending.

        Calculates offset dynamically to retrieve the latest messages if offset is not specified.

        Args:
            conversation_id (str): Associated conversation UUID.
            limit (int): Max number of messages to return.
            offset (int): Starting record offset.

        Returns:
            list[Message]: List of domain messages.

        Raises:
            StorageError: If the query fails.
        """
        try:
            total = self.count_by_conversation(conversation_id)
            calculated_offset = offset if offset > 0 else max(0, total - limit)

            models = (
                MessageModel.query.filter(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.timestamp.asc())
                .offset(calculated_offset)
                .limit(limit)
                .all()
            )
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving messages for Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error fetching messages for Conversation '{conversation_id}': {exc}") from exc

    def count_by_conversation(self, conversation_id: str) -> int:
        """Returns the total number of messages recorded for a conversation.

        Args:
            conversation_id (str): Conversation UUID.

        Returns:
            int: Message count.

        Raises:
            StorageError: If counting fails.
        """
        try:
            return MessageModel.query.filter(
                MessageModel.conversation_id == conversation_id
            ).count()
        except SQLAlchemyError as exc:
            logger.error("Error counting messages for Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error counting messages for Conversation '{conversation_id}': {exc}") from exc

    def delete(self, message_id: str) -> bool:
        """Deletes a message record by its unique ID.

        Args:
            message_id (str): Target message UUID.

        Returns:
            bool: True if removed, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        try:
            model = db.session.get(MessageModel, message_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Message '%s': %s", message_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Message '{message_id}': {exc}") from exc
