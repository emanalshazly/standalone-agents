"""
Tests for src/subagents/research_subagent.py — the ReAct-style loop's pure
parsing/termination logic, plus an end-to-end run with stub collaborators
(no real LLM, retrieval index, or network call).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.legal_index import RetrievedChunk
from src.subagents.research_subagent import (
    ResearchSubAgent,
    _parse_sufficiency_response,
    _should_stop,
)
from src.tools.web_search import WebSearchResult


# --- pure function tests -----------------------------------------------


def test_parse_sufficiency_response_valid_json():
    raw = '{"sufficient": true, "gap": "", "refined_query": null}'
    sufficient, gap, refined = _parse_sufficiency_response(raw)
    assert sufficient is True
    assert refined is None


def test_parse_sufficiency_response_insufficient_with_refinement():
    raw = '{"sufficient": false, "gap": "no article number found", "refined_query": "بحث أدق"}'
    sufficient, gap, refined = _parse_sufficiency_response(raw)
    assert sufficient is False
    assert gap == "no article number found"
    assert refined == "بحث أدق"


def test_parse_sufficiency_response_malformed_defaults_to_insufficient():
    sufficient, gap, refined = _parse_sufficiency_response("not json at all")
    assert sufficient is False
    assert "unparseable" in gap


def test_should_stop_when_sufficient_even_on_first_iteration():
    assert _should_stop(iteration_index=0, max_iterations=3, sufficient=True) is True


def test_should_stop_continues_while_budget_remains():
    assert _should_stop(iteration_index=0, max_iterations=3, sufficient=False) is False
    assert _should_stop(iteration_index=1, max_iterations=3, sufficient=False) is False


def test_should_stop_when_budget_exhausted_even_if_insufficient():
    assert _should_stop(iteration_index=2, max_iterations=3, sufficient=False) is True


# --- end-to-end loop test with stubs ------------------------------------


class _StubLegalIndex:
    def __init__(self, chunks_by_call):
        self._chunks_by_call = chunks_by_call
        self.calls = []

    def retrieve(self, query, **kwargs):
        self.calls.append(query)
        idx = min(len(self.calls) - 1, len(self._chunks_by_call) - 1)
        return self._chunks_by_call[idx]


class _StubSearchProvider:
    def search(self, query, max_results=5):
        return []


class _StubSufficientOnSecondTryLLM:
    """First call: insufficient with a refined query. Second call: sufficient."""

    def __init__(self):
        self.call_count = 0

    def invoke(self, messages):
        self.call_count += 1

        class _R:
            pass

        r = _R()
        if self.call_count == 1:
            r.content = '{"sufficient": false, "gap": "missing article", "refined_query": "استعلام أدق"}'
        else:
            r.content = '{"sufficient": true, "gap": "", "refined_query": null}'
        return r


def _chunk(entry_id="probation_period"):
    return RetrievedChunk(
        entry_id=entry_id,
        text="نص تجريبي",
        language="ar",
        law_name_ar="قانون العمل",
        law_name_en="Labor Law",
        article_number="104",
        article_number_confidence="single_source_only",
        source_urls=[],
        verified_by_lawyer=False,
        rerank_score=0.8,
    )


def test_research_loop_stops_early_once_sufficient():
    legal_index = _StubLegalIndex([[_chunk()], [_chunk()]])
    agent = ResearchSubAgent(
        legal_index=legal_index,
        search_provider=_StubSearchProvider(),
        llm=_StubSufficientOnSecondTryLLM(),
        max_iterations=5,
    )

    result = agent.run("هل يجوز تجديد فترة الاختبار؟")

    assert result.iteration_count == 2  # stopped after becoming sufficient, not at max_iterations=5
    assert result.sufficient is True
    assert legal_index.calls[1] == "استعلام أدق"  # second call used the refined query


class _StubNeverSufficientLLM:
    def invoke(self, messages):
        class _R:
            content = '{"sufficient": false, "gap": "still missing", "refined_query": "بحث آخر"}'

        return _R()


def test_research_loop_stops_at_max_iterations_when_never_sufficient():
    legal_index = _StubLegalIndex([[_chunk()]])
    agent = ResearchSubAgent(
        legal_index=legal_index,
        search_provider=_StubSearchProvider(),
        llm=_StubNeverSufficientLLM(),
        max_iterations=3,
    )

    result = agent.run("سؤال بدون إجابة كافية")

    assert result.iteration_count == 3
    assert result.sufficient is False
