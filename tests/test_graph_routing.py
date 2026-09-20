"""
Tests for the LangGraph conditional-edge routing functions in
src/graph/legal_graph.py. These are pure functions of state, so they can
be tested directly without compiling/running the full graph or calling
any LLM — this is the real branching logic that replaced
src/core/orchestrator.py's plain dict lookup.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.legal_graph import (
    MAX_DRAFT_RETRIES,
    _route_after_classify,
    _route_after_retrieve,
    _route_after_verify,
)
from src.rag.legal_index import RetrievedChunk
from src.verification.citation_verifier import ClaimVerdict, VerificationResult


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        entry_id="probation_period",
        text="لا يجوز تجديد فترة الاختبار.",
        language="ar",
        law_name_ar="قانون العمل رقم 14 لسنة 2025",
        law_name_en="Labor Law No. 14 of 2025",
        article_number="104",
        article_number_confidence="single_source_only",
        source_urls=[],
        verified_by_lawyer=False,
        rerank_score=0.9,
    )


def test_route_after_classify_in_scope():
    assert _route_after_classify({"in_scope": True}) == "retrieve"


def test_route_after_classify_out_of_scope():
    assert _route_after_classify({"in_scope": False}) == "handoff"


def test_route_after_retrieve_no_chunks_handoffs():
    assert _route_after_retrieve({"retrieved_chunks": []}) == "handoff"
    assert _route_after_retrieve({}) == "handoff"


def test_route_after_retrieve_with_chunks_drafts():
    assert _route_after_retrieve({"retrieved_chunks": [_chunk()]}) == "draft_answer"


def test_route_after_verify_all_supported_goes_to_disclaimer():
    result = VerificationResult(claims=[
        ClaimVerdict("s", [1], supported=True, verdict_detail="", cited_chunks_verified_by_lawyer=False)
    ])
    state = {"verification": result, "draft_retry_count": 1}
    assert _route_after_verify(state) == "add_disclaimer"


def test_route_after_verify_unsupported_retries_while_budget_remains():
    result = VerificationResult(claims=[
        ClaimVerdict("s", [1], supported=False, verdict_detail="no", cited_chunks_verified_by_lawyer=False)
    ])
    state = {"verification": result, "draft_retry_count": MAX_DRAFT_RETRIES - 1}
    assert _route_after_verify(state) == "draft_answer"


def test_route_after_verify_unsupported_hands_off_after_retry_budget_exhausted():
    result = VerificationResult(claims=[
        ClaimVerdict("s", [1], supported=False, verdict_detail="no", cited_chunks_verified_by_lawyer=False)
    ])
    state = {"verification": result, "draft_retry_count": MAX_DRAFT_RETRIES}
    assert _route_after_verify(state) == "handoff"


def test_route_after_verify_uncited_claims_never_pass():
    result = VerificationResult(uncited_claims=["some fact stated with no [n] marker"])
    state = {"verification": result, "draft_retry_count": MAX_DRAFT_RETRIES}
    assert _route_after_verify(state) == "handoff"
