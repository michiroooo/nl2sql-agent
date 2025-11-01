"""Web search and information retrieval tools for AG2 agents."""

from __future__ import annotations

from typing import Callable

import httpx


def create_web_tools() -> dict[str, Callable]:
    """Create web search and scraping tools.

    Returns:
        Dictionary mapping tool names to callable functions.
    """

    def web_search(query: str) -> str:
        """Search web using DuckDuckGo API.

        Args:
            query: Search query string.

        Returns:
            Formatted search results with titles, snippets, and URLs.
        """
        try:
            response = httpx.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
                timeout=10.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()

            results = []

            if data.get("AbstractText"):
                results.append(f"Summary: {data['AbstractText']}\n")

            related_topics = data.get("RelatedTopics", [])[:5]

            if related_topics:
                results.append("Related Results:")
                for i, topic in enumerate(related_topics, 1):
                    if isinstance(topic, dict) and "Text" in topic:
                        title = topic["Text"][:100]
                        url = topic.get("FirstURL", "")
                        results.append(f"{i}. {title}")
                        if url:
                            results.append(f"   URL: {url}")

            if not results:
                return f"No results found for query: {query}"

            return "\n".join(results)

        except Exception as e:
            return f"Web search failed: {e!s}"

    def scrape_webpage(url: str) -> str:
        """Scrape text content from a webpage.

        Args:
            url: URL of the webpage to scrape.

        Returns:
            Text content of the webpage (first 2000 characters).
        """
        try:
            response = httpx.get(
                url,
                timeout=10.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AG2Bot/1.0)"},
            )
            response.raise_for_status()

            text = response.text

            from html import unescape
            import re

            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = unescape(text)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) > 2000:
                text = text[:2000] + "..."

            return text

        except Exception as e:
            return f"Failed to scrape webpage: {e!s}"

    return {
        "web_search": web_search,
        "scrape_webpage": scrape_webpage,
    }
