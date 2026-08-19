"""
LLM and Image Generator Provider Implementations.

Integrates concrete LLM and image generation backend APIs (OpenAI and Google Gemini).
"""

import base64
from collections.abc import Generator
import logging
import os
from typing import Any

from app.domain.image_generator import ImageGeneratorProvider
from app.domain.llm import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completion API Provider implementation."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=os.getenv("LLM_API_KEY"))
        self.model = model

    def stream(self, messages: list[LLMMessage]) -> Generator[str, None, None]:
        """Streams chat completion tokens from OpenAI."""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GeminiProvider(LLMProvider):
    """Google Gemini GenAI SDK Provider implementation."""

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
        self.model = model

    def stream(self, messages: list[LLMMessage]) -> Generator[str, None, None]:
        """Streams content response chunks from Google Gemini."""
        from google.genai import types

        system_prompts = [m.content for m in messages if m.role == "system" and isinstance(m.content, str)]
        system_instruction = "\n\n---\n\n".join(system_prompts) if system_prompts else None

        contents: list[Any] = []
        for m in messages:
            if m.role == "system":
                continue

            if isinstance(m.content, list):
                for part in m.content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        contents.append(
                            types.Part.from_bytes(
                                data=part["data"],
                                mime_type=part["mime_type"],
                            )
                        )
                    else:
                        contents.append(part)
            else:
                contents.append(m.content)

        config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
        response = self.client.models.generate_content_stream(model=self.model, contents=contents, config=config)

        for chunk in response:
            if chunk.text:
                yield chunk.text


class GeminiImagenProvider(ImageGeneratorProvider):
    """Google Image Generation Provider using Gemini or Imagen models."""

    def __init__(self, model: str | None = None) -> None:
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
        self.model = model or os.getenv("IMAGE_GENERATOR_MODEL", "gemini-3.1-flash-image")

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

    def __init__(self, model: str = "dall-e-3") -> None:
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=os.getenv("LLM_API_KEY"))
        self.model = model

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
