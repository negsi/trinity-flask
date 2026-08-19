"""
LLM and Image Generator Provider Implementations.

Integrates concrete LLM and Image Generation backend APIs (OpenAI and Google Gemini).
"""

import base64
import os
from typing import Any, Generator, List, Optional   

from app.domain.image_generator import ImageGeneratorProvider
from app.domain.llm import LLMMessage, LLMProvider


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
        from google.genai import types

        system_prompts = [m.content for m in messages if m.role == "system" and isinstance(m.content, str)]
        system_instruction_text = "\n\n---\n\n".join(system_prompts) if system_prompts else None

        contents = []
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

        config = types.GenerateContentConfig(system_instruction=system_instruction_text) if system_instruction_text else None
        response = self.client.models.generate_content_stream(model=self.model, contents=contents, config=config)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text


class GeminiImagenProvider:
    """Google Image Generation Provider using Gemini or Imagen Models."""

    def __init__(self, model: Optional[str] = None):
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
        # Default fallback to Gemini flash image if not explicitly configured
        self.model = model or os.getenv("IMAGE_GENERATOR_MODEL", "gemini-3.1-flash-image")

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        **kwargs: Any,
    ) -> bytes:
        """Generates image bytes using Gemini's native or Imagen image generation models."""
        clean_model = self.model.replace("models/", "")

        # Branch 1: Dedicated Imagen 4 Models (using generate_images)
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

        # Branch 2: Gemini Multimodal Native Image Models (using generate_content)
        else:
            formatted_prompt = (
                f"Generate an image: {prompt}. "
                f"Aspect ratio: {aspect_ratio}."
            )

            response = self.client.models.generate_content(
                model=clean_model,
                contents=formatted_prompt,
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        if part.inline_data.mime_type.startswith("image/"):
                            return part.inline_data.data

        raise RuntimeError(f"No image binary received from model {clean_model}.")


class OpenAIDalleProvider(ImageGeneratorProvider):
    """OpenAI DALL-E 3 implementation."""

    def __init__(self, model: str = "dall-e-3"):
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
        size = "1024x1024"
        if aspect_ratio == "16:9":
            size = "1792x1024"
        elif aspect_ratio == "9:16":
            size = "1024x1792"

        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            response_format="b64_json",
            n=1,
        )
        b64_data = response.data[0].b64_json
        return base64.b64decode(b64_data)
