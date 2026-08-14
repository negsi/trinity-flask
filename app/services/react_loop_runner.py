"""
ReAct Loop Runner Module.

Encapsulates multi-turn reasoning and tool execution loops, managing turn iterations,
sub-step stream parsing, and conversational follow-up prompt compilation.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from app.domain.models.llm_execution import LLMExecution
from app.domain.models.message_attachment import MessageAttachment
from app.services.agent_context_builder import AgentContextBuilder
from app.services.llm.stream_parser import StreamResponseParser
from app.services.llm_service import LLMService
from app.services.task_executer import TaskExecutor
from app.services.tools import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ReActTurnState:
    """State container for multi-turn ReAct workflow execution."""

    user_prompt: str
    accumulated_all_text: List[str] = field(default_factory=list)
    last_chain_chunks: List[str] = field(default_factory=list)
    is_complete: bool = False
    turn_count: int = 0
    max_turns: int = 5


@dataclass
class ReActExecutionSummary:
    """Final output summary of a multi-turn ReAct execution cycle."""

    accumulated_text: str
    final_text: str
    last_execution: Optional[LLMExecution] = None


class ReActLoopRunner:
    """Service managing the multi-turn ReAct reasoning and tool invocation lifecycle."""

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: AgentContextBuilder,
        tool_registry: ToolRegistry,
        email_service: Optional[Any] = None,
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
        attachments: List[MessageAttachment],
        conversation_history: List[Any],
        on_turn_completed: Optional[Callable[[str, Optional[LLMExecution]], None]] = None,
    ) -> Generator[str, None, ReActExecutionSummary]:
        """
        Executes the ReAct loop iteratively, yielding text stream chunks to the caller.

        Args:
            user_text (str): Initial user prompt.
            conversation_id (str): Conversation UUID.
            agent_id (str): Target Agent UUID.
            attachments (List[MessageAttachment]): Associated user attachments.
            conversation_history (List[Any]): Past conversation messages.
            on_turn_completed (Optional[Callable]): Callback invoked when an execution turn completes.

        Yields:
            str: Streamed text tokens for live user display.

        Returns:
            ReActExecutionSummary: The aggregated execution result summary.
        """
        state = ReActTurnState(user_prompt=user_text)
        last_execution: Optional[LLMExecution] = None

        while not state.is_complete and state.turn_count < state.max_turns:
            state.turn_count += 1
            logger.info("[ReActLoopRunner] Starting ReAct Turn %d/%d...", state.turn_count, state.max_turns)

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

            last_result = yield from self._execute_task_chain(
                execution=execution,
                conversation_id=conversation_id,
                agent_id=agent_id,
                attachments=attachments,
                conversation_history=conversation_history,
                state=state,
            )

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
        )

    def _run_stream_turn(
        self,
        state: ReActTurnState,
        agent_id: str,
        attachments: List[MessageAttachment],
        conversation_history: List[Any],
    ) -> Generator[str, None, Optional[Dict[str, Any]]]:
        """Streams a single LLM turn, isolating embedded JSON blocks."""
        llm_messages = self.context_builder.build_llm_messages(
            user_text=state.user_prompt,
            agent_id=agent_id,
            attachments=attachments,
            conversation_history=conversation_history,
        )

        parser = StreamResponseParser()
        extracted_json: Optional[Dict[str, Any]] = None

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
        attachments: List[MessageAttachment],
        conversation_history: List[Any],
        state: ReActTurnState,
    ) -> Generator[str, None, str]:
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
        chain_text_chunks: List[str] = []
        last_result = ""

        chain_gen = executor.execute_chain_stream(execution, initial_context=initial_context)

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
