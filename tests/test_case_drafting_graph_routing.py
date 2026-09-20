"""
Tests for the pure conditional-edge routing functions in
src/graph/case_drafting_graph.py — same style as
tests/test_graph_routing.py for the literacy-agent graph.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.case_drafting_graph import (
    _route_after_classify,
    _route_after_drafting,
    _route_after_research,
)
from src.rag.legal_index import RetrievedChunk
from src.subagents.drafting_subagent import DraftingResult
from src.subagents.research_subagent import ResearchIteration, ResearchResult


def test_route_after_classify_in_scope():
    assert _route_after_classify({"in_scope": True}) == "research"


def test_route_after_classify_out_of_scope():
    assert _route_after_classify({"in_scope": False}) == "handoff"


def _chunk():
    return RetrievedChunk(
        entry_id="e",
        text="t",
        language="ar",
        law_name_ar="l",
        law_name_en="l",
        article_number="1",
        article_number_confidence="single_source_only",
        source_urls=[],
        verified_by_lawyer=False,
        rerank_score=0.5,
    )


def test_route_after_research_handoffs_when_nothing_found():
    empty_research = ResearchResult(
        original_query="q",
        iterations=[ResearchIteration(query="q", local_chunks=[], web_results=[], sufficient=False, gap="none")],
    )
    assert _route_after_research({"research": empty_research}) == "handoff"


def test_route_after_research_continues_when_local_chunks_found():
    research = ResearchResult(
        original_query="q",
        iterations=[ResearchIteration(query="q", local_chunks=[_chunk()], web_results=[], sufficient=True, gap="")],
    )
    assert _route_after_research({"research": research}) == "evidence_review"


def test_route_after_drafting_finalizes_when_not_blocked():
    result = DraftingResult(draft_text="draft", verification=None, blocked=False)
    assert _route_after_drafting({"drafting_result": result}) == "finalize"


def test_route_after_drafting_handoffs_when_blocked():
    result = DraftingResult(draft_text="", verification=None, blocked=True, block_reason="x")
    assert _route_after_drafting({"drafting_result": result}) == "handoff"
