"""
LLM and Image Generator Provider Implementations.

Integrates concrete LLM and image generation backend APIs (OpenAI and Google Gemini).
"""

import base64
from collections.abc import Generator
import logging
import json
from typing import Any
from pathlib import Path

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
    """Google Gemini Provider using the official Interactions API for streaming thoughts and text."""

    def __init__(
        self,
        model: str | None = None,
        thinking_level: str | None = None,
    ) -> None:
        from google import genai  # type: ignore

        self.client = genai.Client(api_key=Config.LLM_API_KEY)
        self.model = model or Config.LLM_MODEL or "gemini-4-argon"
        
        config_level = getattr(Config, "LLM_THINKING_LEVEL", "medium")
        self.thinking_level = thinking_level or config_level

    def stream(self, messages: list[LLMMessage]) -> Generator[Any, None, None]:
        """Streams thoughts and text tokens using client.interactions.create with streaming enabled."""
        from google.genai import types  # type: ignore

        # 1. Extract system instruction if present
        system_prompts = [
            m.content for m in messages if m.role == "system" and isinstance(m.content, str)
        ]
        system_instruction = "\n\n---\n\n".join(system_prompts) if system_prompts else None

        # 2. Build input payload supporting text and uploaded image files for the Interactions API
        final_input: Any = ""
        latest_message = messages[-1] if messages else None
        
        if latest_message and isinstance(latest_message.content, list):
            input_parts = []
            for item in latest_message.content:
                if isinstance(item, str):
                    input_parts.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    if "file_path" in item and item["file_path"] and Path(item["file_path"]).is_file():
                        # Upload image file to Gemini Files API as required by Interactions API
                        uploaded_file = self.client.files.upload(file=item["file_path"])
                        input_parts.append({
                            "type": "image",
                            "uri": uploaded_file.uri,
                            "mime_type": item.get("mime_type", "image/png"),
                            "resolution": "high",
                        })
                    elif "text" in item:
                        input_parts.append({"type": "text", "text": item["text"]})
            final_input = input_parts
        else:
            prompt_parts = []
            for m in messages:
                if m.role == "system":
                    continue
                role_prefix = "User: " if m.role == "user" else ("Assistant: " if m.role == "model" else "System: ")
                if isinstance(m.content, str):
                    prompt_parts.append(f"{role_prefix}{m.content}")
            final_input = "\n".join(prompt_parts)

        # 3. Prepare generation configuration with thinking enabled
        generation_config: dict[str, Any] = {
            "thinking_level": self.thinking_level,
            "thinking_summaries": "auto",
        }

        call_kwargs: dict[str, Any] = {
            "model": self.model,
            "input": final_input,
            "generation_config": generation_config,
            "stream": True,
        }

        if system_instruction:
            call_kwargs["system_instruction"] = system_instruction

        # 4. Invoke Interactions API stream
        stream = self.client.interactions.create(**call_kwargs)

        # 5. Process event stream conforming to Interactions API specs
        for event in stream:
            event_type = getattr(event, "event_type", None)
            
            if event_type == "step.delta":
                delta = getattr(event, "delta", None)
                if not delta:
                    continue
                
                delta_type = getattr(delta, "type", None)
                
                if delta_type == "thought_summary":
                    content_obj = getattr(delta, "content", None)
                    thought_text = getattr(content_obj, "text", "") if content_obj else ""
                    if thought_text:
                        yield f"{PROTOCOL_THOUGHT}{json.dumps({'content': thought_text})}"
                
                elif delta_type == "text":
                    text_content = getattr(delta, "text", "")
                    if text_content:
                        yield text_content


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


class MistralProvider(LLMProvider):
    """Mistral AI Provider using the Chat Completions API for streaming thoughts and text."""

    def __init__(
        self,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        from mistralai.client import Mistral  # type: ignore

        self.client = Mistral(api_key=Config.LLM_API_KEY)
        self.model = model or Config.LLM_MODEL or "mistral-large-latest"

        config_level = getattr(Config, "LLM_THINKING_LEVEL", "high")
        self.reasoning_effort = reasoning_effort or config_level

    def _build_message_payload(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Converts LLMMessage history into the Mistral chat payload, including image attachments."""
        payload: list[dict[str, Any]] = []
        for m in messages:
            if isinstance(m.content, str):
                payload.append({"role": m.role, "content": m.content})
                continue

            content_parts: list[dict[str, Any]] = []
            for item in m.content:
                if isinstance(item, str):
                    content_parts.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    if item.get("file_path") and Path(item["file_path"]).is_file():
                        with open(item["file_path"], "rb") as image_file:
                            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                        content_parts.append({
                            "type": "image_url",
                            "image_url": f"data:{item.get('mime_type', 'image/png')};base64,{encoded_image}",
                        })
                    elif item.get("text"):
                        content_parts.append({"type": "text", "text": item["text"]})
            if content_parts:
                payload.append({"role": m.role, "content": content_parts})
        return payload

    def stream(self, messages: list[LLMMessage]) -> Generator[Any, None, None]:
        """Streams thoughts and text tokens using client.chat.stream with reasoning_effort enabled."""
        from mistralai.client.models import TextChunk, ThinkChunk  # type: ignore

        call_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._build_message_payload(messages),
        }

        if self.reasoning_effort:
            call_kwargs["reasoning_effort"] = self.reasoning_effort

        # Mistral streams delta.content in three shapes: a list with ThinkChunk(s) during the
        # thinking phase, a mixed list with the closing ThinkChunk and first TextChunk, and a
        # plain string for the remaining answer tokens.
        for event in self.client.chat.stream(**call_kwargs):
            data = getattr(event, "data", event)
            if not getattr(data, "choices", None):
                continue

            delta = data.choices[0].delta
            delta_content = getattr(delta, "content", None)
            if not delta_content:
                continue

            if isinstance(delta_content, str):
                yield delta_content
                continue

            for chunk in delta_content:
                if isinstance(chunk, ThinkChunk):
                    for inner in getattr(chunk, "thinking", None) or []:
                        inner_text = inner if isinstance(inner, str) else getattr(inner, "text", "")
                        if inner_text:
                            yield f"{PROTOCOL_THOUGHT}{json.dumps({'content': inner_text})}"
                elif isinstance(chunk, TextChunk) and chunk.text:
                    yield chunk.text
                elif isinstance(chunk, str) and chunk:
                    yield chunk