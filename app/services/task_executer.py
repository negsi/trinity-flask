"""
Task Chain Execution Engine Module.

Executes sequential steps of a structured LLM task chain and resolves dynamic context parameters.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Callable, Dict, Generator, Optional

from app.domain.errors import ToolNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ChainExecutionResult:
    """Result data structure returned after task chain execution completes."""

    is_complete: bool
    context: Dict[str, Any] = field(default_factory=dict)
    last_result: str = ""


class TaskExecutor:
    """Executes structured tool steps and handles dynamic parameter replacements."""

    def __init__(
        self,
        tools: Dict[str, Callable[..., Any]],
        llm_stream_func: Optional[Callable[[str], Generator[str, None, None]]] = None,
        email_service: Optional[Any] = None,
    ) -> None:
        self.tools = tools
        self.llm_stream_func = llm_stream_func
        self.email_service = email_service

    def execute_chain_stream(
        self,
        execution: Any,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, ChainExecutionResult]:
        """
        Executes sequence steps iteratively and streams output chunks.

        Args:
            execution (Any): The LLMExecution domain model containing steps.
            initial_context (Optional[Dict[str, Any]]): Initial contextual variables.

        Yields:
            str: Real-time text tokens from tool execution or sub-LLM prompts.

        Returns:
            ChainExecutionResult: Execution completion summary.
        """
        context: Dict[str, Any] = dict(initial_context) if initial_context else {}

        for step in getattr(execution, "steps", []):
            step_num = getattr(step, "step_number", 0)
            tool_name = getattr(step, "tool_name", "")
            raw_params = getattr(step, "parameters", {}) or {}

            logger.info("[TaskExecutor] Step %d (%s) Raw Params: %s", step_num, tool_name, raw_params)
            resolved_params = self._resolve_parameters(raw_params, context)

            if tool_name == "message_llm":
                yield from self._execute_llm_tool(step_num, resolved_params, context)
            else:
                yield from self._execute_standard_tool(step_num, tool_name, resolved_params, context)

        is_complete = getattr(execution, "is_complete", True)
        return ChainExecutionResult(
            is_complete=is_complete,
            context=context,
            last_result=context.get("last_result", ""),
        )

    def _execute_llm_tool(
        self,
        step_num: int,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Generator[str, None, None]:
        """Executes nested LLM streaming tool requests."""
        prompt = str(params.get("message", "")).strip()
        if not prompt:
            logger.warning("[TaskExecutor] Step %d: Empty prompt for message_llm.", step_num)
            return

        if not self.llm_stream_func:
            output = "LLM streaming function is unavailable."
            context[f"step_{step_num}"] = output
            context["last_result"] = output
            yield output
            return

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
        self,
        step_num: int,
        tool_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Generator[str, None, None]:
        """Executes standard callable tool functions."""
        if tool_name not in self.tools:
            err = f"\n[Error: Tool '{tool_name}' is not registered.]"
            logger.error(err)
            yield err
            return

        try:
            tool_func = self.tools[tool_name]
            exec_params = dict(params)

            if "conversation_id" in context and "conversation_id" not in exec_params:
                exec_params["conversation_id"] = context["conversation_id"]
            if "base_dir" in context and "base_dir" not in exec_params:
                exec_params["base_dir"] = context["base_dir"]
            if self.email_service and "email_service" not in exec_params:
                exec_params["email_service"] = self.email_service

            output = str(tool_func(**exec_params))
            context[f"step_{step_num}"] = output
            context["last_result"] = output
        except Exception as e:
            err_msg = f"\n[Error executing tool '{tool_name}' in Step {step_num}: {e}]"
            logger.error(err_msg, exc_info=True)
            yield err_msg

    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Recursively resolves dynamic contextual placeholders across parameter dictionaries."""
        return {k: self._resolve_value(v, context) for k, v in params.items()}

    def _resolve_value(self, val: Any, context: Dict[str, Any]) -> Any:
        """Resolves dynamic placeholder tokens within strings, lists, and dicts."""
        if isinstance(val, str):
            stripped = val.strip()
            for ctx_key, ctx_val in context.items():
                token_upper = f"[{ctx_key.upper()}]"
                token_lower = f"[{ctx_key.lower()}]"

                if stripped in (token_upper, token_lower):
                    return ctx_val

                val_str = str(ctx_val)
                if token_upper in val:
                    val = val.replace(token_upper, val_str)
                if token_lower in val:
                    val = val.replace(token_lower, val_str)
            return val
        if isinstance(val, dict):
            return {k: self._resolve_value(v, context) for k, v in val.items()}
        if isinstance(val, list):
            return [self._resolve_value(item, context) for item in val]
        return val
