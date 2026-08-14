"""SQLAlchemy Conversation Repository Implementation Module.

Handles persistence, retrieval, and deletion of Conversation domain entities.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import StorageError
from app.domain.models.conversation import Conversation
from app.domain.repositories.conversation_repository import ConversationRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import ConversationModel

logger = logging.getLogger(__name__)


class SQLAlchemyConversationRepository(ConversationRepository):
    """SQLAlchemy-backed implementation of the ConversationRepository interface."""

    def _to_domain(self, model: ConversationModel) -> Conversation:
        """Maps an ORM ConversationModel to a domain Conversation entity.

        Args:
            model (ConversationModel): ORM entity.

        Returns:
            Conversation: Clean domain model.
        """
        return Conversation(
            id=model.id,
            agent_id=model.agent_id,
            title=model.title,
            created_at=model.created_at,
        )

    def save(self, conversation: Conversation) -> Conversation:
        """Persists or updates a Conversation entity in the database.

        Args:
            conversation (Conversation): The conversation entity to persist.

        Returns:
            Conversation: The saved domain entity.

        Raises:
            StorageError: If persistence encounters a database error.
        """
        try:
            model: ConversationModel | None = None
            if conversation.id:
                model = db.session.get(ConversationModel, conversation.id)

            if not model:
                model = ConversationModel(
                    id=conversation.id,
                    title=conversation.title,
                    agent_id=conversation.agent_id,
                    created_at=conversation.created_at,
                )
                db.session.add(model)
            else:
                model.title = conversation.title
                model.agent_id = conversation.agent_id

            db.session.commit()
            return self._to_domain(model)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Conversation '%s': %s", conversation.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Conversation '{conversation.id}': {exc}") from exc

    def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Retrieves a single conversation by its unique ID.

        Args:
            conversation_id (str): Unique UUID.

        Returns:
            Conversation | None: Domain entity if found, else None.

        Raises:
            StorageError: If the database query fails.
        """
        try:
            model = db.session.get(ConversationModel, conversation_id)
            return self._to_domain(model) if model else None
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Conversation '{conversation_id}': {exc}") from exc

    def get_by_agent_id(self, agent_id: str) -> list[Conversation]:
        """Lists all conversations assigned to a specific agent ordered by creation date descending.

        Args:
            agent_id (str): Agent UUID.

        Returns:
            list[Conversation]: Chronologically ordered conversation entities.

        Raises:
            StorageError: If the query fails.
        """
        try:
            models = (
                ConversationModel.query.filter(ConversationModel.agent_id == agent_id)
                .order_by(ConversationModel.created_at.desc())
                .all()
            )
            return [self._to_domain(c) for c in models]
        except SQLAlchemyError as exc:
            logger.error("Error retrieving conversations for Agent '%s': %s", agent_id, exc, exc_info=True)
            raise StorageError(f"Database error fetching conversations for Agent '{agent_id}': {exc}") from exc

    def list_all(self) -> list[Conversation]:
        """Lists all conversations ordered by creation date descending.

        Returns:
            list[Conversation]: List of all conversations.

        Raises:
            StorageError: If the query fails.
        """
        try:
            models = ConversationModel.query.order_by(ConversationModel.created_at.desc()).all()
            return [self._to_domain(c) for c in models]
        except SQLAlchemyError as exc:
            logger.error("Error listing all conversations: %s", exc, exc_info=True)
            raise StorageError(f"Database error listing conversations: {exc}") from exc

    def delete(self, conversation_id: str) -> bool:
        """Deletes a conversation entity and all cascaded children by ID.

        Args:
            conversation_id (str): Unique conversation UUID.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        try:
            model = db.session.get(ConversationModel, conversation_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Conversation '{conversation_id}': {exc}") from exc
