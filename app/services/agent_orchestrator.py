"""
Agent Orchestrator Service.

This module provides the central orchestration logic for AI agent interactions.
It handles streaming token-by-token responses to the frontend, parsing embedded JSON tool
execution plans, executing multi-turn ReAct (Reason + Act) loops via TaskExecutor, and managing
persistent updates for messages and execution logs in the database.
"""

import logging
from typing import Generator, Optional
from dataclasses import dataclass, field

from app.domain.models.message import Message, ActorType
from app.repositories.sqlalchemy_llm_execution_repository import SQLAlchemyLLMExecutionRepository
from app.services.llm_service import LLMService
from app.services.messaging_service import MessagingService
from app.services.agent_context_builder import AgentContextBuilder
from app.services.llm.stream_parser import StreamResponseParser
from app.domain.models.llm_execution import LLMExecution
from app.services.task_executer import TaskExecutor
from app.services.tools import SYSTEM_TOOLS

# Initialize logger for tracking orchestrator operations
logger = logging.getLogger(__name__)


@dataclass
class ReActTurnState:
    """
    Mutable state container managing multi-turn ReAct loop execution.

    Attributes:
        user_prompt (str): Active prompt input for the current turn iteration.
        accumulated_all_text (list[str]): Complete text history accumulated across all turns.
        last_chain_chunks (list[str]): Text chunks emitted specifically during the last tool execution.
        saved_message (Optional[Message]): Reference to the persisted agent database Message entity.
        is_complete (bool): Flag indicating if the ReAct goal has been fully satisfied.
        turn_count (int): Counter tracking the current ReAct iteration step.
        max_turns (int): Safety threshold defining maximum permitted ReAct turns (prevents infinite loops).
    """
    user_prompt: str
    accumulated_all_text: list[str] = field(default_factory=list)
    last_chain_chunks: list[str] = field(default_factory=list)
    saved_message: Optional[Message] = None
    is_complete: bool = False
    turn_count: int = 0
    max_turns: int = 5


class AgentOrchestrator:
    """
    Orchestrates real-time streaming LLM communication, ReAct loop execution, and data persistence.
    """

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: AgentContextBuilder,
        messaging_service: MessagingService,
        llm_execution_repo: SQLAlchemyLLMExecutionRepository,
    ):
        """
        Initializes the AgentOrchestrator with required domain services and repositories.

        Args:
            llm_service (LLMService): Service routing prompts to LLM provider backends.
            context_builder (AgentContextBuilder): Service constructing system instructions & knowledge context.
            messaging_service (MessagingService): Service handling chat message creation and updates.
            llm_execution_repo (SQLAlchemyLLMExecutionRepository): Repository persisting task chain state.
        """
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
        """
        Streams parsed text response chunks live to the client while executing multi-turn ReAct task chains.

        Workflow:
          1. Constructs the system prompt and context for the target agent.
          2. Streams LLM tokens while stripping embedded JSON response markers.
          3. Creates an initial agent Message record in the database.
          4. If a task chain JSON block is detected, executes tool steps via TaskExecutor.
          5. If the task chain is incomplete, loops back for follow-up LLM reasoning turns.
          6. Updates the database message with final accumulated text output once completed.

        Args:
            user_text (str): Initial input prompt submitted by the user.
            conversation_id (str): Identifier of the active conversation context.
            agent_id (str): Identifier of the responding AI agent.
            agent_name (str): Display name of the responding agent.
            user_id (str): Identifier of the user initiating the request.

        Yields:
            Generator[str, None, None]: Live text token strings formatted for response streaming.
        """
        # Initialize mutable state tracking across ReAct turns
        state = ReActTurnState(user_prompt=user_text)

        # Helper adapter allowing TaskExecutor to stream nested LLM calls if requested by tools
        def llm_stream_adapter(prompt_text: str) -> Generator[str, None, None]:
            messages = self.context_builder.build_llm_messages(
                user_text=prompt_text, agent_id=agent_id
            )
            yield from self.llm_service.stream(messages)

        # === ReAct Multi-Turn Loop ===
        while not state.is_complete and state.turn_count < state.max_turns:
            state.turn_count += 1
            logger.info(f"[AgentOrchestrator] Starting ReAct Turn {state.turn_count}/{state.max_turns}...")

            # Build full system instructions and prompt context
            llm_messages = self.context_builder.build_llm_messages(
                user_text=state.user_prompt, agent_id=agent_id
            )

            parser = StreamResponseParser()
            accumulated_turn_text = []
            extracted_json_payload = None

            # --- Step 1: Process and stream raw LLM token chunks ---
            for chunk in self.llm_service.stream(llm_messages):
                if not chunk:
                    continue
                # Process chunk through stream parser to separate plain text from JSON payloads
                display_text, json_data = parser.process_chunk(chunk)
                if display_text:
                    accumulated_turn_text.append(display_text)
                    state.accumulated_all_text.append(display_text)
                    yield display_text
                if json_data:
                    extracted_json_payload = json_data

            # --- Step 2: Flush remaining buffer from stream parser ---
            remaining_text, _ = parser.finalize()
            if remaining_text:
                accumulated_turn_text.append(remaining_text)
                state.accumulated_all_text.append(remaining_text)
                yield remaining_text

            # Create initial database message entry for the agent if not already created
            state.saved_message = self._ensure_message_created(
                state.saved_message,
                conversation_id,
                agent_id,
                agent_name,
                user_id,
                "".join(state.accumulated_all_text).strip(),
            )

            # --- Step 3: Check if task chain JSON was received ---
            if not extracted_json_payload:
                # Standard conversational text response without tools -> complete ReAct loop
                state.is_complete = True
                break

            # --- Step 4: Execute Task Chain ---
            execution = LLMExecution.from_json_payload(
                payload=extracted_json_payload,
                conversation_id=conversation_id,
                message_id=state.saved_message.id if state.saved_message else None,
            )

            if not execution:
                state.is_complete = True
                break

            # Persist initial execution plan step models to SQL storage
            self._save_execution_safe(execution)

            executor = TaskExecutor(
                tools=SYSTEM_TOOLS, llm_stream_func=llm_stream_adapter
            )
            chain_parser = StreamResponseParser()
            chain_text_chunks = []

            # Execute tool steps and stream output back live
            chain_gen = executor.execute_chain_stream(execution)

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
                # Capture return value from generator (ChainExecutionResult)
                exec_result = e.value
                state.is_complete = exec_result.is_complete if exec_result else True
                last_result = exec_result.last_result if exec_result else ""

            # Flush tool chain stream parser buffer
            rem_chain_text, _ = chain_parser.finalize()
            if rem_chain_text:
                chain_text_chunks.append(rem_chain_text)
                state.accumulated_all_text.append(rem_chain_text)
                yield rem_chain_text

            if chain_text_chunks:
                state.last_chain_chunks = chain_text_chunks

            # Exit loop if plan execution reports completion
            if state.is_complete:
                break

            # --- Step 5: Prepare follow-up prompt for next ReAct turn ---
            state.user_prompt = (
                f"Original User Query: {user_text}\n\n"
                f"Result from previous task step execution:\n{last_result}\n\n"
                f"Please formulate the next sub-plan step or final response using these actual result data."
            )

        # === Finalize Database Message Content ===
        self._finalize_message_update(state)

    def _ensure_message_created(
        self,
        existing_message: Optional[Message],
        conversation_id: str,
        sender_id: str,
        sender_name: str,
        recipient_id: str,
        text: str,
    ) -> Optional[Message]:
        """
        Ensures an agent Message record exists in the database.
        Creates a new Message entity on the first turn if one does not exist yet.
        """
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
            logger.error(f"Error creating agent message record: {e}", exc_info=True)
            return None

    def _save_execution_safe(self, execution: LLMExecution) -> None:
        """Safely persists LLMExecution records while intercepting database exceptions."""
        try:
            self.llm_execution_repo.save(execution)
        except Exception as e:
            logger.error(f"Error persisting LLMExecution state: {e}", exc_info=True)

    def _finalize_message_update(self, state: ReActTurnState) -> None:
        """Updates the stored database message entry with the final accumulated text output."""
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
                logger.error(f"Error performing final message update: {e}", exc_info=True)

    def handle_incoming_message(self, message: Message) -> None:
        """
        Observer event listener for incoming messaging events.
        Filters out self-emitted agent messages or messages without valid recipients.
        """
        if message.sender_type == ActorType.AGENT or not message.recipient_id:
            return
