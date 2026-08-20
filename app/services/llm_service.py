"""
LLM Service Proxy Module.

Routes prompt message sequences to configured provider backends via the Provider Registry.
"""

from collections.abc import Generator
import logging

from app.domain.llm import LLMMessage
from app.services.llm.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class LLMService:
    """Service proxy routing LLM prompts to selected provider backends."""

    def __init__(
        self,
        default_provider: str = "gemini",
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self.registry = ProviderRegistry(model_name=model_name)
        self.default_provider = default_provider

    def stream(
        self,
        messages: list[LLMMessage],
        provider_name: str | None = None,
    ) -> Generator[str, None, None]:
        """
        Streams response chunks from the designated LLM provider.

        Args:
            messages: Sequence of prompt messages.
            provider_name: Target provider override.

        Yields:
            str: Response token chunks.
        """
        name = provider_name or self.default_provider
        provider = self.registry.get(name)
        logger.debug("Routing request to LLM provider: '%s'", name)
        yield from provider.stream(messages)
