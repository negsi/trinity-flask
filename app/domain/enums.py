"""Domain Enumerations Module.

Provides centralized, string-serialized enumeration types utilized across domain entities,
business logic validations, and API interfaces.
"""

from enum import Enum


class ActorType(str, Enum):
    """Represents the category of actor interacting within the messaging system."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

    def __str__(self) -> str:
        """Returns the string value of the enumeration."""
        return self.value


class ResponseType(str, Enum):
    """Categorizes the nature of an LLM generation format."""

    SIMPLE_MESSAGE = "simple_message"
    TASK_CHAIN = "task_chain"

    def __str__(self) -> str:
        """Returns the string value of the enumeration."""
        return self.value


class MemoryMode(str, Enum):
    """Defines which message history types are included in agent memory context."""

    USER_ONLY = "user_only"
    ALL = "all"

    def __str__(self) -> str:
        """Returns the string value of the enumeration."""
        return self.value


class MemoryLimitType(str, Enum):
    """Defines the bounding strategy applied to agent conversation history."""

    ALL = "all"
    MESSAGE_COUNT = "message_count"

    def __str__(self) -> str:
        """Returns the string value of the enumeration."""
        return self.value


class ExecutionStepStatus(str, Enum):
    """Represents the lifecycle execution state of an individual ReAct task step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    def __str__(self) -> str:
        """Returns the string value of the enumeration."""
        return self.value
