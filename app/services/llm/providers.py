"""
LLM Provider Implementations.

Integrates concrete LLM backend APIs (OpenAI and Google Gemini) supporting token streaming.
"""

import os
from typing import Generator, List
from app.domain.llm import LLMProvider, LLMMessage


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider implementation."""

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=os.getenv("LLM_API_KEY"))
        self.model = model

    def stream(self, messages: List[LLMMessage]) -> Generator[str, None, None]:
        """Streams chat completion tokens from OpenAI."""
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        response = self.client.chat.completions.create(
            model=self.model, messages=formatted_messages, stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GeminiProvider(LLMProvider):
    """Google Gemini GenAI SDK provider implementation."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
        self.model = model

    def stream(self, messages: List[LLMMessage]) -> Generator[str, None, None]:
        """Streams content tokens from Google Gemini using system instruction configs."""
        from google.genai import types

        system_prompts = [m.content for m in messages if m.role == "system"]
        system_instruction_text = (
            "\n\n---\n\n".join(system_prompts) if system_prompts else None
        )

        contents = [m.content for m in messages if m.role != "system"]

        config = (
            types.GenerateContentConfig(
                system_instruction=system_instruction_text
            )
            if system_instruction_text
            else None
        )

        response = self.client.models.generate_content_stream(
            model=self.model, contents=contents, config=config
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
