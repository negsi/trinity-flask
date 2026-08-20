"""
System Tools Registry Module.

Provides standard execution tools for web fetching, RSS feed parsing, PDF parsing,
file management, email dispatching, and image generation.
"""

from collections.abc import Callable
import io
import json
import logging
import os
from pathlib import Path
import re
from typing import Any
import uuid

from bs4 import BeautifulSoup
from ddgs import DDGS
import feedparser
from pypdf import PdfReader
import requests
from tavily import TavilyClient

from app.domain.errors import ToolExecutionError
from app.domain.image_generator import ImageGeneratorProvider
from app.services.email_service import EmailService
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


def call_api(
    url: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    **kwargs: Any,
) -> str:
    """
    Performs an HTTP API request (GET, POST, PUT, PATCH, DELETE) to a target URL.

    Args:
        url: Complete target URL.
        method: HTTP method. Defaults to 'GET'.
        params: URL query string parameters.
        json_data: JSON payload for write requests.
        headers: Custom HTTP headers.
        timeout: Timeout in seconds.

    Returns:
        str: JSON string containing 'status_code', 'success', and 'data' or 'error'.
    """
    method_upper = method.upper()
    valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    if method_upper not in valid_methods:
        return json.dumps({
            "success": False,
            "error": f"Invalid HTTP method '{method}'. Supported: {sorted(valid_methods)}"
        })

    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        request_headers.update(headers)

    try:
        logger.info("Executing API Call: %s %s", method_upper, url)
        response = requests.request(
            method=method_upper,
            url=url,
            params=params,
            json=json_data,
            headers=request_headers,
            timeout=timeout,
        )

        try:
            res_payload = response.json()
        except ValueError:
            res_payload = response.text

        is_success = 200 <= response.status_code < 300
        result = {
            "success": is_success,
            "status_code": response.status_code,
            "data" if is_success else "error": res_payload,
        }
        return json.dumps(result, ensure_ascii=False)
    except requests.exceptions.Timeout:
        logger.error("API Call timed out: %s %s", method_upper, url)
        return json.dumps({"success": False, "error": f"Request timed out after {timeout} seconds."})
    except requests.exceptions.RequestException as exc:
        logger.error("API Call failed: %s %s: %s", method_upper, url, exc)
        return json.dumps({"success": False, "error": f"HTTP Request failed: {exc}"})


def fetch_url(url: str, **kwargs: Any) -> str:
    """
    Fetches and extracts clean textual content from a URL (HTML, RSS/Atom, JSON, PDF).

    Args:
        url: Target resource URL.

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

        # 1. Feeds
        is_feed_type = any(ft in content_type for ft in ["rss", "atom", "xml"]) and ("html" not in content_type)
        is_feed_ext = any(url_lower.endswith(ext) for ext in [".rss", ".xml", "/feed", "/rss", "mainfeed"])
        has_xml_struct = b"<rss" in raw_content[:400].lower() or b"<feed" in raw_content[:400].lower()

        if is_feed_type or is_feed_ext or has_xml_struct:
            feed = feedparser.parse(raw_content)
            if feed.entries:
                feed_entries: list[str] = []
                for entry in feed.entries[:10]:
                    title = entry.get("title", "No title")
                    link = entry.get("link", "")
                    summary_raw = entry.get("summary", "") or entry.get("description", "")
                    if not summary_raw and "content" in entry and len(entry.content) > 0:
                        summary_raw = entry.content[0].get("value", "")

                    clean_summary = (
                        BeautifulSoup(summary_raw, "html.parser").get_text(separator=" ", strip=True)
                        if summary_raw else "No description available."
                    )
                    if len(clean_summary) > 300:
                        clean_summary = f"{clean_summary[:300]}..."

                    published = entry.get("published", entry.get("updated", ""))
                    date_str = f" ({published})" if published else ""
                    feed_entries.append(f"• {title}{date_str}\n  Link: {link}\n  Content: {clean_summary}")

                return f"=== RSS / ATOM FEED: {feed.feed.get('title', url)} ===\n\n" + "\n\n".join(feed_entries)

            return BeautifulSoup(raw_content, "html.parser").get_text(separator="\n", strip=True)

        # 2. JSON
        if "json" in content_type or url_lower.endswith(".json"):
            try:
                return json.dumps(response.json(), indent=2, ensure_ascii=False)
            except Exception:
                return response.text

        # 3. HTML
        if "html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "header", "footer", "noscript", "aside"]):
                element.decompose()
            return soup.get_text(separator="\n", strip=True)

        # 4. PDF
        if content_type == "application/pdf" or url_lower.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(raw_content))
            extracted_text = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n".join(extracted_text).strip()

        # 5. Plaintext
        if content_type.startswith("text/"):
            return response.text.strip()

        # 6. Fallback
        return response.text

    except Exception as exc:
        logger.error("Error fetching URL '%s': %s", url, exc, exc_info=True)
        return f"Error loading {url}: {exc}"


def message_llm(message: str, **kwargs: Any) -> str:
    """Placeholder tool signature for sub-task delegation."""
    return message


def web_search(query: str, max_results: int = 5, **kwargs: Any) -> list[dict[str, Any]] | str:
    """
    Hybrid Web Search Tool using Tavily or DuckDuckGo.

    Args:
        query: Keywords or question.
        max_results: Max hits to return.

    Returns:
        list[dict[str, Any]] | str: Formatted search result list or error string.
    """
    if tavily_api_key := os.getenv("TAVILY_API_KEY"):
        try:
            client = TavilyClient(api_key=tavily_api_key)
            response = client.search(query=query, max_results=max_results, search_depth="basic")
            results = [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content"),
                    "source_provider": "tavily",
                }
                for item in response.get("results", [])
            ]
            if results:
                return results
        except Exception as exc:
            logger.warning("[web_search] Tavily failed (%s). Falling back to DuckDuckGo...", exc)

    try:
        with DDGS() as ddgs:
            return [
                {
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                    "source_provider": "duckduckgo",
                }
                for item in ddgs.text(query, region="de-de", max_results=max_results)
            ]
    except Exception as exc:
        logger.error("[web_search] DuckDuckGo failed: %s", exc, exc_info=True)
        return f"Error executing web search: {exc}"


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
        self.conversations_folder = str(conversations_folder) if conversations_folder else None
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
        base_dir: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Writes content to a sandboxed file."""
        target_base = base_dir or self.conversations_folder or "."
        try:
            return self.file_storage_service.write_sandboxed_file(
                file_path=file_path,
                content=content,
                base_dir=target_base,
                sandbox_id=conversation_id,
                mode=mode,
            )
        except Exception as exc:
            logger.error("Error executing write_file tool: %s", exc, exc_info=True)
            return f"Error executing write_file: {exc}"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: list[str] | None = None,
        conversation_id: str | None = None,
        base_dir: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Dispatches an email and resolves body-referenced local files."""
        if not self.email_service:
            return "Error: EmailService is not configured in the tool registry."

        resolved_attachments = list(attachments or [])
        target_base = Path(base_dir or self.conversations_folder or ".").resolve()

        # 1. Resolve explicit attachments
        final_attachments: list[str] = []
        for att in resolved_attachments:
            if found := self._locate_file(att, target_base, conversation_id):
                final_attachments.append(str(found))
            else:
                logger.warning("Specified email attachment not found: %s", att)

        # 2. Extract referenced attachments from body
        file_refs = re.findall(r"([a-zA-Z0-9_\-]+\.(?:png|jpg|jpeg|webp|pdf|txt|csv))", body, re.IGNORECASE)
        processed_body = body

        for raw_ref in set(file_refs):
            if found := self._locate_file(raw_ref, target_base, conversation_id):
                path_str = str(found)
                if path_str not in final_attachments:
                    final_attachments.append(path_str)

                md_pattern = rf"!\[.*?\]\([^)]*{re.escape(found.name)}[^)]*\)"
                processed_body = re.sub(md_pattern, "", processed_body)
                html_pattern = rf'<img\s+[^>]*src=["\'][^"\']*{re.escape(found.name)}["\'][^>]*>'
                processed_body = re.sub(html_pattern, "", processed_body, flags=re.IGNORECASE)

        # 3. Fallback: Latest image
        if not final_attachments and target_base.is_dir():
            latest_img = self._get_latest_image_in_dir(target_base)
            if latest_img:
                final_attachments.append(str(latest_img))

        try:
            return self.email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=processed_body,
                is_html=is_html,
                attachments=final_attachments,
            )
        except Exception as exc:
            logger.error("Error executing send_email: %s", exc, exc_info=True)
            return f"Error executing send_email: {exc}"

    def generate_image(
        self,
        prompt: str,
        filename: str | None = None,
        aspect_ratio: str = "1:1",
        conversation_id: str | None = None,
        base_dir: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generates an image via provider and writes it to sandbox storage."""
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

            target_base = base_dir or self.conversations_folder or "."
            saved_path = self.file_storage_service.write_sandboxed_file(
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

    def get_tools(self) -> dict[str, Callable[..., Any]]:
        """Returns map of tool identifiers to callable functions."""
        base_tools: dict[str, Callable[..., Any]] = {
            "fetch_url": fetch_url,
            "web_search": web_search,
            "message_llm": message_llm,
            "call_api": call_api,
            "write_file": self.write_file,
            "send_email": self.send_email,
            "generate_image": self.generate_image,
        }
        base_tools.update(self._custom_tools)
        return base_tools

    @staticmethod
    def _locate_file(filename: str, target_base: Path, conversation_id: str | None) -> Path | None:
        """Helper to locate a named file across conversation sandboxes."""
        clean_name = Path(filename).name
        candidates = [
            target_base / clean_name,
            Path(filename),
        ]
        if conversation_id:
            candidates.insert(0, target_base / conversation_id / clean_name)

        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()

        if target_base.is_dir():
            for found_file in target_base.rglob(clean_name):
                if found_file.is_file():
                    return found_file.resolve()

        return None

    @staticmethod
    def _get_latest_image_in_dir(directory: Path) -> Path | None:
        """Finds the most recently modified image file in a directory tree."""
        valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
        image_files = [f for f in directory.rglob("*") if f.is_file() and f.suffix.lower() in valid_exts]
        if not image_files:
            return None
        return max(image_files, key=lambda f: f.stat().st_mtime)
