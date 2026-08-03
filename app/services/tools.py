"""
System Tools Registry Module.

Provides standard Python tool implementations for web fetching, RSS parsing, PDF reading,
and central tool registration.
"""

import io
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from pypdf import PdfReader


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
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower().split(";")[0].strip()
        url_lower = url.lower()
        raw_content = response.content

        is_feed_content_type = any(ft in content_type for ft in ["rss", "atom", "xml"]) and ("html" not in content_type)
        is_feed_extension = any(url_lower.endswith(ext) for ext in [".rss", ".xml", "/feed", "/rss", "mainfeed"])
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
                        clean_summary = BeautifulSoup(summary_raw, "html.parser").get_text(separator=" ", strip=True)
                        if len(clean_summary) > 300:
                            clean_summary = clean_summary[:300] + "..."
                    else:
                        clean_summary = "No description available."

                    published = entry.get("published", entry.get("updated", ""))
                    date_str = f" ({published})" if published else ""

                    entry_str = f"• {title}{date_str}\n  Link: {link}\n  Content: {clean_summary}"
                    feed_entries.append(entry_str)

                text_content = f"=== RSS / ATOM FEED: {feed.feed.get('title', url)} ===\n\n" + "\n\n".join(feed_entries)
            else:
                text_content = BeautifulSoup(raw_content, "html.parser").get_text(separator="\n", strip=True)

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
            
            for element in soup(["script", "style", "nav", "header", "footer", "noscript", "aside"]):
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

        print(f"[ToolExecutor] Fetched content from: {url}")
        return cleaned_text

    except Exception as e:
        print(f"[ToolExecutor] Error fetching URL {url}: {e}")
        return f"Error loading {url}: {e}"


def message_llm(message: str) -> str:
    """Placeholder tool for nested LLM message calls."""
    return "foo"


# Central Tool Registry dictionary mapping tool names to python callables
SYSTEM_TOOLS = {
    "fetch_url": fetch_url,
    "message_llm": message_llm
}
