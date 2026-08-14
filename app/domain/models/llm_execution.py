"""LLM Execution Domain Models Module.

Defines execution lifecycle states, ReAct multi-step tool plans, and structured response parsers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Self
import uuid

from app.domain.enums import ExecutionStepStatus, ResponseType
from app.domain.errors import ValidationError


@dataclass(slots=True)
class ExecutionStep:
    """Represents a single step in a multi-turn ReAct task execution plan.

    Attributes:
        step_number (int): Order index of the step within the chain.
        description (str): Human-readable explanation of the step's goal.
        tool_name (str | None): Identifier of the tool or skill to invoke.
        parameters (dict[str, Any]): Arguments passed to the tool invocation.
        status (ExecutionStepStatus): Current execution state of this step.
        result (str | None): Output string generated upon tool execution.
    """

    step_number: int
    description: str
    tool_name: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    status: ExecutionStepStatus = ExecutionStepStatus.PENDING
    result: str | None = None

    def __post_init__(self) -> None:
        """Validates execution step constraints.

        Raises:
            ValidationError: If step properties are invalid.
        """
        if self.step_number < 0:
            raise ValidationError("Step number cannot be negative.")

        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", ExecutionStepStatus(self.status))
            except ValueError:
                raise ValidationError(f"Invalid step status '{self.status}'.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the execution step into a dictionary format.

        Returns:
            dict[str, Any]: Serialized step data.
        """
        return {
            "step": self.step_number,
            "description": self.description,
            "tool": self.tool_name,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": self.result,
        }


@dataclass(slots=True)
class LLMExecution:
    """Domain entity tracking the state, plan, and results of an LLM ReAct task execution cycle.

    Attributes:
        conversation_id (str): Unique UUID of the associated conversation.
        message_id (str | None): Optional message ID triggered by or creating this execution.
        response_type (ResponseType): Whether the execution is a simple message or a task chain.
        summary_or_content (str): Summary text or raw final generated output.
        is_complete (bool): Flag indicating whether the entire execution plan has terminated.
        steps (list[ExecutionStep]): Ordered list of execution sub-steps.
        id (str): Unique UUID identifier.
        created_at (datetime): Creation timestamp.
    """

    conversation_id: str
    message_id: str | None = None
    response_type: ResponseType = ResponseType.SIMPLE_MESSAGE
    summary_or_content: str = ""
    is_complete: bool = True
    steps: list[ExecutionStep] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validates the execution domain entity.

        Raises:
            ValidationError: If invariants are violated.
        """
        if not self.conversation_id or not self.conversation_id.strip():
            raise ValidationError("LLMExecution conversation_id cannot be empty.")

        if isinstance(self.response_type, str):
            try:
                object.__setattr__(self, "response_type", ResponseType(self.response_type))
            except ValueError:
                raise ValidationError(f"Invalid response type '{self.response_type}'.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the execution lifecycle model into a dictionary.

        Returns:
            dict[str, Any]: Serialized execution dictionary.
        """
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "response_type": self.response_type.value,
            "summary_or_content": self.summary_or_content,
            "is_complete": self.is_complete,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_json_payload(
        cls,
        payload: dict[str, Any],
        conversation_id: str,
        message_id: str | None = None,
    ) -> Self | None:
        """Parses structured JSON response from an LLM into an LLMExecution task chain entity.

        Args:
            payload (dict[str, Any]): Structured JSON dictionary returned by the LLM.
            conversation_id (str): Associated conversation UUID.
            message_id (str | None): Optional associated message UUID.

        Returns:
            Self | None: An instantiated LLMExecution entity if payload matches a task chain, else None.
        """
        if not isinstance(payload, dict):
            return None

        response_data = payload.get("response")
        if not isinstance(response_data, dict):
            return None

        type_str = response_data.get("type")
        if type_str != ResponseType.TASK_CHAIN.value:
            return None

        is_complete = bool(response_data.get("is_complete", True))
        raw_steps = response_data.get("steps", [])

        steps: list[ExecutionStep] = []
        if isinstance(raw_steps, list):
            for s in raw_steps:
                if isinstance(s, dict):
                    step_num = s.get("step")
                    if isinstance(step_num, int):
                        steps.append(
                            ExecutionStep(
                                step_number=step_num,
                                description=str(s.get("description", "")),
                                tool_name=s.get("tool") if s.get("tool") else None,
                                parameters=s.get("parameters") if isinstance(s.get("parameters"), dict) else {},
                                status=ExecutionStepStatus.PENDING,
                            )
                        )

        return cls(
            conversation_id=conversation_id,
            message_id=message_id,
            response_type=ResponseType.TASK_CHAIN,
            summary_or_content=str(response_data.get("summary", "")),
            is_complete=is_complete,
            steps=steps,
        )
