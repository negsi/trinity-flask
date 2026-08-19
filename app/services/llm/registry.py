"""
LLM Provider Registry Module.

Manages provider class bindings and singleton provider lifecycle caching.
"""

from app.domain.llm import LLMProvider
from app.services.llm.providers import GeminiProvider, OpenAIProvider


class ProviderRegistry:
    """Registry maintaining available LLM provider instances."""

    def __init__(self, model_name: str) -> None:
        self._provider_classes: dict[str, type[LLMProvider]] = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
        }
        self._instances: dict[str, LLMProvider] = {}
        self.model_name = model_name

    def get(self, name: str) -> LLMProvider:
        """
        Retrieves or initializes a provider instance.

        Args:
            name: Provider key identifier ('openai', 'gemini').

        Returns:
            LLMProvider: Active provider instance.

        Raises:
            ValueError: If the provider name is unregistered.
        """
        clean_name = name.strip().lower()
        if clean_name not in self._provider_classes:
            raise ValueError(f"Provider '{clean_name}' is not registered in ProviderRegistry.")

        if clean_name not in self._instances:
            provider_cls = self._provider_classes[clean_name]
            self._instances[clean_name] = provider_cls(model=self.model_name)

        return self._instances[clean_name]
