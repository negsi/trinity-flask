"""
Conversation SQLAlchemy ORM Model.

Defines database schema for chat conversations.
"""

from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.storage.sqlalchemy.db import db


class ConversationModel(db.Model):
    """SQLAlchemy ORM entity representing the `conversations` table."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
