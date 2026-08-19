"""
ReAct Loop Runner Module.

Encapsulates multi-turn reasoning and tool execution loops, managing turn iterations,
sub-step stream parsing, and conversational follow-up prompt compilation.
"""

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
import logging
from typing import Any

from app.domain.models.llm_execution import LLMExecution
from app.domain.models.message import MessageAttachment
from app.services.agent_context_builder import AgentContextBuilder
from app.services.llm.stream_parser import StreamResponseParser
from app.services.llm_service import LLMService
from app.services.task_executer import TaskExecutor
from app.services.tools import ToolRegistry

logger = logging.getLogger(__name__)

PROTOCOL_TASK_CHAIN = "__TASK_CHAIN__:"


@dataclass
class ReActTurnState:
    """State container for multi-turn ReAct workflow execution."""

    user_prompt: str
    accumulated_all_text: list[str] = field(default_factory=list)
    last_chain_chunks: list[str] = field(default_factory=list)
    is_complete: bool = False
    turn_count: int = 0
    max_turns: int = 5


@dataclass
class ReActExecutionSummary:
    """Final output summary of a multi-turn ReAct execution cycle."""

    accumulated_text: str
    final_text: str
    last_execution: LLMExecution | None = None
    created_files: list[dict[str, Any]] = field(default_factory=list)


class ReActLoopRunner:
    """Service managing multi-turn ReAct reasoning and tool invocation cycles."""

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: AgentContextBuilder,
        tool_registry: ToolRegistry,
        email_service: Any | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.context_builder = context_builder
        self.tool_registry = tool_registry
        self.email_service = email_service

    def run_react_loop(
        self,
        user_text: str,
        conversation_id: str,
        agent_id: str,
        attachments: list[MessageAttachment],
        conversation_history: list[Any],
        on_turn_completed: Callable[[str, LLMExecution | None], None] | None = None,
    ) -> Generator[str, None, ReActExecutionSummary]:
        """
        Executes the ReAct loop iteratively, yielding stream chunks to the caller.

        Args:
            user_text: Initial user prompt.
            conversation_id: Active conversation UUID.
            agent_id: Target Agent UUID.
            attachments: Message attachments.
            conversation_history: Past conversation messages.
            on_turn_completed: Turn-end callback for intermediate persistence.

        Yields:
            str: Streamed text tokens for user output.

        Returns:
            ReActExecutionSummary: The aggregated execution result summary.
        """
        state = ReActTurnState(user_prompt=user_text)
        last_execution: LLMExecution | None = None
        all_created_files: list[dict[str, Any]] = []

        while not state.is_complete and state.turn_count < state.max_turns:
            state.turn_count += 1
            logger.info("[ReActLoopRunner] Starting Turn %d/%d...", state.turn_count, state.max_turns)

            extracted_json = yield from self._run_stream_turn(
                state=state,
                agent_id=agent_id,
                attachments=attachments,
                conversation_history=conversation_history,
            )

            current_text = "".join(state.accumulated_all_text).strip()
            if on_turn_completed:
                on_turn_completed(current_text, None)

            if not extracted_json:
                state.is_complete = True
                break

            execution = LLMExecution.from_json_payload(
                payload=extracted_json,
                conversation_id=conversation_id,
            )

            if not execution:
                state.is_complete = True
                break

            last_execution = execution
            if on_turn_completed:
                on_turn_completed(current_text, execution)

            last_result, step_files = yield from self._execute_task_chain(
                execution=execution,
                conversation_id=conversation_id,
                agent_id=agent_id,
                attachments=attachments,
                conversation_history=conversation_history,
                state=state,
            )

            if step_files:
                all_created_files.extend(step_files)

            if state.is_complete:
                break

            state.user_prompt = (
                f"Original User Query: {user_text}\n\n"
                f"Result from previous task step execution:\n{last_result}\n\n"
                f"Please formulate the next sub-plan step or final response using these actual result data."
            )

        final_text = (
            "".join(state.last_chain_chunks).strip()
            if state.last_chain_chunks
            else "".join(state.accumulated_all_text).strip()
        )

        return ReActExecutionSummary(
            accumulated_text="".join(state.accumulated_all_text).strip(),
            final_text=final_text,
            last_execution=last_execution,
            created_files=all_created_files,
        )

    def _run_stream_turn(
        self,
        state: ReActTurnState,
        agent_id: str,
        attachments: list[MessageAttachment],
        conversation_history: list[Any],
    ) -> Generator[str, None, dict[str, Any] | None]:
        """Streams a single turn, isolating embedded JSON blocks."""
        llm_messages = self.context_builder.build_llm_messages(
            user_text=state.user_prompt,
            agent_id=agent_id,
            attachments=attachments,
            conversation_history=conversation_history,
        )

        parser = StreamResponseParser()
        extracted_json: dict[str, Any] | None = None

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
        conversation_history: list[Any],
        state: ReActTurnState,
    ) -> Generator[str, None, tuple[str, list[dict[str, Any]]]]:
        """Executes tools specified in the task chain plan."""

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
                conversation_history=conversation_history,
            )
            yield from self.llm_service.stream(messages)

        executor = TaskExecutor(
            tools=self.tool_registry.get_tools(),
            llm_stream_func=llm_stream_adapter,
            email_service=self.email_service,
        )

        initial_context = {"conversation_id": conversation_id}
        chain_parser = StreamResponseParser()
        chain_text_chunks: list[str] = []
        last_result = ""
        created_files: list[dict[str, Any]] = []

        chain_gen = executor.execute_chain_stream(execution, initial_context=initial_context)

        try:
            while True:
                raw_chunk = next(chain_gen)
                if raw_chunk:
                    if PROTOCOL_TASK_CHAIN in raw_chunk:
                        yield raw_chunk
                        continue

                    display_text, _ = chain_parser.process_chunk(raw_chunk)
                    if display_text:
                        chain_text_chunks.append(display_text)
                        state.accumulated_all_text.append(display_text)
                        yield display_text
        except StopIteration as stop_err:
            if exec_result := stop_err.value:
                state.is_complete = getattr(exec_result, "is_complete", False)
                last_result = getattr(exec_result, "last_result", "") or ""
                created_files = getattr(exec_result, "created_files", []) or []

        rem_chain_text, _ = chain_parser.finalize()
        if rem_chain_text:
            chain_text_chunks.append(rem_chain_text)
            state.accumulated_all_text.append(rem_chain_text)
            yield rem_chain_text

        if chain_text_chunks:
            state.last_chain_chunks = chain_text_chunks

        return last_result, created_files
