"""
Tests for src/subagents/evidence_review_subagent.py's pure parsing logic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.subagents.evidence_review_subagent import (
    EvidenceReviewSubAgent,
    _parse_evidence_review_response,
)
from src.subagents.research_subagent import ResearchIteration, ResearchResult


def test_parse_valid_evidence_review_response():
    raw = """
    {
      "supporting_points": [{"citation_index": 1, "explanation": "يدعم الادعاء"}],
      "gaps": [{"description": "لا يوجد تاريخ دقيق للإنهاء", "why_it_matters": "يحدد مدة الإخطار"}],
      "risk_notes": ["قد يكون هناك دفاع من صاحب العمل"],
      "overall_assessment": "الوضع يحتاج توضيح إضافي"
    }
    """
    result = _parse_evidence_review_response(raw)

    assert result.parse_failed is False
    assert len(result.supporting_points) == 1
    assert result.supporting_points[0].citation_index == 1
    assert len(result.gaps) == 1
    assert result.gaps[0].description == "لا يوجد تاريخ دقيق للإنهاء"
    assert result.risk_notes == ["قد يكون هناك دفاع من صاحب العمل"]
    assert result.has_significant_gaps is True


def test_parse_malformed_response_forces_manual_review_gap():
    result = _parse_evidence_review_response("this is not json")

    assert result.parse_failed is True
    assert result.has_significant_gaps is True
    assert "مراجعة" in result.gaps[0].why_it_matters or "مراجعة" in result.overall_assessment


def test_parse_response_with_no_gaps_has_no_significant_gaps():
    raw = '{"supporting_points": [], "gaps": [], "risk_notes": [], "overall_assessment": "لا توجد فجوات"}'
    result = _parse_evidence_review_response(raw)
    assert result.has_significant_gaps is False


class _StubLLM:
    def __init__(self, content):
        self._content = content

    def invoke(self, messages):
        class _R:
            pass

        r = _R()
        r.content = self._content
        return r


def test_evidence_review_subagent_run_sets_case_facts():
    llm = _StubLLM('{"supporting_points": [], "gaps": [], "risk_notes": [], "overall_assessment": "ok"}')
    subagent = EvidenceReviewSubAgent(llm=llm)

    empty_research = ResearchResult(
        original_query="q",
        iterations=[ResearchIteration(query="q", local_chunks=[], web_results=[], sufficient=True, gap="")],
    )

    result = subagent.run("صاحب العمل أنهى عقدي فجأة", empty_research)
    assert result.case_facts == "صاحب العمل أنهى عقدي فجأة"
