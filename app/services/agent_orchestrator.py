"""
Agent Orchestrator Service Module.

Coordinates AI agent response streaming, database message lifecycle,
and task chain persistence.
"""

import os, logging, json
from typing import Generator, Optional

from app.domain.enums import ActorType
from app.domain.models.llm_execution import LLMExecution
from app.domain.models.message import Message
from app.domain.repositories.llm_execution_repository import LLMExecutionRepository
from app.services.messaging_service import MessagingService
from app.services.react_loop_runner import ReActLoopRunner

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates streaming agent responses, database persistence, and ReAct loop execution."""

    def __init__(
        self,
        messaging_service: MessagingService,
        llm_execution_repo: LLMExecutionRepository,
        react_loop_runner: ReActLoopRunner,
    ) -> None:
        self.messaging_service = messaging_service
        self.llm_execution_repo = llm_execution_repo
        self.react_loop_runner = react_loop_runner

    def stream_agent_response(
        self,
        user_text: str,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        user_id: str,
    ) -> Generator[str, None, None]:
        """
        Streams response tokens to the client while orchestrating ReAct loop cycles and persistence.
        """
        fetched_attachments = self.messaging_service.get_latest_user_attachments(conversation_id)
        conversation_history = self.messaging_service.get_conversation_history(
            conversation_id=conversation_id, limit=100
        )

        saved_message: Optional[Message] = None

        def on_turn_completed(accumulated_text: str, execution: Optional[LLMExecution]) -> None:
            nonlocal saved_message
            if not saved_message and conversation_id:
                try:
                    saved_message = self.messaging_service.send_message(
                        conversation_id=conversation_id,
                        sender_id=agent_id,
                        sender_type=ActorType.AGENT,
                        sender_name=agent_name,
                        text=accumulated_text,
                        recipient_id=user_id,
                    )
                except Exception as e:
                    logger.error("Error creating initial agent message: %s", e, exc_info=True)

            if execution:
                if saved_message:
                    execution.message_id = saved_message.id
                self._save_execution_safe(execution)

        loop_gen = self.react_loop_runner.run_react_loop(
            user_text=user_text,
            conversation_id=conversation_id,
            agent_id=agent_id,
            attachments=fetched_attachments,
            conversation_history=conversation_history,
            on_turn_completed=on_turn_completed,
        )

        summary = yield from loop_gen

        if summary:
            final_text = summary.final_text or summary.accumulated_text or ""
            created_files = getattr(summary, "created_files", None) or []

            image_snippets = []
            formatted_files = []

            for f in created_files:
                if isinstance(f, dict):
                    fpath = f.get("file_path") or f.get("filename") or ""
                    fname = os.path.basename(fpath)
                    if fname:
                        file_url = f"/api/v1/chat/conversations/{conversation_id}/files/{fname}"
                        formatted_files.append({
                            "id": fpath,
                            "name": fname,
                            "filename": fname,
                            "url": file_url,
                        })
                        if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                            if fname not in final_text and file_url not in final_text:
                                image_snippets.append(f"![Generiertes Bild]({file_url})")

            if image_snippets:
                img_block = "\n\n" + "\n\n".join(image_snippets)
                if not final_text or final_text.strip() == "Aufgabe ausgeführt.":
                    final_text = "\n\n".join(image_snippets)
                    yield final_text
                else:
                    final_text += img_block
                    yield img_block
            elif not final_text:
                final_text = "Aufgabe ausgeführt."
                yield final_text

            if not saved_message and conversation_id:
                try:
                    saved_message = self.messaging_service.send_message(
                        conversation_id=conversation_id,
                        sender_id=agent_id,
                        sender_type=ActorType.AGENT,
                        sender_name=agent_name,
                        text=final_text,
                        recipient_id=user_id,
                    )
                except Exception as e:
                    logger.error("Error creating fallback agent message: %s", e, exc_info=True)
            elif saved_message and final_text:
                try:
                    self.messaging_service.update_message_text(
                        message_id=saved_message.id,
                        text=final_text,
                    )
                except Exception as e:
                    logger.error("Error updating final message text: %s", e, exc_info=True)

            if saved_message and formatted_files:
                try:
                    self.messaging_service.add_attachments_to_message(
                        message_id=saved_message.id,
                        file_info_list=created_files,
                    )

                    attachments_payload = {
                        "type": "attachments",
                        "files": formatted_files
                    }
                    yield f"\n__ATTACHMENTS__:{json.dumps(attachments_payload)}"
                except Exception as e:
                    logger.error("Error adding generated attachments to message: %s", e, exc_info=True)

    def _save_execution_safe(self, execution: LLMExecution) -> None:
        """Safely persists LLM execution metadata to the repository."""
        try:
            self.llm_execution_repo.save(execution)
        except Exception as e:
            logger.error("Error persisting LLMExecution metadata: %s", e, exc_info=True)

    def handle_incoming_message(self, message: Message) -> None:
        """Callback handler subscribed to incoming message events."""
        if message.sender_type == ActorType.AGENT or not message.recipient_id:
            return
