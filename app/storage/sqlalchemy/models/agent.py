"""SQLAlchemy ORM model for Agent entities."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.enums import MemoryLimitType, MemoryMode
from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentModel(db.Model):
    """SQLAlchemy ORM entity representing the `agents` table."""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)

    # Memory settings
    memory_enabled = Column(Boolean, default=False, nullable=False)
    memory_mode = Column(
        SQLEnum(MemoryMode),
        default=MemoryMode.USER_ONLY,
        nullable=False,
    )
    memory_limit_type = Column(
        SQLEnum(MemoryLimitType),
        default=MemoryLimitType.ALL,
        nullable=False,
    )
    memory_message_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=True)

    # Relationships
    datasources = relationship(
        "DatasourceModel",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    conversations = relationship(
        "ConversationModel",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<AgentModel id='{self.id}' name='{self.name}'>"
