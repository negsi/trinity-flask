"""SQLAlchemy ORM model for message attachments."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageAttachmentModel(db.Model):
    """SQLAlchemy model representing message attachments in `message_attachments`."""

    __tablename__ = "message_attachments"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_size = Column(Integer, nullable=False)

    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    # Relationships
    message = relationship("MessageModel", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<MessageAttachmentModel id='{self.id}' filename='{self.filename}'>"
