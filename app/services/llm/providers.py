"""
LLM and Image Generator Provider Implementations.

Integrates concrete LLM and image generation backend APIs (OpenAI and Google Gemini).
"""

import base64
from collections.abc import Generator
import logging
import json
from typing import Any

from app.config import BaseConfig as Config
from app.domain.image_generator import ImageGeneratorProvider
from app.domain.llm import LLMMessage, LLMProvider
from app.services.agent.constants import PROTOCOL_THOUGHT

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completion API Provider implementation."""

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=Config.LLM_API_KEY)
        self.model = model or Config.LLM_MODEL or "gpt-4o-mini"

    def stream(self, messages: list[LLMMessage]) -> Generator[Any, None, None]:
        """Streams chat completion tokens from OpenAI."""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            stream=True,
        )
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield (True, reasoning)
            elif delta.content:
                yield (False, delta.content)


class GeminiProvider(LLMProvider):
    """Google Gemini Provider streaming thoughts and text using standard generate_content_stream."""

    def __init__(
        self,
        model: str | None = None,
        thinking_budget: int | None = None,
    ) -> None:
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=Config.LLM_API_KEY)
        self.model = model or Config.LLM_MODEL or "gemini-3.7-flash"
        self.thinking_budget = (
            thinking_budget if thinking_budget is not None else Config.LLM_THINKING_BUDGET
        )

    def stream(self, messages: list[LLMMessage]) -> Generator[Any, None, None]:
        """Streams thoughts and text tokens directly via standard GenAI SDK."""
        # Always comment source code in English
        from google.genai import types  # type: ignore

        # 1. Extract system instruction
        system_prompts = [
            m.content for m in messages if m.role == "system" and isinstance(m.content, str)
        ]
        system_instruction = "\n\n---\n\n".join(system_prompts) if system_prompts else None

        # 2. Format contents list for generate_content_stream
        contents = []
        for m in messages:
            if m.role == "system":
                continue

            role = "user" if m.role == "user" else "model"

            if isinstance(m.content, list):
                parts = []
                for part in m.content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        parts.append({
                            "inline_data": {
                                "data": part["data"],
                                "mime_type": part["mime_type"],
                            }
                        })
                    else:
                        parts.append({"text": str(part)})
                contents.append({"role": role, "parts": parts})
            else:
                contents.append({"role": role, "parts": [{"text": str(m.content)}]})

        # 3. Build thinking_config safely
        thinking_kwargs: dict[str, Any] = {"include_thoughts": True}
        if self.thinking_budget is not None and self.thinking_budget > 0:
            thinking_kwargs["thinking_budget"] = self.thinking_budget

        config_kwargs: dict[str, Any] = {
            "thinking_config": types.ThinkingConfig(**thinking_kwargs)
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs)

        # 4. Invoke generate_content_stream
        response_stream = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        )

        # 5. Extract incremental thoughts and response text
        for chunk in response_stream:
            if not chunk.candidates:
                continue

            candidate = chunk.candidates[0]
            if not candidate.content or not candidate.content.parts:
                continue

            for part in candidate.content.parts:
                if not part.text:
                    continue

                is_thought = getattr(part, "thought", False)

                if is_thought:
                    yield f"{PROTOCOL_THOUGHT}{json.dumps({'content': part.text})}"
                else:
                    yield part.text


class GeminiImagenProvider(ImageGeneratorProvider):
    """Google Image Generation Provider using Gemini or Imagen models."""

    def __init__(self, model: str | None = None) -> None:
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=Config.LLM_API_KEY)
        self.model = model or Config.IMAGE_GENERATOR_MODEL or "gemini-3.1-flash-image"

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        **kwargs: Any,
    ) -> bytes:
        """Generates image bytes using Imagen 4 or Gemini Multimodal endpoints."""
        clean_model = self.model.replace("models/", "")

        if "imagen" in clean_model.lower():
            response = self.client.models.generate_images(
                model=clean_model,
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    output_mime_type="image/png",
                ),
            )
            if response.generated_images:
                return response.generated_images[0].image.image_bytes
        else:
            formatted_prompt = f"Generate an image: {prompt}. Aspect ratio: {aspect_ratio}."
            response = self.client.models.generate_content(
                model=clean_model,
                contents=formatted_prompt,
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        if part.inline_data.mime_type.startswith("image/"):
                            return part.inline_data.data

        raise RuntimeError(f"No image binary returned from Gemini/Imagen model '{clean_model}'.")


class OpenAIDalleProvider(ImageGeneratorProvider):
    """OpenAI DALL-E 3 Image Generation Provider."""

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=Config.LLM_API_KEY)
        self.model = model or "dall-e-3"

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        **kwargs: Any,
    ) -> bytes:
        """Generates image bytes using OpenAI DALL-E 3."""
        size_map = {
            "16:9": "1792x1024",
            "9:16": "1024x1792",
        }
        target_size = size_map.get(aspect_ratio, "1024x1024")

        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=target_size,
            response_format="b64_json",
            n=1,
        )
        b64_data = response.data[0].b64_json
        return base64.b64decode(b64_data)