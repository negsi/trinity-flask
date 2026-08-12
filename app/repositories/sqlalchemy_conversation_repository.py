"""
SQLAlchemy Conversation Repository Implementation.

Handles database persistence and loading of Conversation entities.
"""

from typing import List, Optional
from app.storage.sqlalchemy.db import db
from app.domain.models.conversation import Conversation
from app.domain.repositories.conversation_repository import ConversationRepository
from app.storage.sqlalchemy.models.conversation import ConversationModel


class SQLAlchemyConversationRepository(ConversationRepository):
    """SQLAlchemy implementation for managing conversation storage."""

    def _to_domain(self, db_conv: ConversationModel) -> Conversation:
        return Conversation(
            id=db_conv.id,
            agent_id=db_conv.agent_id,
            title=db_conv.title,
            created_at=db_conv.created_at,
        )

    def save(self, conversation: Conversation) -> Conversation:
        db_conv = None
        if conversation.id:
            db_conv = db.session.get(ConversationModel, conversation.id)

        if not db_conv:
            db_conv = ConversationModel(
                title=conversation.title,
                agent_id=conversation.agent_id,
                created_at=conversation.created_at,
            )
            if conversation.id:
                db_conv.id = conversation.id
            db.session.add(db_conv)
        else:
            db_conv.title = conversation.title
            db_conv.agent_id = conversation.agent_id
            db_conv.created_at = conversation.created_at

        db.session.commit()
        return self._to_domain(db_conv)

    def get_by_agent_id(self, agent_id: str) -> List[Conversation]:
        """Lists all conversations for a specific agent ordered by creation date descending."""
        db_convs = (
            ConversationModel.query.filter(ConversationModel.agent_id == agent_id)
            .order_by(ConversationModel.created_at.desc())
            .all()
        )
        return [self._to_domain(c) for c in db_convs]

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieves a single conversation by ID."""
        db_conv = db.session.get(ConversationModel, conversation_id)
        return self._to_domain(db_conv) if db_conv else None

    def list_all(self) -> List[Conversation]:
        """Lists all conversations ordered by creation date descending."""
        db_convs = (
            ConversationModel.query.order_by(ConversationModel.created_at.desc()).all()
        )
        return [self._to_domain(c) for c in db_convs]
