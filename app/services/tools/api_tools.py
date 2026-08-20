"""
API and Web Extraction Tools Module.

Provides tools for generic HTTP API requests and web/document content extraction
(HTML, RSS/Atom feeds, PDF, JSON, Plaintext).
"""

import io
import json
import logging
from typing import Any

from bs4 import BeautifulSoup
import feedparser
from pypdf import PdfReader
import requests

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
            "error": f"Invalid HTTP method '{method}'. Supported: {sorted(valid_methods)}",
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
