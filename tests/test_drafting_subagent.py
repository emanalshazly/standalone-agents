"""
Tests for src/subagents/drafting_subagent.py — the highest-stakes module
in the repo. Covers: the out-of-scope defensive keyword check, a
successful citation-verified draft, and the block-after-exhausted-retries
path, all with stub LLMs (no network/API key needed).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.legal_index import RetrievedChunk
from src.subagents.drafting_subagent import (
    DraftingSubAgent,
    _contains_out_of_scope_keywords,
)
from src.subagents.evidence_review_subagent import EvidenceReviewResult
from src.subagents.research_subagent import ResearchIteration, ResearchResult


def test_out_of_scope_keyword_detection_arabic():
    assert _contains_out_of_scope_keywords("أنا متهم في قضية جنائية") is True


def test_out_of_scope_keyword_detection_english():
    assert _contains_out_of_scope_keywords("I was charged with a criminal offense") is True


def test_in_scope_text_not_flagged():
    assert _contains_out_of_scope_keywords("صاحب العمل أنهى عقدي بدون إخطار") is False


def _chunk():
    return RetrievedChunk(
        entry_id="notice_period_indefinite",
        text="مهلة الإخطار قبل الإنهاء 3 أشهر.",
        language="ar",
        law_name_ar="قانون العمل رقم 14 لسنة 2025",
        law_name_en="Labor Law No. 14 of 2025",
        article_number="156_OR_123_DISPUTED",
        article_number_confidence="CONFLICTING_ACROSS_SOURCES",
        source_urls=["https://example.com"],
        verified_by_lawyer=False,
        rerank_score=0.9,
    )


def _research_with_one_chunk():
    chunk = _chunk()
    return ResearchResult(
        original_query="q",
        iterations=[
            ResearchIteration(query="q", local_chunks=[chunk], web_results=[], sufficient=True, gap="")
        ],
    )


def _empty_evidence_review():
    return EvidenceReviewResult(case_facts="facts", gaps=[], risk_notes=[])


class _StubDraftLLM:
    def __init__(self, draft_text):
        self._draft_text = draft_text

    def invoke(self, messages):
        class _R:
            pass

        r = _R()
        r.content = self._draft_text
        return r


class _StubVerifierLLM:
    def __init__(self, verdict="yes"):
        self._verdict = verdict

    def invoke(self, messages):
        class _R:
            pass

        r = _R()
        r.content = f'{{"verdict": "{self._verdict}", "reason": "test"}}'
        return r


def test_out_of_scope_facts_block_before_any_llm_call():
    subagent = DraftingSubAgent(llm=_StubDraftLLM("should never be used"))
    result = subagent.draft(
        case_facts="أنا متهم في قضية جنائية وأحتاج مساعدة",
        research=_research_with_one_chunk(),
        evidence_review=_empty_evidence_review(),
    )
    assert result.blocked is True
    assert "جنائي" in result.block_reason or "جنائ" in result.block_reason


def test_successful_draft_is_not_blocked_and_has_draft_header():
    drafting_llm = _StubDraftLLM("مهلة الإخطار قبل الإنهاء 3 أشهر [1].")
    verifier_llm = _StubVerifierLLM(verdict="yes")
    subagent = DraftingSubAgent(llm=drafting_llm, verifier_llm=verifier_llm)

    result = subagent.draft(
        case_facts="صاحب العمل أنهى عقدي بدون إخطار",
        research=_research_with_one_chunk(),
        evidence_review=_empty_evidence_review(),
        language="ar",
    )

    assert result.blocked is False
    assert "مسودة أولية" in result.draft_text
    assert "غير جاهزة للتقديم" in result.draft_text
    assert result.retry_count == 0


def test_draft_blocked_after_exhausting_retries_when_never_verified():
    drafting_llm = _StubDraftLLM("مهلة الإخطار قبل الإنهاء 3 أشهر [1].")
    verifier_llm = _StubVerifierLLM(verdict="no")  # never supports the claim
    subagent = DraftingSubAgent(llm=drafting_llm, verifier_llm=verifier_llm, max_retries=2)

    result = subagent.draft(
        case_facts="صاحب العمل أنهى عقدي بدون إخطار",
        research=_research_with_one_chunk(),
        evidence_review=_empty_evidence_review(),
    )

    assert result.blocked is True
    assert result.retry_count == 2
    assert result.draft_text == ""  # never return a half-verified draft
