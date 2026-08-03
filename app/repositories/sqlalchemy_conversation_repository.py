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
        """Converts an ORM instance to a domain Conversation entity."""
        return Conversation(
            id=db_conv.id,
            title=db_conv.title,
            created_at=db_conv.created_at
        )

    def save(self, conversation: Conversation) -> Conversation:
        """Saves a new conversation or updates an existing record."""
        db_conv = None
        if conversation.id:
            db_conv = ConversationModel.query.get(conversation.id)

        if not db_conv:
            db_conv = ConversationModel(
                title=conversation.title,
                created_at=conversation.created_at
            )
            if conversation.id:
                db_conv.id = conversation.id
            db.session.add(db_conv)
        else:
            db_conv.title = conversation.title
            db_conv.created_at = conversation.created_at

        db.session.commit()
        return self._to_domain(db_conv)

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieves a single conversation by ID."""
        db_conv = ConversationModel.query.get(conversation_id)
        return self._to_domain(db_conv) if db_conv else None

    def list_all(self) -> List[Conversation]:
        """Lists all conversations ordered by creation date descending."""
        db_convs = (
            ConversationModel.query
            .order_by(ConversationModel.created_at.desc())
            .all()
        )
        return [self._to_domain(c) for c in db_convs]
