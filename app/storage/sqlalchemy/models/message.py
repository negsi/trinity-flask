"""SQLAlchemy ORM model for persisted chat messages."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.domain.enums import ActorType
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageModel(db.Model):
    """SQLAlchemy ORM model representing persisted chat messages in `messages`."""

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

    __table_args__ = (
        Index("ix_messages_conv_timestamp", "conversation_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<MessageModel id='{self.id}' sender='{self.sender_name}' conv='{self.conversation_id}'>"
