"""
Datasource SQLAlchemy ORM Model.

Defines the table structure for uploaded agent documents and knowledge sources.
"""

import uuid
from app.storage.sqlalchemy.db import db


class DatasourceModel(db.Model):
    """SQLAlchemy ORM model representing the `datasources` database table."""

    __tablename__ = "datasources"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)

    # Foreign key link back to the owning agent
    agent_id = db.Column(
        db.String(36), 
        db.ForeignKey("agents.id", ondelete="CASCADE"), 
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<DatasourceModel {self.name} (Agent: {self.agent_id})>"
