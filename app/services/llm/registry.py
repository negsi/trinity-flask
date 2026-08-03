from typing import Dict, Type
from app.domain.llm import LLMProvider
from app.services.llm.providers import OpenAIProvider, GeminiProvider

class ProviderRegistry:
    def __init__(self, model_name: str):
        self._providers: Dict[str, Type[LLMProvider]] = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider
        }
        self._instances: Dict[str, LLMProvider] = {}
        self.model_name = model_name

    def get(self, name: str) -> LLMProvider:
        name = name.lower()
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' ist in der Registry nicht bekannt.")
        
        if name not in self._instances:
            # Modellname wird hier dynamisch mitgegeben
            self._instances[name] = self._providers[name](model=self.model_name)
            
        return self._instances[name]
