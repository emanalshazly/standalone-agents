"""
Tests for src/tools/web_search.py — provider selection and the
NullSearchProvider's safe-degradation behavior (no API key -> empty
results, never fabricated ones).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.web_search import (
    NullSearchProvider,
    TavilySearchProvider,
    get_search_provider,
)


def test_null_provider_returns_empty_list_not_fabricated_data():
    provider = NullSearchProvider()
    results = provider.search("أي استعلام")
    assert results == []


def test_get_search_provider_defaults_to_null_without_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    provider = get_search_provider()
    assert isinstance(provider, NullSearchProvider)


def test_get_search_provider_uses_tavily_when_key_present(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key-for-test")
    provider = get_search_provider()
    assert isinstance(provider, TavilySearchProvider)


def test_tavily_provider_handles_http_error_gracefully(monkeypatch):
    """A network failure must degrade to empty results, not raise and
    crash the research loop."""
    import httpx

    def _raise(*args, **kwargs):
        raise httpx.ConnectError("simulated network failure")

    monkeypatch.setattr(httpx, "post", _raise)

    provider = TavilySearchProvider(api_key="fake-key")
    results = provider.search("test query")
    assert results == []
