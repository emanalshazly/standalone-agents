"""
Drafting Sub-Agent - وكيل الصياغة

Assembles a draft document (e.g. a labor-office complaint memo) from the
research + evidence-review sub-agents' output. This is the highest-stakes
component in the repo, so it inherits the strictest guardrails:

1. Citations in the draft body may ONLY reference locally-retrieved,
   numbered sources ([1], [2], ...) — never a web result. Web findings can
   inform phrasing but are appended separately as unverified research
   notes, never presented as a citation the reader could mistake for
   verified legal authority.
2. Every draft is run through the SAME citation_verifier used by the
   legal-literacy agent before being returned. Exhausted retries block the
   draft entirely rather than returning a best-effort, partially-grounded
   document — the exact opposite of what the 2026 court-sanctioned filings
   did.
3. A keyword-based defensive check blocks obviously out-of-scope (criminal)
   matters even if the graph-level scope classifier upstream missed them —
   belt-and-suspenders, not a replacement for that classifier.
4. The "DRAFT — NOT FOR FILING" header is added in code, not requested from
   the LLM, so it cannot be omitted by a bad generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.subagents.evidence_review_subagent import EvidenceReviewResult
from src.subagents.research_subagent import ResearchResult
from src.verification.citation_verifier import VerificationResult, verify_draft

logger = logging.getLogger(__name__)

MAX_DRAFT_RETRIES = 2

_CRIMINAL_LAW_KEYWORDS = [
    "جريمة", "جنائي", "قتل", "سرقة", "اتهام جنائي", "نيابة عامة", "حبس",
    "criminal", "felony", "prosecution", "police report",
]

_DRAFT_HEADER_AR = (
    "⚠️ مسودة أولية لمراجعة محامٍ مرخّص — غير جاهزة للتقديم لأي جهة رسمية أو محكمة.\n"
    "هذا الناتج مساعدة صياغة آلية وليس تمثيلاً قانونياً ولا بديلاً عن محامٍ.\n"
    "----------------------------------------\n"
)
_DRAFT_HEADER_EN = (
    "⚠️ Preliminary draft for a licensed lawyer's review — NOT ready for "
    "filing with any official body or court.\n"
    "This is automated drafting assistance, not legal representation and "
    "not a substitute for a lawyer.\n"
    "----------------------------------------\n"
)

_DRAFTING_SYSTEM_PROMPT_AR = """أنت مساعد صياغة قانونية. اكتب مسودة {document_type} بناءً حصراً على \
وقائع الحالة ونتائج البحث المرفقة. استشهد بكل معلومة قانونية برقم المصدر المحلي [n] فقط \
(لا تستخدم أرقاماً لنتائج الويب). لا تضف وقائع لم يذكرها المستخدم. لا تدّعِ نتيجة القضية. \
اذكر بوضوح أي نقطة غير مؤكدة بدلاً من افتراضها."""


@dataclass
class DraftingResult:
    draft_text: str
    verification: VerificationResult | None
    blocked: bool
    block_reason: str = ""
    retry_count: int = 0


def _contains_out_of_scope_keywords(text: str) -> bool:
    """Defensive secondary check — pure function, unit-testable."""
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in _CRIMINAL_LAW_KEYWORDS)


class DraftingSubAgent:
    def __init__(self, llm, verifier_llm=None, max_retries: int = MAX_DRAFT_RETRIES):
        self.llm = llm
        self.verifier_llm = verifier_llm or llm
        self.max_retries = max_retries

    def _generate_draft_text(
        self,
        case_facts: str,
        research: ResearchResult,
        evidence_review: EvidenceReviewResult,
        document_type: str,
        language: str,
        retry_feedback: str,
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        chunks = research.final_local_chunks
        sources_block = "\n".join(
            f"[{i+1}] ({c.citation_label}) {c.text}" for i, c in enumerate(chunks)
        ) or "(لا توجد مصادر محلية موثوقة كافية)"

        gaps_block = "\n".join(
            f"- {g.description}: {g.why_it_matters}" for g in evidence_review.gaps
        ) or "(لا توجد فجوات مسجّلة)"

        system_prompt = _DRAFTING_SYSTEM_PROMPT_AR.format(document_type=document_type)
        if retry_feedback:
            system_prompt += f"\n\nمحاولة سابقة فشل التحقق منها، صحّح: {retry_feedback}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"وقائع الحالة:\n{case_facts}\n\n"
                    f"المصادر القانونية المحلية:\n{sources_block}\n\n"
                    f"فجوات الأدلة المسجّلة (اذكرها في المسودة كنقاط تحتاج استكمال):\n{gaps_block}"
                )
            ),
        ]
        response = self.llm.invoke(messages)
        return getattr(response, "content", str(response))

    def draft(
        self,
        case_facts: str,
        research: ResearchResult,
        evidence_review: EvidenceReviewResult,
        document_type: str = "مذكرة شكوى",
        language: str = "ar",
    ) -> DraftingResult:
        if _contains_out_of_scope_keywords(case_facts):
            return DraftingResult(
                draft_text="",
                verification=None,
                blocked=True,
                block_reason=(
                    "الوقائع تشير لعناصر جنائية محتملة — خارج نطاق هذه الأداة تماماً. "
                    "يُرجى استشارة محامٍ جنائي مباشرة."
                ),
            )

        chunks = research.final_local_chunks
        retry_feedback = ""
        verification: VerificationResult | None = None

        for attempt in range(self.max_retries + 1):
            draft_text = self._generate_draft_text(
                case_facts, research, evidence_review, document_type, language, retry_feedback
            )
            verification = verify_draft(draft_text, chunks, self.verifier_llm)

            if verification.all_supported:
                final_text = self._finalize(draft_text, evidence_review, research, language)
                return DraftingResult(
                    draft_text=final_text,
                    verification=verification,
                    blocked=False,
                    retry_count=attempt,
                )

            feedback_parts = [f"uncited: {c}" for c in verification.uncited_claims]
            feedback_parts += [
                f"unsupported: {c.sentence[:100]} ({c.verdict_detail})"
                for c in verification.claims
                if not c.supported
            ]
            retry_feedback = "; ".join(feedback_parts)

        return DraftingResult(
            draft_text="",
            verification=verification,
            blocked=True,
            block_reason=(
                "تعذّر إنتاج مسودة كل ادعاءاتها مدعومة بمصادر موثّقة بعد "
                f"{self.max_retries + 1} محاولات. راجع الحالة يدوياً بدلاً من الاعتماد "
                "على مسودة غير مكتملة التحقق."
            ),
            retry_count=self.max_retries,
        )

    @staticmethod
    def _finalize(
        draft_text: str,
        evidence_review: EvidenceReviewResult,
        research: ResearchResult,
        language: str,
    ) -> str:
        header = _DRAFT_HEADER_AR if language == "ar" else _DRAFT_HEADER_EN
        footer_parts = [draft_text]

        if research.final_web_results:
            web_notes = "\n".join(
                f"- {w.title} ({w.url}) — غير موثّق، للاطلاع فقط"
                for w in research.final_web_results
            )
            footer_parts.append(f"\n\n## ملاحظات بحثية إضافية (مصادر ويب غير موثّقة):\n{web_notes}")

        if evidence_review.risk_notes:
            risk_block = "\n".join(f"- {r}" for r in evidence_review.risk_notes)
            footer_parts.append(f"\n\n## ملاحظات مخاطر:\n{risk_block}")

        return header + "\n".join(footer_parts)
