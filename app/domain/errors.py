"""
Domain Errors Module.

Contains core application exceptions representing domain-level business logic rule violations.
"""


class DomainError(Exception):
    """Base exception class for all domain errors."""

    def __init__(self, message: str, details: list | dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(DomainError):
    """Raised when a requested domain entity cannot be found."""

    pass


class ValidationError(DomainError):
    """Raised when entity validation rules are violated."""

    pass


class LLMError(DomainError):
    """Raised when an error occurs during interaction with LLM services."""

    pass


class ToolExecutionError(DomainError):
    """Raised when an error occurs during agent tool execution."""

    pass
