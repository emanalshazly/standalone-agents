"""
Tests for the citation verifier's pure logic (sentence splitting, marker
parsing, uncited-claim detection) using a stub judge so no API key/network
is required. This directly tests the mechanism that replaced the old fake
`_calculate_confidence` heuristic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.legal_index import RetrievedChunk
from src.verification.citation_verifier import verify_draft


def _make_chunk(entry_id: str, text: str, verified: bool = False) -> RetrievedChunk:
    return RetrievedChunk(
        entry_id=entry_id,
        text=text,
        language="ar",
        law_name_ar="قانون العمل رقم 14 لسنة 2025",
        law_name_en="Labor Law No. 14 of 2025",
        article_number="104",
        article_number_confidence="single_source_only",
        source_urls=["https://example.com"],
        verified_by_lawyer=verified,
        rerank_score=0.9,
    )


class _StubYesJudge:
    """Every claim is entailed by its cited source."""

    def invoke(self, messages):
        class _R:
            content = '{"verdict": "yes", "reason": "matches source"}'

        return _R()


class _StubNoJudge:
    """Every claim is rejected."""

    def invoke(self, messages):
        class _R:
            content = '{"verdict": "no", "reason": "not supported by source"}'

        return _R()


def test_uncited_claim_detected():
    chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.")
    draft = "لا يجوز تجديد فترة الاختبار بعد انتهائها."  # no [1] marker at all
    result = verify_draft(draft, [chunk], llm=_StubYesJudge())

    assert result.uncited_claims, "a factual sentence with no citation marker must be flagged"
    assert not result.all_supported


def test_cited_and_supported_claim_passes():
    chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.")
    draft = "لا يجوز تجديد فترة الاختبار [1]."
    result = verify_draft(draft, [chunk], llm=_StubYesJudge())

    assert not result.uncited_claims
    assert len(result.claims) == 1
    assert result.claims[0].supported
    assert result.all_supported


def test_cited_but_unsupported_claim_fails():
    chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.")
    draft = "يمكن تجديد فترة الاختبار لمدة عام كامل [1]."  # contradicts the source
    result = verify_draft(draft, [chunk], llm=_StubNoJudge())

    assert len(result.claims) == 1
    assert not result.claims[0].supported
    assert not result.all_supported


def test_citation_marker_out_of_range_is_treated_as_uncited():
    chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.")
    draft = "لا يجوز تجديد فترة الاختبار [5]."  # only 1 chunk was retrieved
    result = verify_draft(draft, [chunk], llm=_StubYesJudge())

    assert result.uncited_claims
    assert not result.all_supported


def test_any_unverified_lawyer_review_flag():
    unverified_chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.", verified=False)
    draft = "لا يجوز تجديد فترة الاختبار [1]."
    result = verify_draft(draft, [unverified_chunk], llm=_StubYesJudge())

    assert result.any_unverified_lawyer_review is True

    verified_chunk = _make_chunk("probation_period", "لا يجوز تجديد فترة الاختبار.", verified=True)
    result2 = verify_draft(draft, [verified_chunk], llm=_StubYesJudge())
    assert result2.any_unverified_lawyer_review is False
