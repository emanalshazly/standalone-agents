"""External tools available to sub-agents (currently: web search)."""

from src.tools.web_search import WebSearchResult, get_search_provider

__all__ = ["WebSearchResult", "get_search_provider"]
