"""SQLAlchemy Message Repository Implementation Module.

Handles persistence, query operations, dynamic pagination, attachment synchronization,
and timeline composition for Message domain models.
"""

import logging
from typing import Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.domain.enums import ActorType
from app.domain.errors import StorageError
from app.domain.models.message import Message, MessageAttachment, MessageThought
from app.domain.repositories.message_repository import MessageRepository
from app.storage.sqlalchemy.db import db
from app.storage.sqlalchemy.models import (
    MessageAttachmentModel,
    MessageModel,
    MessageThoughtModel,
)
from app.storage.sqlalchemy.models.llm_execution import LLMExecutionModel

logger = logging.getLogger(__name__)


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy-backed implementation of the MessageRepository interface."""

    def _build_timeline(
        self,
        thoughts: list[MessageThoughtModel],
        executions: list[LLMExecutionModel],
    ) -> list[dict[str, Any]]:
        """Merges thoughts and executions into a unified timeline sorted by sequence_index."""
        items: list[dict[str, Any]] = []

        # 1. Thought-Blöcke inkl. sequence_index verarbeiten
        for t in thoughts:
            items.append({
                "sequence_index": t.sequence_index,
                "data": {
                    "type": "thought",
                    "content": t.content,
                },
            })

        # 2. Executions (Task Chains) inkl. sequence_index verarbeiten
        for ex in executions:
            steps_payload = []
            if ex.steps:
                sorted_steps = sorted(ex.steps, key=lambda s: s.step_number)
                for step in sorted_steps:
                    status_str = step.status.value if hasattr(step.status, "value") else str(step.status)
                    steps_payload.append({
                        "step_number": step.step_number,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "parameters": step.parameters or {},
                        "result": step.result,
                        "status": status_str.lower(),
                    })

            items.append({
                "sequence_index": getattr(ex, "sequence_index", 0),
                "data": {
                    "type": "phase",
                    "phase": {
                        "phaseIndex": 1,
                        "steps": steps_payload,
                    },
                },
            })

        # 3. Strikt nach sequence_index sortieren
        items.sort(key=lambda x: x["sequence_index"])

        # 4. Nur das Payload-Array für das Frontend zurückgeben
        return [item["data"] for item in items]

    def _to_domain(
        self,
        model: MessageModel,
        executions: list[LLMExecutionModel] | None = None,
    ) -> Message:
        """Maps an ORM MessageModel instance to a Message domain entity."""
        executions = executions or []

        attachments = [
            MessageAttachment(
                id=att.id,
                name=att.name,
                filename=att.filename,
                file_path=att.file_path,
                mime_type=att.mime_type,
                file_size=att.file_size,
                message_id=att.message_id,
                created_at=att.created_at,
            )
            for att in (model.attachments or [])
        ]

        thoughts = [
            MessageThought(
                id=t.id,
                content=t.content,
                sequence_index=t.sequence_index,
                message_id=t.message_id,
                created_at=t.created_at,
            )
            for t in (model.thoughts or [])
        ]

        # Nur noch die merged Timeline aufbauen
        timeline = self._build_timeline(model.thoughts or [], executions)

        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            sender_id=model.sender_id,
            sender_type=model.sender_type,
            sender_name=model.sender_name,
            text=model.text,
            recipient_id=model.recipient_id,
            attachments=attachments,
            thoughts=thoughts,
            timeline=timeline,
            timestamp=model.timestamp,
        )

    def save(self, message: Message) -> Message:
        """Persists or updates a message along with its thoughts and attachments in the database."""
        try:
            model: MessageModel | None = None
            if message.id:
                model = db.session.get(MessageModel, message.id)

            if not model:
                model = MessageModel(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    sender_id=message.sender_id,
                    sender_type=message.sender_type,
                    sender_name=message.sender_name,
                    text=message.text,
                    recipient_id=message.recipient_id,
                    timestamp=message.timestamp,
                )
                db.session.add(model)
            else:
                model.conversation_id = message.conversation_id
                model.sender_id = message.sender_id
                model.sender_type = message.sender_type
                model.sender_name = message.sender_name
                model.text = message.text
                model.recipient_id = message.recipient_id
                model.timestamp = message.timestamp

            # Synchronisiere thoughts (1:n Beziehung)
            synced_thoughts: list[MessageThoughtModel] = []
            for t in message.thoughts:
                thought_model = db.session.get(MessageThoughtModel, t.id)
                if thought_model:
                    thought_model.content = t.content
                    thought_model.sequence_index = t.sequence_index
                    thought_model.message_id = model.id
                else:
                    thought_model = MessageThoughtModel(
                        id=t.id,
                        content=t.content,
                        sequence_index=t.sequence_index,
                        message_id=model.id,
                        created_at=t.created_at,
                    )
                synced_thoughts.append(thought_model)
            model.thoughts = synced_thoughts

            # Synchronisiere attachments (1:n Beziehung)
            synced_attachments: list[MessageAttachmentModel] = []
            for att in message.attachments:
                att_model = db.session.get(MessageAttachmentModel, att.id)
                if att_model:
                    att_model.name = att.name
                    att_model.filename = att.filename
                    att_model.file_path = att.file_path
                    att_model.mime_type = att.mime_type
                    att_model.file_size = att.file_size
                    att_model.message_id = model.id
                else:
                    att_model = MessageAttachmentModel(
                        id=att.id,
                        name=att.name,
                        filename=att.filename,
                        file_path=att.file_path,
                        mime_type=att.mime_type,
                        file_size=att.file_size,
                        message_id=model.id,
                        created_at=att.created_at,
                    )
                synced_attachments.append(att_model)
            model.attachments = synced_attachments

            db.session.commit()

            # Executions zur Message holen für sauberen Domain-Build
            executions = (
                LLMExecutionModel.query.options(joinedload(LLMExecutionModel.steps))
                .filter(LLMExecutionModel.message_id == model.id)
                .all()
            )
            return self._to_domain(model, executions)

        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to save Message '%s': %s", message.id, exc, exc_info=True)
            raise StorageError(f"Database error while saving Message '{message.id}': {exc}") from exc

    def get_by_id(self, message_id: str) -> Message | None:
        try:
            model = db.session.get(MessageModel, message_id)
            if not model:
                return None

            executions = (
                LLMExecutionModel.query.options(joinedload(LLMExecutionModel.steps))
                .filter(LLMExecutionModel.message_id == message_id)
                .all()
            )
            return self._to_domain(model, executions)
        except SQLAlchemyError as exc:
            logger.error("Error retrieving Message '%s': %s", message_id, exc, exc_info=True)
            raise StorageError(f"Database error retrieving Message '{message_id}': {exc}") from exc

    def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        try:
            total = self.count_by_conversation(conversation_id)
            calculated_offset = offset if offset > 0 else max(0, total - limit)

            models = (
                MessageModel.query.filter(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.timestamp.asc())
                .offset(calculated_offset)
                .limit(limit)
                .all()
            )

            if not models:
                return []

            # Alle Executions der Conversation auf einmal laden
            executions = (
                LLMExecutionModel.query.options(joinedload(LLMExecutionModel.steps))
                .filter(LLMExecutionModel.conversation_id == conversation_id)
                .all()
            )

            # Executions pro message_id gruppieren
            execution_map: dict[str, list[LLMExecutionModel]] = {}
            unmapped_executions: list[LLMExecutionModel] = []

            for ex in executions:
                if ex.message_id:
                    execution_map.setdefault(ex.message_id, []).append(ex)
                else:
                    unmapped_executions.append(ex)

            # Fallback für Unmapped Executions (z.B. alten Agent-Nachrichten zuweisen)
            if unmapped_executions:
                agent_models = [
                    m for m in models 
                    if getattr(m.sender_type, "value", str(m.sender_type)).lower() == "agent"
                ]
                for i, ex in enumerate(unmapped_executions):
                    if i < len(agent_models):
                        execution_map.setdefault(agent_models[i].id, []).append(ex)

            return [self._to_domain(m, execution_map.get(m.id, [])) for m in models]

        except SQLAlchemyError as exc:
            logger.error(
                "Error retrieving messages for Conversation '%s': %s",
                conversation_id,
                exc,
                exc_info=True,
            )
            raise StorageError(
                f"Database error fetching messages for Conversation '{conversation_id}': {exc}"
            ) from exc

    def count_by_conversation(self, conversation_id: str) -> int:
        try:
            return MessageModel.query.filter(
                MessageModel.conversation_id == conversation_id
            ).count()
        except SQLAlchemyError as exc:
            logger.error("Error counting messages for Conversation '%s': %s", conversation_id, exc, exc_info=True)
            raise StorageError(f"Database error counting messages for Conversation '{conversation_id}': {exc}") from exc

    def delete(self, message_id: str) -> bool:
        try:
            model = db.session.get(MessageModel, message_id)
            if not model:
                return False

            db.session.delete(model)
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error deleting Message '%s': %s", message_id, exc, exc_info=True)
            raise StorageError(f"Database error deleting Message '{message_id}': {exc}") from exc