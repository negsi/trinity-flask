"""
System Tools Registry Module.

Provides standard execution tools for web fetching, RSS feed parsing, PDF parsing,
file management, email dispatching, image generation, and a decoupled registry
for tool dependency injection.
"""

import io
import json
import logging
import os
import re
import uuid
from typing import Any, Callable, Dict, Optional

from bs4 import BeautifulSoup
import feedparser
from pypdf import PdfReader
import requests

from ddgs import DDGS
from tavily import TavilyClient

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


def web_search(query: str, max_results: int = 5, **kwargs: Any) -> Any:
    """
    Hybrid Web Search Tool:
    Uses Tavily if TAVILY_API_KEY is present in environment variables.
    Falls back seamlessly to DuckDuckGo (ddgs) otherwise.

    Args:
        query (str): Search query or keywords.
        max_results (int): Maximum number of search results to return.

    Returns:
        list[dict] or str: Search results containing title, url, and snippet.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if tavily_api_key:
        try:
            client = TavilyClient(api_key=tavily_api_key)
            response = client.search(query=query, max_results=max_results, search_depth="basic")
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content"),
                    "source_provider": "tavily"
                })
            if results:
                return results
        except Exception as e:
            logger.warning("[web_search] Tavily request failed (%s). Falling back to DuckDuckGo...", e)

    try:
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, region="de-de", max_results=max_results))
            results = []
            for item in ddg_results:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                    "source_provider": "duckduckgo"
                })
            return results
    except Exception as e:
        logger.error("[web_search] DuckDuckGo search failed: %s", e, exc_info=True)
        return f"Error executing web search: {e}"
        

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
        attachments: Optional[list] = None,
        conversation_id: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Dispatches an email using the injected EmailService, auto-resolving local files as email attachments."""
        if not self.email_service:
            error_msg = "EmailService is not configured in the tool registry."
            logger.error(error_msg)
            return f"Error: {error_msg}"

        resolved_attachments = list(attachments) if attachments else []
        target_base = base_dir or self.conversations_folder or os.getcwd()

        def locate_file(filename: str) -> Optional[str]:
            """Searches for a filename in potential target directories."""
            clean_name = os.path.basename(filename)
            
            # Direct checks
            direct_candidates = [
                filename,
                clean_name,
                os.path.join(target_base, clean_name),
            ]
            if conversation_id and target_base:
                direct_candidates.insert(0, os.path.join(target_base, conversation_id, clean_name))

            for path in direct_candidates:
                if os.path.exists(path) and os.path.isfile(path):
                    return path

            # Recursive search in target_base as fallback
            if target_base and os.path.exists(target_base):
                for root, _, files in os.walk(target_base):
                    if clean_name in files:
                        return os.path.join(root, clean_name)

            return None

        # 1. Resolve explicit attachments passed in arguments
        final_attachments = []
        for att in resolved_attachments:
            found = locate_file(att)
            if found:
                final_attachments.append(found)
            else:
                logger.warning("Specified attachment not found: %s", att)

        # 2. Extract image/file references mentioned in the email body
        file_references = re.findall(r'([a-zA-Z0-9_\-]+\.(?:png|jpg|jpeg|webp|pdf|txt|csv))', body, re.IGNORECASE)
        processed_body = body

        for raw_ref in set(file_references):
            found_path = locate_file(raw_ref)
            if found_path:
                if found_path not in final_attachments:
                    final_attachments.append(found_path)
                    logger.info("Auto-resolved email attachment from body match: %s", found_path)

                # Clean up broken Markdown/HTML image snippets from body
                md_pattern = rf'!\[.*?\]\([^)]*{re.escape(os.path.basename(raw_ref))}[^)]*\)'
                processed_body = re.sub(md_pattern, '', processed_body)
                html_pattern = rf'<img\s+[^>]*src=["\'][^"\']*{re.escape(os.path.basename(raw_ref))}["\'][^>]*>'
                processed_body = re.sub(html_pattern, '', processed_body, flags=re.IGNORECASE)

        # 3. Last Resort Fallback: If still no attachments, pick the latest generated image in target_base
        if not final_attachments and target_base and os.path.exists(target_base):
            found_images = []
            for root, _, files in os.walk(target_base):
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        fp = os.path.join(root, f)
                        found_images.append((fp, os.path.getmtime(fp)))

            if found_images:
                # Pick the most recently created image
                found_images.sort(key=lambda x: x[1], reverse=True)
                latest_image = found_images[0][0]
                final_attachments.append(latest_image)
                logger.info("Fallback: Auto-attached most recent image: %s", latest_image)

        try:
            return self.email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=processed_body,
                is_html=is_html,
                attachments=final_attachments,
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
                "is_attachment": True,
            }

            return res

        except Exception as e:
            logger.error("Error executing generate_image tool: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> Dict[str, Callable[..., Any]]:
        """Returns the dictionary mapping tool names to bound callable functions."""
        tools: Dict[str, Callable[..., Any]] = {
            "fetch_url": fetch_url,
            "web_search": web_search,
            "message_llm": message_llm,
            "write_file": self.write_file,
            "send_email": self.send_email,
            "generate_image": self.generate_image,
        }
        tools.update(self._custom_tools)
        return tools
