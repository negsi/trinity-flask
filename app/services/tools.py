"""
System Tools Registry Module.

Provides standard Python tool implementations for web fetching, RSS parsing, PDF reading,
and central tool registration.
"""

import io
import json
import logging
import os
import pathlib
from typing import Any, Optional

from bs4 import BeautifulSoup
import feedparser
from flask import current_app
from pypdf import PdfReader
import requests

logger = logging.getLogger(__name__)


def fetch_url(url: str, **kwargs) -> str:
    """
    Fetches content from a URL, automatically handling HTML web pages, RSS/Atom feeds, JSON APIs, and PDF documents.

    Args:
        url (str): Target URL string.

    Returns:
        str: Cleaned text content extracted from the resource.
    """
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        response.raise_for_status()

        content_type = (
            response.headers.get("Content-Type", "").lower().split(";")[0].strip()
        )
        url_lower = url.lower()
        raw_content = response.content

        is_feed_content_type = any(
            ft in content_type for ft in ["rss", "atom", "xml"]
        ) and ("html" not in content_type)
        is_feed_extension = any(
            url_lower.endswith(ext)
            for ext in [".rss", ".xml", "/feed", "/rss", "mainfeed"]
        )
        has_xml_structure = (
            b"<rss" in raw_content[:400].lower()
            or b"<feed" in raw_content[:400].lower()
        )

        # 1. RSS / Atom Feeds
        if is_feed_content_type or is_feed_extension or has_xml_structure:
            feed = feedparser.parse(raw_content)

            if feed.entries:
                feed_entries = []
                for entry in feed.entries[:10]:
                    title = entry.get("title", "No title")
                    link = entry.get("link", "")

                    summary_raw = entry.get("summary", "") or entry.get(
                        "description", ""
                    )
                    if (
                        not summary_raw
                        and "content" in entry
                        and len(entry.content) > 0
                    ):
                        summary_raw = entry.content[0].get("value", "")

                    if summary_raw:
                        clean_summary = BeautifulSoup(
                            summary_raw, "html.parser"
                        ).get_text(separator=" ", strip=True)
                        if len(clean_summary) > 300:
                            clean_summary = clean_summary[:300] + "..."
                    else:
                        clean_summary = "No description available."

                    published = entry.get("published", entry.get("updated", ""))
                    date_str = f" ({published})" if published else ""

                    entry_str = f"• {title}{date_str}\n  Link: {link}\n  Content: {clean_summary}"
                    feed_entries.append(entry_str)

                text_content = (
                    f"=== RSS / ATOM FEED: {feed.feed.get('title', url)} ===\n\n"
                    + "\n\n".join(feed_entries)
                )
            else:
                text_content = BeautifulSoup(raw_content, "html.parser").get_text(
                    separator="\n", strip=True
                )

        # 2. JSON APIs
        elif "json" in content_type or url_lower.endswith(".json"):
            try:
                json_data = response.json()
                text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            except Exception:
                text_content = response.text

        # 3. HTML Webpages
        elif "html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")

            for element in soup(
                ["script", "style", "nav", "header", "footer", "noscript", "aside"]
            ):
                element.decompose()

            text_content = soup.get_text(separator="\n", strip=True)

        # 4. PDF Documents
        elif content_type == "application/pdf" or url_lower.endswith(".pdf"):
            pdf_file = io.BytesIO(raw_content)
            reader = PdfReader(pdf_file)

            extracted_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text.append(page_text)

            text_content = "\n".join(extracted_text)

        # 5. Plain Text
        elif content_type.startswith("text/"):
            text_content = response.text

        # 6. Fallback
        else:
            try:
                json_data = response.json()
                text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            except Exception:
                return f"[Notice: Content format '{content_type}' from {url} is currently unsupported.]"

        cleaned_text = text_content.strip()
        if not cleaned_text:
            return f"[Notice: No readable text could be extracted from {url}.]"

        logger.info("Fetched content from: %s", url)
        return cleaned_text

    except Exception as e:
        logger.error("Error fetching URL %s: %s", url, e, exc_info=True)
        return f"Error loading {url}: {e}"


def message_llm(message: str) -> str:
    """Placeholder tool for nested LLM message calls."""
    return "foo"


def write_file(
    file_path: str,
    content: str,
    mode: str = "w",
    conversation_id: str = None,
    base_dir: str = None,
) -> str:
    """
    Writes or appends text content to a specified file path.
    Automatically resolves relative paths into the active conversation workspace.

    Args:
        file_path (str): Relative or absolute target path for the file.
        content (str): The string content payload to write.
        mode (str, optional): File write mode. 'w' for overwrite/create, 'a' for append. Defaults to "w".
        conversation_id (str, optional): Active conversation UUID for directory isolation. Defaults to None.
        base_dir (str, optional): Root directory for conversation workspaces. Defaults to None.

    Returns:
        str: Status message indicating success or detailing an error.
    """
    try:
        path = pathlib.Path(file_path)

        if not base_dir:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            base_dir = os.path.join(project_root, "instance", "conversations")

        target_dir = (
            pathlib.Path(base_dir) / (conversation_id or "default")
        ).resolve()

        if not path.is_absolute():
            resolved_path = (target_dir / path).resolve()
        else:
            resolved_path = path.resolve()

        # Path Traversal Guard: ensure file target is inside designated sandbox
        if not resolved_path.is_relative_to(target_dir):
            error_msg = f"Security Error: Cannot write outside conversation sandbox directory '{target_dir}'."
            logger.error(error_msg)
            return error_msg

        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        if mode not in ["w", "a"]:
            return f"Error: Invalid mode '{mode}'. Use 'w' (overwrite) or 'a' (append)."

        with open(resolved_path, mode, encoding="utf-8") as f:
            f.write(content)

        action = "Appended to" if mode == "a" else "Successfully wrote to"
        size = len(content)
        logger.info("%s %s (%s characters)", action, resolved_path, size)
        return f"{action} file '{resolved_path.name}' at '{resolved_path}' ({size} characters written)."

    except Exception as e:
        logger.error("Error writing to file %s: %s", file_path, e, exc_info=True)
        return f"Error writing to file '{file_path}': {e}"


def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    email_service: Optional[Any] = None,
    **kwargs,
) -> str:
    """
    Sends an email using the injected EmailService or resolves it via Flask DI container.
    """
    try:
        service = email_service
        if service is None and current_app:
            container = getattr(current_app, "container", None)
            if container:
                service = container.email_service()

        if service is None:
            return "Error: EmailService dependency is not available."

        return service.send_email(
            to_email=to_email, subject=subject, body=body, is_html=is_html
        )
    except Exception as e:
        logger.error("Error executing send_email: %s", e, exc_info=True)
        return f"Error executing send_email tool: {e}"


# Central Tool Registry dictionary mapping tool names to python callables
SYSTEM_TOOLS = {
    "fetch_url": fetch_url,
    "message_llm": message_llm,
    "write_file": write_file,
    "send_email": send_email,
}
