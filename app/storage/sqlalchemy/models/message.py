"""SQLAlchemy ORM models for persisted chat messages, attachments, and sequenced thoughts."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.enums import ActorType
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageThoughtModel(db.Model):
    """SQLAlchemy ORM model for individual thought blocks within a message."""

    __tablename__ = "message_thoughts"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content = Column(Text, nullable=False)
    sequence_index = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    # Relationships
    message = relationship("MessageModel", back_populates="thoughts")

    def __repr__(self) -> str:
        return (
            f"<MessageThoughtModel id='{self.id}' message_id='{self.message_id}' "
            f"sequence_index={self.sequence_index}>"
        )


class MessageAttachmentModel(db.Model):
    """SQLAlchemy ORM model for file attachments linked to a message."""

    __tablename__ = "message_attachments"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    # Relationships
    message = relationship("MessageModel", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<MessageAttachmentModel id='{self.id}' filename='{self.filename}'>"


class MessageModel(db.Model):
    """SQLAlchemy ORM model for chat messages."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(String(36), nullable=False, index=True)
    sender_type = Column(SQLEnum(ActorType), nullable=False)
    sender_name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    recipient_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    attachments = relationship(
        "MessageAttachmentModel",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    thoughts = relationship(
        "MessageThoughtModel",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageThoughtModel.sequence_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MessageModel id='{self.id}' sender_name='{self.sender_name}'>"