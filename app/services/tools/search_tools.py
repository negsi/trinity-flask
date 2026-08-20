"""
Search Tools Module.

Provides web search capabilities using Tavily API with DuckDuckGo fallback.
"""

import logging
import os
from typing import Any

from ddgs import DDGS
from tavily import TavilyClient

logger = logging.getLogger(__name__)


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
