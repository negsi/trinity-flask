"""
Agent Orchestrator Service.

Central orchestration logic for AI agent interactions, multi-turn ReAct loops,
streaming responses, and persistent state management.
"""

import logging
from dataclasses import dataclass, field
from typing import Generator

from app.domain.enums import ActorType
from app.domain.models.message import Message
from app.domain.models.message_attachment import MessageAttachment
from app.domain.models.llm_execution import LLMExecution
from app.repositories.sqlalchemy_llm_execution_repository import (
    SQLAlchemyLLMExecutionRepository,
)
from app.services.llm_service import LLMService
from app.services.messaging_service import MessagingService
from app.services.agent_context_builder import AgentContextBuilder
from app.services.llm.stream_parser import StreamResponseParser
from app.services.task_executer import TaskExecutor
from app.services.tools import SYSTEM_TOOLS

logger = logging.getLogger(__name__)


@dataclass
class ReActTurnState:
    """Mutable state container managing multi-turn ReAct loop execution."""

    user_prompt: str
    accumulated_all_text: list[str] = field(default_factory=list)
    last_chain_chunks: list[str] = field(default_factory=list)
    saved_message: Message | None = None
    is_complete: bool = False
    turn_count: int = 0
    max_turns: int = 5


class AgentOrchestrator:
    """Orchestrates streaming LLM communication, ReAct tasks, and data persistence."""

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: AgentContextBuilder,
        messaging_service: MessagingService,
        llm_execution_repo: SQLAlchemyLLMExecutionRepository,
    ) -> None:
        self.llm_service = llm_service
        self.context_builder = context_builder
        self.messaging_service = messaging_service
        self.llm_execution_repo = llm_execution_repo

    def stream_agent_response(
        self,
        user_text: str,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        user_id: str,
    ) -> Generator[str, None, None]:
        """Streams text chunks live while running multi-turn ReAct task chains."""
        fetched_attachments = self.messaging_service.get_latest_user_attachments(
            conversation_id
        )
        state = ReActTurnState(user_prompt=user_text)

        while not state.is_complete and state.turn_count < state.max_turns:
            state.turn_count += 1
            logger.info(
                "[AgentOrchestrator] Starting ReAct Turn %s/%s...",
                state.turn_count,
                state.max_turns,
            )

            # Step 1: Run standard stream turn
            extracted_json = yield from self._run_stream_turn(
                state=state,
                agent_id=agent_id,
                attachments=fetched_attachments,
            )

            # Ensure agent message record exists in database
            state.saved_message = self._ensure_message_created(
                existing_message=state.saved_message,
                conversation_id=conversation_id,
                sender_id=agent_id,
                sender_name=agent_name,
                recipient_id=user_id,
                text="".join(state.accumulated_all_text).strip(),
            )

            if not extracted_json:
                state.is_complete = True
                break

            # Step 2: Parse and execute tool chain if present
            execution = LLMExecution.from_json_payload(
                payload=extracted_json,
                conversation_id=conversation_id,
                message_id=state.saved_message.id if state.saved_message else None,
            )

            if not execution:
                state.is_complete = True
                break

            self._save_execution_safe(execution)

            last_result = yield from self._execute_task_chain(
                execution=execution,
                conversation_id=conversation_id,
                agent_id=agent_id,
                attachments=fetched_attachments,
                state=state,
            )

            if state.is_complete:
                break

            # Step 3: Construct follow-up turn prompt
            state.user_prompt = (
                f"Original User Query: {user_text}\n\n"
                f"Result from previous task step execution:\n{last_result}\n\n"
                f"Please formulate the next sub-plan step or final response using these actual result data."
            )

        self._finalize_message_update(state)

    def _run_stream_turn(
        self,
        state: ReActTurnState,
        agent_id: str,
        attachments: list[MessageAttachment],
    ) -> Generator[str, None, dict | None]:
        """Streams a single turn from the LLM and extracts embedded JSON task payloads."""
        llm_messages = self.context_builder.build_llm_messages(
            user_text=state.user_prompt,
            agent_id=agent_id,
            attachments=attachments,
        )

        parser = StreamResponseParser()
        extracted_json = None

        for chunk in self.llm_service.stream(llm_messages):
            if not chunk:
                continue
            display_text, json_data = parser.process_chunk(chunk)
            if display_text:
                state.accumulated_all_text.append(display_text)
                yield display_text
            if json_data:
                extracted_json = json_data

        remaining_text, _ = parser.finalize()
        if remaining_text:
            state.accumulated_all_text.append(remaining_text)
            yield remaining_text

        return extracted_json

    def _execute_task_chain(
        self,
        execution: LLMExecution,
        conversation_id: str,
        agent_id: str,
        attachments: list[MessageAttachment],
        state: ReActTurnState,
    ) -> Generator[str, None, str]:
        """Executes a structured task chain and streams sub-step responses."""

        def llm_stream_adapter(prompt_text: str) -> Generator[str, None, None]:
            system_instruction = (
                "System Notice: You are executing a sub-step execution task. "
                "Do NOT wrap your response in JSON (###START_JSON_RESPONSE###). "
                "Do NOT output a task chain plan. "
                "Provide strictly and directly the raw requested text/code response.\n\n"
            )
            messages = self.context_builder.build_llm_messages(
                user_text=system_instruction + prompt_text,
                agent_id=agent_id,
                attachments=attachments,
            )
            yield from self.llm_service.stream(messages)

        executor = TaskExecutor(tools=SYSTEM_TOOLS, llm_stream_func=llm_stream_adapter)
        initial_context = {"conversation_id": conversation_id}
        chain_parser = StreamResponseParser()
        chain_text_chunks = []
        last_result = ""

        chain_gen = executor.execute_chain_stream(
            execution, initial_context=initial_context
        )

        try:
            while True:
                raw_chunk = next(chain_gen)
                if raw_chunk:
                    display_text, _ = chain_parser.process_chunk(raw_chunk)
                    if display_text:
                        chain_text_chunks.append(display_text)
                        state.accumulated_all_text.append(display_text)
                        yield display_text
        except StopIteration as e:
            exec_result = e.value
            if exec_result:
                state.is_complete = exec_result.is_complete
                last_result = exec_result.last_result

        rem_chain_text, _ = chain_parser.finalize()
        if rem_chain_text:
            chain_text_chunks.append(rem_chain_text)
            state.accumulated_all_text.append(rem_chain_text)
            yield rem_chain_text

        if chain_text_chunks:
            state.last_chain_chunks = chain_text_chunks

        return last_result

    def _ensure_message_created(
        self,
        existing_message: Message | None,
        conversation_id: str,
        sender_id: str,
        sender_name: str,
        recipient_id: str,
        text: str,
    ) -> Message | None:
        """Saves initial database record for the agent's streaming response."""
        if existing_message or not conversation_id:
            return existing_message
        try:
            return self.messaging_service.send_message(
                conversation_id=conversation_id,
                sender_id=sender_id,
                sender_type=ActorType.AGENT,
                sender_name=sender_name,
                text=text,
                recipient_id=recipient_id,
            )
        except Exception as e:
            logger.error("Error creating agent message record: %s", e, exc_info=True)
            return None

    def _save_execution_safe(self, execution: LLMExecution) -> None:
        """Safely persists execution chain metadata."""
        try:
            self.llm_execution_repo.save(execution)
        except Exception as e:
            logger.error("Error persisting LLMExecution state: %s", e, exc_info=True)

    def _finalize_message_update(self, state: ReActTurnState) -> None:
        """Performs final update on agent message content in database."""
        final_text = (
            "".join(state.last_chain_chunks).strip()
            if state.last_chain_chunks
            else "".join(state.accumulated_all_text).strip()
        )

        if state.saved_message and final_text:
            try:
                self.messaging_service.update_message_text(
                    message_id=state.saved_message.id, text=final_text
                )
            except Exception as e:
                logger.error("Error updating final message text: %s", e, exc_info=True)

    def handle_incoming_message(self, message: Message) -> None:
        """Subscribed event callback for incoming messages."""
        if message.sender_type == ActorType.AGENT or not message.recipient_id:
            return
