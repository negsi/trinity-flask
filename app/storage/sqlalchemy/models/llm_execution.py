"""
LLM Execution SQLAlchemy ORM Model.

Stores execution metadata, status, step plans, and results in JSON format.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from app.storage.sqlalchemy.db import db


class LLMExecutionModel(db.Model):
    """SQLAlchemy ORM entity for persisting ReAct task chain state to `llm_executions`."""

    __tablename__ = "llm_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), nullable=False, index=True)
    message_id = Column(String(36), nullable=True, index=True)
    
    response_type = Column(String(50), nullable=False)  # simple_message | task_chain
    summary_or_content = Column(Text, nullable=False)
    
    # Execution flag indicating if multi-turn loop has finished
    is_complete = Column(Boolean, nullable=False, default=True)
    
    # Stores complete step arrays including parameters and status updates as JSON
    steps = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<LLMExecutionModel {self.id} ({self.response_type})>"
