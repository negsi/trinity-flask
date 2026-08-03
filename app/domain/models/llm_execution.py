"""
LLM Execution Domain Models.

Tracks ReAct task chains, tool execution plans, step execution states, and response types.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional


class ResponseType(str, Enum):
    """Categorizes the nature of the LLM response execution format."""
    SIMPLE_MESSAGE = "simple_message"
    TASK_CHAIN = "task_chain"


@dataclass
class ExecutionStep:
    """Represents a single step in a multi-tool ReAct task execution plan."""
    step_number: int
    description: str
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # Status values: pending, running, completed, failed
    result: Optional[str] = None


@dataclass
class LLMExecution:
    """Domain entity representing an overall task-chain execution lifecycle."""
    conversation_id: str
    message_id: Optional[str] = None
    response_type: ResponseType = ResponseType.SIMPLE_MESSAGE
    summary_or_content: str = ""
    is_complete: bool = True
    steps: List[ExecutionStep] = field(default_factory=list)
    id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serializes the execution object and all child steps into a dict structure."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "response_type": self.response_type.value,
            "summary_or_content": self.summary_or_content,
            "is_complete": self.is_complete,
            "steps": [
                {
                    "step": s.step_number,
                    "description": s.description,
                    "tool": s.tool_name,
                    "parameters": s.parameters,
                    "status": s.status,
                    "result": s.result
                }
                for s in self.steps
            ],
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_json_payload(
        cls, 
        payload: dict, 
        conversation_id: str, 
        message_id: Optional[str] = None
    ) -> Optional["LLMExecution"]:
        """
        Constructs an LLMExecution object from parsed structured JSON returned by the LLM.

        Args:
            payload (dict): Parsed JSON dictionary payload from the LLM.
            conversation_id (str): Associated conversation ID.
            message_id (Optional[str]): Associated parent message ID.

        Returns:
            Optional[LLMExecution]: Instantiated execution model if response is a task chain.
        """
        response_data = payload.get("response", {})
        type_str = response_data.get("type")

        if type_str != ResponseType.TASK_CHAIN.value:
            return None

        is_complete = response_data.get("is_complete", True)

        raw_steps = response_data.get("steps", [])
        steps = [
            ExecutionStep(
                step_number=s.get("step", 0),
                description=s.get("description", ""),
                tool_name=s.get("tool"),
                parameters=s.get("parameters", {}),
                status="pending"
            )
            for s in raw_steps
        ]

        return cls(
            conversation_id=conversation_id,
            message_id=message_id,
            response_type=ResponseType.TASK_CHAIN,
            summary_or_content=response_data.get("summary", ""),
            is_complete=is_complete,
            steps=steps
        )
