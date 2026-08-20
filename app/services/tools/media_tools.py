"""
Media Tools Module.

Provides image generation and media processing capabilities.
"""

import logging
from pathlib import Path
from typing import Any
import uuid

from app.domain.errors import ToolExecutionError
from app.domain.image_generator import ImageGeneratorProvider
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


def generate_image(
    image_generator_provider: ImageGeneratorProvider | None,
    file_storage_service: FileStorageService,
    prompt: str,
    filename: str | None = None,
    aspect_ratio: str = "1:1",
    conversation_id: str | None = None,
    base_dir: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Generates an image via the provider and writes it to sandbox storage.

    Args:
        image_generator_provider: Image generation provider implementation.
        file_storage_service: Storage service instance.
        prompt: Image generation prompt description.
        filename: Optional desired output filename.
        aspect_ratio: Aspect ratio (e.g. '1:1', '16:9').
        conversation_id: Optional conversation sandbox ID.
        base_dir: Target base directory.

    Returns:
        dict[str, Any]: Result dictionary containing status, filename, and path or error.
    """
    if not image_generator_provider:
        raise ToolExecutionError("Image generation provider is not configured.")

    try:
        image_bytes = image_generator_provider.generate_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
        )

        safe_filename = filename or f"generated_{uuid.uuid4().hex[:8]}.png"
        if not safe_filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            safe_filename = f"{safe_filename}.png"

        target_base = str(base_dir) if base_dir else "."
        saved_path = file_storage_service.write_sandboxed_file(
            file_path=safe_filename,
            content=image_bytes,
            base_dir=target_base,
            sandbox_id=conversation_id,
        )

        return {
            "status": "success",
            "filename": safe_filename,
            "file_path": saved_path,
            "mime_type": "image/png",
            "is_attachment": True,
        }
    except Exception as exc:
        logger.error("Error executing generate_image tool: %s", exc, exc_info=True)
        return {"status": "error", "error": str(exc)}
