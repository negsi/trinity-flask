"""
LLM Domain Interfaces and Dataclasses.

Defines core message abstractions and provider contracts for streaming LLM communication.
"""

from dataclasses import dataclass
from typing import Generator, List, Protocol


@dataclass
class LLMMessage:
    """Represents a unified chat message object for LLM providers."""
    role: str  # E.g., "system", "user", or "assistant"
    content: str


class LLMProvider(Protocol):
    """Protocol establishing the required interface for LLM provider integration."""

    def stream(self, messages: List[LLMMessage]) -> Generator[str, None, None]:
        """
        Streams response tokens iteratively from the LLM provider.

        Args:
            messages (List[LLMMessage]): List of prompt messages.

        Yields:
            Generator[str, None, None]: Text token chunks.
        """
        ...
