"""LLM Domain Contracts and Protocols Module.

Defines unified message structures and streaming communication protocols for LLM providers.
"""

from dataclasses import dataclass
from typing import Generator, Protocol


@dataclass(slots=True)
class LLMMessage:
    """Represents a standardized chat message payload consumed by LLM providers.

    Attributes:
        role (str): The role of the message author (e.g., 'system', 'user', 'assistant').
        content (str): The text content of the message.
    """

    role: str
    content: str


class LLMProvider(Protocol):
    """Structural protocol defining the contract required for streaming LLM provider integrations."""

    def stream(self, messages: list[LLMMessage]) -> Generator[str, None, None]:
        """Streams text response chunks iteratively from the provider backend.

        Args:
            messages (list[LLMMessage]): Ordered sequence of prompt and context messages.

        Yields:
            str: Real-time generated token text chunks.

        Raises:
            LLMError: If communication or token generation encounters an unrecoverable failure.
        """
        ...
