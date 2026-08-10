"""
Task Chain Execution Engine.

Executes individual steps of a structured LLM task chain and resolves context parameters.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChainExecutionResult:
    """Result data structure returned after task chain execution finishes."""
    is_complete: bool
    context: Dict[str, Any] = field(default_factory=dict)
    last_result: str = ""


class TaskExecutor:
    """Executes structured tool steps and handles dynamic parameter replacements."""

    def __init__(
        self,
        tools: Dict[str, Callable],
        llm_stream_func: Optional[Callable[[str], Generator[str, None, None]]] = None,
        email_service: Optional[Any] = None
    ):
        self.tools = tools
        self.llm_stream_func = llm_stream_func
        self.email_service = email_service

    def execute_chain_stream(
        self, execution: Any,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, ChainExecutionResult]:
        """
        Executes sequence steps and streams live output chunks.

        Args:
            execution (Any): Task chain execution dataclass model.

        Yields:
            Generator[str, None, ChainExecutionResult]: Live execution output strings.
        """
        context: Dict[str, Any] = initial_context.copy() if initial_context else {}

        for step in execution.steps:
            step_num = step.step_number
            tool_name = step.tool_name
            raw_params = step.parameters or {}

            logger.info(f"[TaskExecutor] Step {step_num} ({tool_name}) Params: {raw_params}")
            resolved_params = self._resolve_parameters(raw_params, context)

            # Strategy dispatching
            if tool_name == "message_llm":
                yield from self._execute_llm_tool(step_num, resolved_params, context)
            else:
                yield from self._execute_standard_tool(step_num, tool_name, resolved_params, context)

        is_complete = getattr(execution, "is_complete", True)
        
        return ChainExecutionResult(
            is_complete=is_complete,
            context=context,
            last_result=context.get("last_result", "")
        )

    def _execute_llm_tool(
        self, step_num: int, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """Executes embedded nested LLM streaming tool requests."""
        prompt = params.get("message", "").strip()
        if not prompt:
            logger.warning(f"[TaskExecutor] Step {step_num}: Empty prompt string for message_llm.")
            return

        if not self.llm_stream_func:
            output = "LLM streaming function is unavailable."
            context[f"step_{step_num}"] = output
            context["last_result"] = output
            yield output
            return

        # Ensures double linebreaks between sequential LLM streaming outputs in UI
        if context.get("has_previous_llm_output", False):
            yield "\n\n"

        accumulated_response = []
        try:
            for chunk in self.llm_stream_func(prompt):
                if chunk:
                    accumulated_response.append(chunk)
                    yield chunk
        except Exception as e:
            error_msg = f"\n[Error during LLM execution in Step {step_num}: {e}]"
            logger.error(error_msg, exc_info=True)
            yield error_msg
            accumulated_response.append(error_msg)

        full_output = "".join(accumulated_response)
        context[f"step_{step_num}"] = full_output
        context["last_result"] = full_output
        context["has_previous_llm_output"] = True

    def _execute_standard_tool(
        self, step_num: int, tool_name: str, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """Executes standard Python tool functions from the tools registry."""
        if tool_name not in self.tools:
            err = f"\n[Error: Tool '{tool_name}' is not registered.]"
            logger.error(err)
            yield err
            return

        try:
            tool_func = self.tools[tool_name]
            
            # Pass contextual variables if expected
            if "conversation_id" in context and "conversation_id" not in params:
                params["conversation_id"] = context["conversation_id"]
            if "base_dir" in context and "base_dir" not in params:
                params["base_dir"] = context["base_dir"]
            if self.email_service and "email_service" not in params:
                params["email_service"] = self.email_service

            output = str(tool_func(**params))
            context[f"step_{step_num}"] = output
            context["last_result"] = output
        except Exception as e:
            err_msg = f"\n[Error executing tool '{tool_name}' in Step {step_num}: {e}]"
            logger.error(err_msg, exc_info=True)
            yield err_msg

    def _resolve_parameters(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolves dynamic contextual placeholder tokens in tool parameters."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str):
                for ctx_key, ctx_val in context.items():
                    val_str = str(ctx_val)
                    value = value.replace(f"[{ctx_key.upper()}]", val_str)
                    value = value.replace(f"[{ctx_key.lower()}]", val_str)
            resolved[key] = value
        return resolved