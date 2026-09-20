"""
Evidence Review Sub-Agent - وكيل مراجعة الأدلة

Takes the user's own description of their situation/evidence (a contract,
a termination message, dates, correspondence) plus the ResearchSubAgent's
output, and produces a structured gap analysis: what supports the user's
position, what's missing, and explicit risk notes.

This does NOT decide whether the user has a "good case" — it surfaces
what the retrieved legal basis does and does not cover, and flags evidence
gaps a human lawyer would want closed. The drafting sub-agent consumes
this output; a low-confidence or gap-heavy review should make the eventual
draft more hedged, never more confident.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.subagents.research_subagent import ResearchResult

logger = logging.getLogger(__name__)

_EVIDENCE_REVIEW_SYSTEM_PROMPT = """أنت مساعد مراجعة أدلة لمحامٍ (لست بديلاً عنه). مهمتك تحليل وقائع الحالة \
المقدَّمة من المستخدم في ضوء نتائج البحث القانوني المرفقة، وإخراج تحليل منظم فقط — \
بدون إصدار حكم نهائي على قوة القضية.

أجب حصراً بصيغة JSON:
{
  "supporting_points": [{"citation_index": <رقم المصدر المحلي 1-indexed أو null للويب>, "explanation": "..."}],
  "gaps": [{"description": "دليل أو معلومة ناقصة", "why_it_matters": "لماذا هذا مهم قانونياً"}],
  "risk_notes": ["ملاحظة خطر أو نقطة ضعف محتملة في الموقف"],
  "overall_assessment": "ملخص محايد بجملتين كحد أقصى - لا تستخدم عبارات مثل 'ستربح القضية'"
}

لا تخترع وقائع لم يذكرها المستخدم. لا تخترع نصوصاً قانونية غير موجودة في نتائج البحث."""


@dataclass
class EvidenceGap:
    description: str
    why_it_matters: str


@dataclass
class SupportingPoint:
    citation_index: Optional[int]
    explanation: str


@dataclass
class EvidenceReviewResult:
    case_facts: str
    supporting_points: list[SupportingPoint] = field(default_factory=list)
    gaps: list[EvidenceGap] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    overall_assessment: str = ""
    parse_failed: bool = False

    @property
    def has_significant_gaps(self) -> bool:
        return len(self.gaps) > 0


def _parse_evidence_review_response(raw: str) -> EvidenceReviewResult:
    """Pure parsing logic, unit-testable without an LLM call."""
    try:
        parsed = json.loads(raw)
        return EvidenceReviewResult(
            case_facts="",  # filled in by caller
            supporting_points=[
                SupportingPoint(
                    citation_index=p.get("citation_index"),
                    explanation=p.get("explanation", ""),
                )
                for p in parsed.get("supporting_points", [])
            ],
            gaps=[
                EvidenceGap(
                    description=g.get("description", ""),
                    why_it_matters=g.get("why_it_matters", ""),
                )
                for g in parsed.get("gaps", [])
            ],
            risk_notes=list(parsed.get("risk_notes", [])),
            overall_assessment=parsed.get("overall_assessment", ""),
            parse_failed=False,
        )
    except (json.JSONDecodeError, AttributeError, TypeError):
        logger.warning("Evidence review judge returned non-JSON: %r", raw)
        return EvidenceReviewResult(
            case_facts="",
            gaps=[
                EvidenceGap(
                    description="تعذّر تحليل نتيجة مراجعة الأدلة آلياً",
                    why_it_matters="يجب مراجعة الحالة يدوياً بواسطة محامٍ قبل أي استخدام",
                )
            ],
            overall_assessment="فشل التحليل الآلي — مراجعة بشرية إلزامية",
            parse_failed=True,
        )


class EvidenceReviewSubAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, case_facts: str, research: ResearchResult) -> EvidenceReviewResult:
        from langchain_core.messages import HumanMessage, SystemMessage

        local_chunks = research.final_local_chunks
        web_results = research.final_web_results

        sources_block = "\n".join(
            [f"[{i+1}] {c.citation_label}: {c.text}" for i, c in enumerate(local_chunks)]
            + [f"[ويب غير موثّق] {w.title}: {w.snippet}" for w in web_results]
        ) or "(لا توجد نتائج بحث)"

        messages = [
            SystemMessage(content=_EVIDENCE_REVIEW_SYSTEM_PROMPT),
            HumanMessage(
                content=f"وقائع الحالة كما وصفها المستخدم:\n{case_facts}\n\n"
                f"نتائج البحث القانوني:\n{sources_block}"
            ),
        ]
        response = self.llm.invoke(messages)
        raw = getattr(response, "content", str(response))

        result = _parse_evidence_review_response(raw)
        result.case_facts = case_facts
        return result
