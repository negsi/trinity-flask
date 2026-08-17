from abc import abstractmethod
from typing import Any, Protocol


class ImageGeneratorProvider(Protocol):
    """Abstract base class for multi-backend image generation providers."""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        **kwargs: Any,
    ) -> bytes:
        """
        Generates an image from a prompt and returns raw image bytes.
        
        Args:
            prompt (str): Detailed image description.
            aspect_ratio (str): Target aspect ratio (e.g., '1:1', '16:9', '9:16').
            
        Returns:
            bytes: Raw binary content of the generated image (e.g., PNG/JPEG).
        """
        pass
