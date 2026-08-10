"""
SQLAlchemy MessageAttachment ORM Model.

Defines the database schema for stored chat message attachment metadata.
"""

from app.storage.sqlalchemy.db import db


class MessageAttachmentModel(db.Model):
    """SQLAlchemy model representing the message_attachments table."""

    __tablename__ = "message_attachments"

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(128), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)

    # Foreign Key zu der Message
    message_id = db.Column(db.String(36), db.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        return f"<MessageAttachmentModel {self.name} ({self.id})>"