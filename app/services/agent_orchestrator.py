"""
Agent Orchestrator Service Module.

Coordinates AI agent response streaming, database message lifecycle,
and task chain persistence.
"""

import logging
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

        Args:
            user_text (str): Incoming user message content.
            conversation_id (str): Associated conversation identifier.
            agent_id (str): Agent entity ID.
            agent_name (str): Agent display name.
            user_id (str): Calling user ID.

        Yields:
            str: Token chunks emitted during prompt processing and tool runs.
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

        summary = None
        try:
            while True:
                chunk = next(loop_gen)
                yield chunk
        except StopIteration as e:
            summary = e.value

        if saved_message and summary and summary.final_text:
            try:
                self.messaging_service.update_message_text(
                    message_id=saved_message.id,
                    text=summary.final_text,
                )
            except Exception as e:
                logger.error("Error updating final message text: %s", e, exc_info=True)

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
