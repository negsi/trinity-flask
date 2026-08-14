"""SQLAlchemy ORM model for Agent Datasources."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DatasourceModel(db.Model):
    """SQLAlchemy ORM model representing uploaded agent documents in `datasources`."""

    __tablename__ = "datasources"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)

    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    # Relationships
    agent = relationship("AgentModel", back_populates="datasources")

    def __repr__(self) -> str:
        return f"<DatasourceModel id='{self.id}' name='{self.name}' agent_id='{self.agent_id}'>"
