"""SQLAlchemy ORM models for Workflows, Nodes, and Edges."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.storage.sqlalchemy.db import db


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowModel(db.Model):
    """SQLAlchemy ORM entity representing the `workflows` table."""

    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(150), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    nodes = relationship(
        "WorkflowNodeModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    edges = relationship(
        "WorkflowEdgeModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkflowModel id='{self.id}' name='{self.name}'>"


class WorkflowNodeModel(db.Model):
    """SQLAlchemy ORM entity representing the `workflow_nodes` table."""

    __tablename__ = "workflow_nodes"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(150), nullable=False)
    agent_description = Column(String(500), nullable=True)
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    prompt = Column(Text, nullable=False, default="")

    workflow = relationship("WorkflowModel", back_populates="nodes")

    def __repr__(self) -> str:
        return f"<WorkflowNodeModel id='{self.id}' agent_name='{self.agent_name}'>"


class WorkflowEdgeModel(db.Model):
    """SQLAlchemy ORM entity representing the `workflow_edges` table."""

    __tablename__ = "workflow_edges"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id = Column(String(36), nullable=False)
    target_node_id = Column(String(36), nullable=False)

    workflow = relationship("WorkflowModel", back_populates="edges")

    def __repr__(self) -> str:
        return (
            f"<WorkflowEdgeModel id='{self.id}' "
            f"source='{self.source_node_id}' target='{self.target_node_id}'>"
        )