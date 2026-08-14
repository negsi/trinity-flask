"""SQLAlchemy ORM model for Conversation sessions."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationModel(db.Model):
    """SQLAlchemy ORM entity representing conversation sessions in `conversations`."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)

    # Relationships
    agent = relationship("AgentModel", back_populates="conversations")
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )
    executions = relationship(
        "LLMExecutionModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<ConversationModel id='{self.id}' title='{self.title}'>"
