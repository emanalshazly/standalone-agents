"""
Web Search Tool - أداة البحث على الإنترنت

Used only by the case-assistant / drafting track (src/subagents/,
src/graph/case_drafting_graph.py), NOT by the plain-language legal-literacy
agent (src/agents/legal/), which deliberately stays scoped to the local,
partially-lawyer-reviewable knowledge base.

Trust tiering matters here as much as the search call itself: a web result
is, by construction, LESS trustworthy than even the unverified local seed
corpus (which at least has a named law and a specific secondary source
consulted by a human researcher). Every result from this module is tagged
`trust_tier="web_unverified"` so downstream consumers (evidence review,
drafting, citation_verifier) can weight it accordingly and never present it
with the same confidence as a lawyer-verified chunk.

No API key configured -> NullSearchProvider, which returns an empty result
list and logs a warning. It does NOT fabricate results or silently fall
back to the LLM's own (unsearched, unverifiable) knowledge — that would
reintroduce exactly the hallucination risk this project's architecture
exists to prevent.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

TRUST_TIER_WEB_UNVERIFIED = "web_unverified"


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str
    trust_tier: str = TRUST_TIER_WEB_UNVERIFIED


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]: ...


class NullSearchProvider:
    """Used when no search API key is configured. Returns nothing rather
    than fabricating or silently degrading to ungrounded LLM knowledge."""

    def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        logger.warning(
            "No web search provider configured (set TAVILY_API_KEY) — "
            "returning zero web results for query: %r. The research "
            "sub-agent will proceed with local knowledge base results only.",
            query,
        )
        return []


class TavilySearchProvider:
    """Real web search via Tavily's REST API (https://tavily.com), called
    directly with httpx rather than pulling in a dedicated SDK dependency."""

    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float = 15.0):
        self._api_key = api_key
        self._timeout = timeout

    def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        try:
            response = httpx.post(
                self.API_URL,
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error("Tavily search failed for query %r: %s", query, exc)
            return []

        results = []
        for item in data.get("results", [])[:max_results]:
            results.append(
                WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                )
            )
        return results


def get_search_provider() -> SearchProvider:
    """Factory: real Tavily provider if TAVILY_API_KEY is set, else Null."""
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        return TavilySearchProvider(api_key=api_key)
    return NullSearchProvider()
