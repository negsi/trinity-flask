"""
Task Chain Execution Engine Module.

Executes sequential steps of a structured LLM task chain and resolves dynamic context parameters.
"""

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
import inspect
import json
import logging
from pathlib import Path
from typing import Any

from app.domain.models.llm_execution import ExecutionStep, LLMExecution
from app.services.agent.constants import PROTOCOL_TASK_CHAIN

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChainExecutionResult:
    """Result data structure returned after task chain execution completes."""

    is_complete: bool
    context: dict[str, Any] = field(default_factory=dict)
    last_result: str = ""
    created_files: list[dict[str, Any]] = field(default_factory=list)


class TaskExecutor:
    """Executes structured tool steps and handles dynamic parameter replacements."""

    def __init__(
        self,
        tools: dict[str, Callable[..., Any]],
        llm_stream_func: Callable[[str], Generator[str, None, None]] | None = None,
        email_service: Any | None = None,
        conversations_folder: Path | str | None = None,
    ) -> None:
        self.tools = tools
        self.llm_stream_func = llm_stream_func
        self.email_service = email_service
        self.conversations_folder = str(conversations_folder) if conversations_folder is not None else None

    def execute_chain_stream(
        self,
        execution: LLMExecution,
        initial_context: dict[str, Any] | None = None,
    ) -> Generator[str, None, ChainExecutionResult]:
        """
        Executes sequence steps iteratively and streams output chunks.

        Args:
            execution: The LLMExecution domain model containing steps.
            initial_context: Initial contextual variables.

        Yields:
            str: Real-time text tokens from tool execution or sub-LLM prompts.

        Returns:
            ChainExecutionResult: Execution completion summary.
        """
        context: dict[str, Any] = dict(initial_context or {})
        steps: list[ExecutionStep] = execution.steps or []

        if steps:
            chain_init_payload = {
                "type": "task_chain_init",
                "steps": [
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "pending",
                    }
                    for step in steps
                ],
            }
            yield f"\n{PROTOCOL_TASK_CHAIN}{json.dumps(chain_init_payload)}\n"

        for step in steps:
            step_num = step.step_number
            tool_name = step.tool_name
            raw_params = step.parameters or {}

            yield f"\n{PROTOCOL_TASK_CHAIN}{json.dumps({'type': 'task_step_update', 'step_number': step_num, 'status': 'running'})}\n"
            logger.info("[TaskExecutor] Step %d (%s) Raw Params: %s", step_num, tool_name, raw_params)

            resolved_params = self._resolve_parameters(raw_params, context)

            if tool_name == "message_llm":
                yield from self._execute_llm_tool(step_num, resolved_params, context)
            else:
                yield from self._execute_standard_tool(step_num, tool_name, resolved_params, context)

            yield f"\n{PROTOCOL_TASK_CHAIN}{json.dumps({'type': 'task_step_update', 'step_number': step_num, 'status': 'completed'})}\n"

        return ChainExecutionResult(
            is_complete=execution.is_complete,
            context=context,
            last_result=context.get("last_result", ""),
            created_files=context.get("created_files", []),
        )

    def _execute_llm_tool(
        self,
        step_num: int,
        params: dict[str, Any],
        context: dict[str, Any],
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

        accumulated_response: list[str] = []
        try:
            for chunk in self.llm_stream_func(prompt):
                if chunk:
                    accumulated_response.append(chunk)
                    yield chunk
        except Exception as exc:
            error_msg = f"\n[Error during LLM execution in Step {step_num}: {exc}]"
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
        params: dict[str, Any],
        context: dict[str, Any],
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

            # Inspect signature to verify accepted parameters before injecting context kwargs
            candidate_context_kwargs: dict[str, Any] = {}
            if "conversation_id" in context:
                candidate_context_kwargs["conversation_id"] = context["conversation_id"]
            if "base_dir" in context:
                candidate_context_kwargs["base_dir"] = context["base_dir"]
            if self.email_service is not None:
                candidate_context_kwargs["email_service"] = self.email_service

            try:
                sig = inspect.signature(tool_func)
                has_var_keyword = any(
                    param.kind == inspect.Parameter.VAR_KEYWORD
                    for param in sig.parameters.values()
                )
                accepted_param_names = set(sig.parameters.keys())
            except (ValueError, TypeError):
                has_var_keyword = False
                accepted_param_names = set()

            for key, val in candidate_context_kwargs.items():
                if key not in exec_params and (has_var_keyword or key in accepted_param_names):
                    exec_params[key] = val

            tool_raw_result = tool_func(**exec_params)
            output = str(tool_raw_result)
            context[f"step_{step_num}"] = output
            context["last_result"] = output

            if "created_files" not in context:
                context["created_files"] = []

            self._collect_created_files(tool_name, tool_raw_result, exec_params, context, output)
        except Exception as exc:
            err_msg = f"\n[Error executing tool '{tool_name}' in Step {step_num}: {exc}]"
            logger.error(err_msg, exc_info=True)
            yield err_msg

    def _collect_created_files(
        self,
        tool_name: str,
        raw_result: Any,
        exec_params: dict[str, Any],
        context: dict[str, Any],
        output_str: str,
    ) -> None:
        """Registers newly created or generated files in the execution context."""
        conversation_id = exec_params.get("conversation_id") or context.get("conversation_id")
        base_dir = (
            exec_params.get("base_dir")
            or context.get("base_dir")
            or self.conversations_folder
        )

        if tool_name == "generate_image" and isinstance(raw_result, dict) and raw_result.get("status") == "success":
            filename = raw_result.get("filename")
            if filename:
                if base_dir and conversation_id:
                    clean_path = str(Path(base_dir) / str(conversation_id) / filename)
                elif conversation_id:
                    clean_path = str(Path(conversation_id) / filename)
                else:
                    clean_path = filename

                context["created_files"].append({
                    "filename": filename,
                    "file_path": clean_path,
                    "conversation_id": conversation_id,
                    "base_dir": str(base_dir) if base_dir else None,
                })
        elif tool_name == "write_file" and not output_str.startswith("Error"):
            file_path = exec_params.get("file_path")
            if file_path:
                context["created_files"].append({
                    "filename": Path(file_path).name,
                    "file_path": file_path,
                    "conversation_id": conversation_id,
                    "base_dir": str(base_dir) if base_dir else None,
                })

    def _resolve_parameters(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Recursively resolves dynamic context placeholders across parameter dictionaries."""
        return {k: self._resolve_value(v, context) for k, v in params.items()}

    def _resolve_value(self, val: Any, context: dict[str, Any]) -> Any:
        """Resolves placeholder tokens in parameter values."""
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
