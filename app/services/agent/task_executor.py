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

from app.domain.enums import ExecutionStepStatus
from app.domain.models.llm_execution import ExecutionStep, LLMExecution
from app.domain.repositories.llm_execution_repository import LLMExecutionRepository
from app.services.agent.constants import PROTOCOL_TASK_CHAIN
from app.services.agent.constants import PAYLOAD_REF_PREFIX

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
        execution_repository: LLMExecutionRepository | None = None,
    ) -> None:
        self.tools = tools
        self.llm_stream_func = llm_stream_func
        self.email_service = email_service
        self.conversations_folder = str(conversations_folder) if conversations_folder is not None else None
        self.execution_repository = execution_repository

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
                "call_depth": context.get("call_depth", 0),
                "agent_id": context.get("agent_id"),
                "steps": [
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "parameters": step.parameters or {},
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

            # 1. Update DB: Step running
            step.status = ExecutionStepStatus.RUNNING
            self._update_step_in_db(execution.id, step_num, ExecutionStepStatus.RUNNING)

            yield f"\n{PROTOCOL_TASK_CHAIN}{json.dumps({'type': 'task_step_update', 'step_number': step_num, 'status': 'running'})}\n"
            logger.info("[TaskExecutor] Step %d (%s) Raw Params: %s", step_num, tool_name, raw_params)

            resolved_params = self._resolve_parameters(raw_params, context)

            step_failed = False
            try:
                if tool_name == "message_llm":
                    yield from self._execute_llm_tool(step_num, resolved_params, context)
                else:
                    yield from self._execute_standard_tool(step_num, tool_name, resolved_params, context)
            except Exception as exc:
                step_failed = True
                logger.error("[TaskExecutor] Execution failed for Step %d: %s", step_num, exc, exc_info=True)

            step_result = str(context.get(f"step_{step_num}", ""))
            final_status = ExecutionStepStatus.FAILED if step_failed else ExecutionStepStatus.COMPLETED
            
            step.status = final_status
            step.result = step_result

            # 2. Update DB: Step completed / failed mit Resultat
            self._update_step_in_db(execution.id, step_num, final_status, step_result)

            yield f"\n{PROTOCOL_TASK_CHAIN}{json.dumps({
                'type': 'task_step_update',
                'step_number': step_num,
                'status': final_status.value,
                'result': step_result
            })}\n"

        return ChainExecutionResult(
            is_complete=execution.is_complete,
            context=context,
            last_result=context.get("last_result", ""),
            created_files=context.get("created_files", []),
        )

    def _update_step_in_db(
        self,
        execution_id: str,
        step_number: int,
        status: ExecutionStepStatus,
        result: str | None = None,
    ) -> None:
        """Helper to safely trigger single step row updates in DB."""
        if not self.execution_repository or not execution_id:
            return

        try:
            self.execution_repository.update_step(
                execution_id=execution_id,
                step_number=step_number,
                status=status,
                result=result,
            )
        except Exception as exc:
            logger.error(
                "Failed to persist step update in DB (Execution: %s, Step: %d): %s",
                execution_id,
                step_number,
                exc,
            )

    def _execute_llm_tool(
        self,
        step_num: int,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> Generator[str, None, None]:
        """Executes nested LLM streaming tool requests."""
        prompt = str(
            params.get("prompt")
            or params.get("message")
            or params.get("text")
            or ""
        ).strip()
        
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
        if tool_name not in self.tools:
            err = f"\n[Error: Tool '{tool_name}' is not registered.]"
            logger.error(err)
            context[f"step_{step_num}"] = err
            yield err
            return

        try:
            tool_func = self.tools[tool_name]
            exec_params = dict(params)

            queued_events: list[str] = []

            def handle_sub_event(event_chunk: str) -> None:
                queued_events.append(event_chunk)

            candidate_context_kwargs: dict[str, Any] = {}
            if "conversation_id" in context:
                candidate_context_kwargs["conversation_id"] = context["conversation_id"]
            if "agent_id" in context:
                candidate_context_kwargs["current_agent_id"] = context["agent_id"]
            if "call_depth" in context:
                candidate_context_kwargs["call_depth"] = context["call_depth"]
            if "base_dir" in context:
                candidate_context_kwargs["base_dir"] = context["base_dir"]
            if self.email_service is not None:
                candidate_context_kwargs["email_service"] = self.email_service
            
            candidate_context_kwargs["on_event"] = handle_sub_event

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

            was_generator = inspect.isgenerator(tool_raw_result)
            if was_generator:
                try:
                    while True:
                        event_chunk = next(tool_raw_result)
                        if event_chunk:
                            yield event_chunk
                except StopIteration as stop_err:
                    tool_raw_result = stop_err.value

            for event in queued_events:
                yield event

            output = str(tool_raw_result)
            context[f"step_{step_num}"] = output
            context["last_result"] = output

            if tool_name == "message_agent" and output and not was_generator:
                yield output

            if "created_files" not in context:
                context["created_files"] = []

            self._collect_created_files(tool_name, tool_raw_result, exec_params, context, output)
        except Exception as exc:
            err_msg = f"\n[Error executing tool '{tool_name}' in Step {step_num}: {exc}]"
            logger.error(err_msg, exc_info=True)
            context[f"step_{step_num}"] = err_msg
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

        if tool_name in ("generate_image", "manage_odf") and isinstance(raw_result, dict) and raw_result.get("status") == "success":
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
                filename = Path(file_path).name
                
                if base_dir and conversation_id:
                    clean_path = str(Path(base_dir) / str(conversation_id) / filename)
                else:
                    clean_path = str(Path(file_path))

                context["created_files"].append({
                    "filename": filename,
                    "file_path": clean_path,
                    "conversation_id": conversation_id,
                    "base_dir": str(base_dir) if base_dir else None,
                })

    def _resolve_parameters(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Recursively resolves dynamic context placeholders and decoupled payloads across parameters."""
        return {k: self._resolve_value(v, context) for k, v in params.items()}

    def _resolve_value(self, val: Any, context: dict[str, Any]) -> Any:
        """Resolves payload references (REF:...) and step placeholder tokens in parameter values."""
        if isinstance(val, str):
            stripped = val.strip()
            payloads: dict[str, str] = context.get("payloads", {})

            # 1. Direct Payload Resolution (e.g. "REF:PAYLOAD_STEP_1" or "PAYLOAD_STEP_1")
            if stripped.startswith("REF:"):
                ref_key = stripped[4:].strip()
                if ref_key in payloads:
                    val = payloads[ref_key]
                    stripped = val.strip() if isinstance(val, str) else ""

            elif stripped in payloads:
                val = payloads[stripped]
                stripped = val.strip() if isinstance(val, str) else ""

            # 2. Embedded Payload Resolution (if REF: appears inside a longer template string)
            if isinstance(val, str) and "REF:" in val:
                for p_key, p_val in payloads.items():
                    target_ref = f"REF:{p_key}"
                    if target_ref in val:
                        val = val.replace(target_ref, p_val)

            # 3. Context Step Placeholder Resolution ([STEP_1], [CONVERSATION_ID], etc.)
            if isinstance(val, str):
                stripped = val.strip()
                for ctx_key, ctx_val in context.items():
                    if ctx_key == "payloads":
                        continue

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
