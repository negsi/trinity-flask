"""
System Tools Registry Module.

Provides standard execution tools for web fetching, RSS feed parsing, PDF parsing,
file management, email dispatching, image generation, and a decoupled registry
for tool dependency injection.
"""

import io
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional

from bs4 import BeautifulSoup
import feedparser
from pypdf import PdfReader
import requests

from app.domain.errors import ToolExecutionError
from app.domain.image_generator import ImageGeneratorProvider
from app.services.email_service import EmailService
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


def fetch_url(url: str, **kwargs: Any) -> str:
    """
    Fetches and extracts clean textual content from a URL (supports HTML, RSS/Atom, JSON, and PDF).

    Args:
        url (str): Target resource URL.

    Returns:
        str: Extracted and cleaned textual content.
    """
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower().split(";")[0].strip()
        url_lower = url.lower()
        raw_content = response.content

        is_feed_content_type = any(
            ft in content_type for ft in ["rss", "atom", "xml"]
        ) and ("html" not in content_type)
        is_feed_extension = any(
            url_lower.endswith(ext) for ext in [".rss", ".xml", "/feed", "/rss", "mainfeed"]
        )
        has_xml_structure = b"<rss" in raw_content[:400].lower() or b"<feed" in raw_content[:400].lower()

        # 1. RSS / Atom Feeds
        if is_feed_content_type or is_feed_extension or has_xml_structure:
            feed = feedparser.parse(raw_content)
            if feed.entries:
                feed_entries = []
                for entry in feed.entries[:10]:
                    title = entry.get("title", "No title")
                    link = entry.get("link", "")
                    summary_raw = entry.get("summary", "") or entry.get("description", "")
                    if not summary_raw and "content" in entry and len(entry.content) > 0:
                        summary_raw = entry.content[0].get("value", "")

                    if summary_raw:
                        clean_summary = BeautifulSoup(summary_raw, "html.parser").get_text(
                            separator=" ", strip=True
                        )
                        if len(clean_summary) > 300:
                            clean_summary = clean_summary[:300] + "..."
                    else:
                        clean_summary = "No description available."

                    published = entry.get("published", entry.get("updated", ""))
                    date_str = f" ({published})" if published else ""
                    feed_entries.append(f"• {title}{date_str}\n  Link: {link}\n  Content: {clean_summary}")

                return f"=== RSS / ATOM FEED: {feed.feed.get('title', url)} ===\n\n" + "\n\n".join(feed_entries)

            return BeautifulSoup(raw_content, "html.parser").get_text(separator="\n", strip=True)

        # 2. JSON APIs
        if "json" in content_type or url_lower.endswith(".json"):
            try:
                json_data = response.json()
                return json.dumps(json_data, indent=2, ensure_ascii=False)
            except Exception:
                return response.text

        # 3. HTML Webpages
        if "html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "header", "footer", "noscript", "aside"]):
                element.decompose()
            return soup.get_text(separator="\n", strip=True)

        # 4. PDF Documents
        if content_type == "application/pdf" or url_lower.endswith(".pdf"):
            pdf_file = io.BytesIO(raw_content)
            reader = PdfReader(pdf_file)
            extracted_text = [
                page.extract_text() for page in reader.pages if page.extract_text()
            ]
            return "\n".join(extracted_text).strip()

        # 5. Plain Text
        if content_type.startswith("text/"):
            return response.text.strip()

        # 6. Fallback
        try:
            json_data = response.json()
            return json.dumps(json_data, indent=2, ensure_ascii=False)
        except Exception:
            return f"[Notice: Content format '{content_type}' from {url} is currently unsupported.]"

    except Exception as e:
        logger.error("Error fetching URL '%s': %s", url, e, exc_info=True)
        return f"Error loading {url}: {e}"


def message_llm(message: str, **kwargs: Any) -> str:
    """
    Placeholder skill implementation for nested LLM delegation.
    Actual sub-prompt streaming is handled by the execution engine.
    """
    return message


class ToolRegistry:
    """
    Registry providing decoupled tool execution bindings without global state dependencies.
    """

    def __init__(
        self,
        file_storage_service: FileStorageService,
        email_service: Optional[EmailService] = None,
        image_generator_provider: Optional[ImageGeneratorProvider] = None,
        conversations_folder: Optional[str] = None,
    ) -> None:
        self.file_storage_service = file_storage_service
        self.email_service = email_service
        self.image_generator_provider = image_generator_provider
        self.conversations_folder = conversations_folder
        self._custom_tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        """Registers a custom callable tool."""
        self._custom_tools[name] = func

    def write_file(
        self,
        file_path: str,
        content: str,
        mode: str = "w",
        conversation_id: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Writes content to a sandboxed file."""
        target_base = base_dir or self.conversations_folder
        try:
            res = self.file_storage_service.write_sandboxed_file(
                file_path=file_path,
                content=content,
                base_dir=target_base,
                sandbox_id=conversation_id,
                mode=mode,
            )
            return res
        except Exception as e:
            logger.error("Error executing write_file tool: %s", e, exc_info=True)
            return f"Error executing write_file: {e}"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        **kwargs: Any,
    ) -> str:
        """Dispatches an email using the injected EmailService."""
        if not self.email_service:
            error_msg = "EmailService is not configured in the tool registry."
            logger.error(error_msg)
            return f"Error: {error_msg}"
        try:
            return self.email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
            )
        except Exception as e:
            logger.error("Error executing send_email tool: %s", e, exc_info=True)
            return f"Error executing send_email: {e}"

    def generate_image(
        self,
        prompt: str,
        filename: Optional[str] = None,
        aspect_ratio: str = "1:1",
        conversation_id: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generates an image and returns file metadata for attachment handling."""
        if not self.image_generator_provider:
            raise ToolExecutionError("Image generation provider is not configured.")

        try:
            image_bytes = self.image_generator_provider.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

            safe_filename = filename or f"generated_{uuid.uuid4().hex[:8]}.png"
            if not safe_filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                safe_filename = f"{safe_filename}.png"

            target_base = base_dir or self.conversations_folder
            saved_path = self.file_storage_service.write_sandboxed_file(
                file_path=safe_filename,
                content=image_bytes,
                base_dir=target_base,
                sandbox_id=conversation_id,
            )

            res = {
                "status": "success",
                "filename": safe_filename,
                "file_path": saved_path,
                "mime_type": "image/png",
                "is_attachment": True
            }

            return res

        except Exception as e:
            logger.error("Error executing generate_image tool: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> Dict[str, Callable[..., Any]]:
        """Returns the dictionary mapping tool names to bound callable functions."""
        tools: Dict[str, Callable[..., Any]] = {
            "fetch_url": fetch_url,
            "message_llm": message_llm,
            "write_file": self.write_file,
            "send_email": self.send_email,
            "generate_image": self.generate_image,
        }
        tools.update(self._custom_tools)
        return tools
