"""
Agent SQLAlchemy ORM Model.

Defines the database schema and relationships for agents.
"""

import uuid
from app.storage.sqlalchemy.db import db


class AgentModel(db.Model):
    """SQLAlchemy ORM entity representing the `agents` table."""

    __tablename__ = "agents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=False)

    # Memory Settings
    memory_enabled = db.Column(db.Boolean, default=False, nullable=False)
    memory_mode = db.Column(db.String(50), default="user_only", nullable=False)
    memory_limit_type = db.Column(db.String(50), default="all", nullable=False)
    memory_message_count = db.Column(db.Integer, nullable=True)

    # One-to-Many relationship with DatasourceModel (cascaded delete)
    datasources = db.relationship(
        "DatasourceModel",
        backref="agent",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<AgentModel {self.name} ({self.id})>"
