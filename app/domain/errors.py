"""
Domain Errors Module.

Defines the hierarchy of domain exceptions representing business rule violations,
entity lookup failures, validation errors, and subsystem execution failures.
"""

from typing import Any, Dict, List, Optional, Union


class DomainError(Exception):
    """Base exception class for all domain-level errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(DomainError):
    """Raised when a requested domain entity cannot be found."""

    pass


class AgentNotFoundError(NotFoundError):
    """Raised when a requested Agent entity does not exist."""

    pass


class DatasourceNotFoundError(NotFoundError):
    """Raised when a requested Datasource entity does not exist."""

    pass


class ConversationNotFoundError(NotFoundError):
    """Raised when a requested Conversation entity does not exist."""

    pass


class MessageNotFoundError(NotFoundError):
    """Raised when a requested Message entity does not exist."""

    pass


class ValidationError(DomainError):
    """Raised when domain entity constraints or business rules are violated."""

    pass


class InvalidFileError(ValidationError):
    """Raised when an uploaded file is missing, empty, or invalid."""

    pass


class StorageError(DomainError):
    """Raised when file storage or disk I/O operations fail."""

    pass


class LLMError(DomainError):
    """Raised when an error occurs during interaction with LLM backend providers."""

    pass


class ToolNotFoundError(NotFoundError):
    """Raised when a requested execution tool is not registered in the system."""

    pass


class ToolExecutionError(DomainError):
    """Raised when an error occurs during the execution of an agent skill or tool."""

    pass
