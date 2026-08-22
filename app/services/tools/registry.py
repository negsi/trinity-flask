"""
Tool Registry Module.

Provides tool management and bindings for stateful and stateless tools.
"""

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

from app.domain.image_generator import ImageGeneratorProvider
from app.services.infrastructure.email_service import EmailService
from app.services.infrastructure.file_storage_service import FileStorageService
from app.services.tools.api_tools import call_api, fetch_url
from app.services.tools.communication_tools import message_llm, send_email
from app.services.tools.file_tools import write_file, read_file
from app.services.tools.media_tools import generate_image
from app.services.tools.search_tools import web_search

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry providing decoupled tool execution bindings."""

    def __init__(
        self,
        file_storage_service: FileStorageService,
        email_service: EmailService | None = None,
        image_generator_provider: ImageGeneratorProvider | None = None,
        conversations_folder: str | Path | None = None,
    ) -> None:
        self.file_storage_service = file_storage_service
        self.email_service = email_service
        self.image_generator_provider = image_generator_provider
        self.conversations_folder = Path(conversations_folder) if conversations_folder else None
        self._custom_tools: dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        """Registers a custom callable tool."""
        self._custom_tools[name] = func

    def write_file(
        self,
        file_path: str,
        content: str,
        mode: str = "w",
        conversation_id: str | None = None,
        base_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> str:
        """Writes content to a sandboxed file."""
        return write_file(
            file_storage_service=self.file_storage_service,
            file_path=file_path,
            content=content,
            mode=mode,
            conversation_id=conversation_id,
            base_dir=base_dir or self.conversations_folder,
            **kwargs,
        )

    def read_file(
        self,
        file_path: str,
        conversation_id: str | None = None,
        base_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> str:
        """Reads content from a sandboxed file."""
        return read_file(
            file_storage_service=self.file_storage_service,
            file_path=file_path,
            conversation_id=conversation_id,
            base_dir=base_dir or self.conversations_folder,
            **kwargs,
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: list[str] | None = None,
        conversation_id: str | None = None,
        base_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> str:
        """Dispatches an email and resolves body-referenced local files."""

        # Remove email_service from kwargs if passed by agent/runner
        kwargs.pop("email_service", None)

        return send_email(
            email_service=self.email_service,
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html,
            attachments=attachments,
            conversation_id=conversation_id,
            base_dir=base_dir or self.conversations_folder,
            **kwargs,
        )

    def generate_image(
        self,
        prompt: str,
        filename: str | None = None,
        aspect_ratio: str = "1:1",
        conversation_id: str | None = None,
        base_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generates an image via provider and writes it to sandbox storage."""
        return generate_image(
            image_generator_provider=self.image_generator_provider,
            file_storage_service=self.file_storage_service,
            prompt=prompt,
            filename=filename,
            aspect_ratio=aspect_ratio,
            conversation_id=conversation_id,
            base_dir=base_dir or self.conversations_folder,
            **kwargs,
        )

    def get_tools(self) -> dict[str, Callable[..., Any]]:
        """Returns map of tool identifiers to callable functions."""
        base_tools: dict[str, Callable[..., Any]] = {
            "fetch_url": fetch_url,
            "web_search": web_search,
            "message_llm": message_llm,
            "call_api": call_api,
            "write_file": self.write_file,
            "read_file": self.read_file,
            "send_email": self.send_email,
            "generate_image": self.generate_image,
        }
        base_tools.update(self._custom_tools)
        return base_tools
