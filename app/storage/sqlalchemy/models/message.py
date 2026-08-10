"""
Message SQLAlchemy ORM Model.

Defines the database table layout for persisted chat messages.
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from datetime import datetime
from app.storage.sqlalchemy.db import db
from app.domain.models.message import ActorType


class MessageModel(db.Model):
    """SQLAlchemy ORM model representing the `messages` table."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    sender_id = Column(String(36), nullable=False)
    sender_type = Column(SQLEnum(ActorType), nullable=False)
    sender_name = Column(String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    recipient_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    attachments = db.relationship("MessageAttachmentModel", backref="message", cascade="all, delete-orphan", lazy=True)