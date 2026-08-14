"""SQLAlchemy ORM model for LLM task executions."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.domain.enums import ResponseType
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LLMExecutionModel(db.Model):
    """SQLAlchemy ORM entity for persisting ReAct task execution states in `llm_executions`."""

    __tablename__ = "llm_executions"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    response_type = Column(SQLEnum(ResponseType), nullable=False)
    summary_or_content = Column(Text, nullable=False)
    is_complete = Column(Boolean, nullable=False, default=True)
    steps = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="executions")

    def __repr__(self) -> str:
        return f"<LLMExecutionModel id='{self.id}' response_type='{self.response_type}'>"
