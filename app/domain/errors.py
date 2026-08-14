"""Domain Errors Module.

Defines the centralized hierarchy of enterprise business rule exceptions,
resource lookup errors, data integrity failures, and subsystem execution faults.
"""

from typing import Any


class DomainError(Exception):
    """Base exception class for all domain-level errors."""

    def __init__(
        self,
        message: str,
        details: list[Any] | dict[str, Any] | None = None,
    ) -> None:
        """Initializes a DomainError instance.

        Args:
            message (str): Human-readable error description.
            details (list[Any] | dict[str, Any] | None): Optional structured metadata or validation errors.
        """
        super().__init__(message)
        self.message: str = message
        self.details: list[Any] | dict[str, Any] = details if details is not None else []

    def __repr__(self) -> str:
        """Returns a string representation of the exception."""
        return f"<{self.__class__.__name__}(message='{self.message}', details={self.details})>"


class NotFoundError(DomainError):
    """Base exception raised when an expected domain entity cannot be resolved."""

    pass


class AgentNotFoundError(NotFoundError):
    """Raised when a specific Agent entity cannot be located."""

    pass


class ConversationNotFoundError(NotFoundError):
    """Raised when a specific Conversation entity cannot be located."""

    pass


class DatasourceNotFoundError(NotFoundError):
    """Raised when a specific Datasource entity cannot be located."""

    pass


class MessageNotFoundError(NotFoundError):
    """Raised when a specific Message entity cannot be located."""

    pass


class LLMExecutionNotFoundError(NotFoundError):
    """Raised when a specific LLMExecution record cannot be located."""

    pass


class ToolNotFoundError(NotFoundError):
    """Raised when a requested execution tool or skill is not registered in the system."""

    pass


class ValidationError(DomainError):
    """Raised when domain entity constraints, contracts, or invariant rules are violated."""

    pass


class InvalidFileError(ValidationError):
    """Raised when an uploaded file payload is missing, empty, or fails security validation."""

    pass


class StorageError(DomainError):
    """Raised when physical storage, file I/O, or database persistence operations fail."""

    pass


class LLMError(DomainError):
    """Raised when an error occurs while communicating with LLM backend providers."""

    pass


class ToolExecutionError(DomainError):
    """Raised when an error occurs during the invocation or runtime execution of an agent tool."""

    pass
