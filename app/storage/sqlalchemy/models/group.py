"""SQLAlchemy ORM model for Group entity and agent_groups association table."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship

from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Join Table for Many-to-Many Relationship
agent_groups = Table(
    "agent_groups",
    db.Model.metadata,
    Column("agent_id", String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", String(36), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


class GroupModel(db.Model):
    """SQLAlchemy ORM entity representing the `groups` table."""

    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=True)

    agents = relationship(
        "AgentModel",
        secondary=agent_groups,
        back_populates="groups",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<GroupModel id='{self.id}' name='{self.name}'>"