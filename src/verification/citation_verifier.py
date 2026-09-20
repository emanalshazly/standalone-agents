"""
Citation Verifier - التحقق من صحة الاستشهادات

This is the direct, architectural answer to the legal-AI hallucination
problem this project pivoted around: Stanford/Yale research found even
specialized legal RAG tools hallucinate citations 17-34% of the time, and
2026 saw six-figure court sanctions ($110,000 in one Oregon case) against
lawyers who filed AI-fabricated citations.

Retrieval quality (src/rag/legal_index.py) is necessary but NOT sufficient:
a model can retrieve the right source and still misstate what it says.
This module runs a per-claim entailment check ("does the cited source text
actually support this sentence?") using an LLM-as-judge constrained to a
yes/no/partial verdict, and it can BLOCK an answer, not just annotate it.

This is a real check against real source text on every answer — it is not
a heuristic score computed from unrelated signals (contrast with the old
src/core/base_agent.py `_calculate_confidence`, which added +0.1/+0.3 for
source count and response length regardless of whether the content was
actually correct).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Protocol

from src.rag.legal_index import RetrievedChunk

logger = logging.getLogger(__name__)

_CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")
# Split on Arabic and Latin sentence terminators, keeping it simple and
# conservative (a bad split just means we check a slightly larger claim
# unit — it never lets an ungrounded claim through unchecked).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!؟?])\s+")

_JUDGE_SYSTEM_PROMPT_AR = """أنت مدقق استشهادات قانونية صارم. مهمتك الوحيدة: تحديد ما إذا كان "النص المصدر" يدعم "الادعاء" المذكور، أم لا.
أجب حصراً بصيغة JSON: {"verdict": "yes"|"no"|"partial", "reason": "شرح موجز بجملة واحدة"}.
- "yes": النص المصدر يدعم الادعاء بوضوح ودون تحريف.
- "partial": النص المصدر يتصل بالموضوع لكنه لا يدعم كامل تفاصيل الادعاء (مثال: رقم أو مدة مختلفة).
- "no": النص المصدر لا يدعم الادعاء إطلاقاً أو يتناقض معه.
لا تفترض معلومات غير موجودة في النص المصدر. لا تُصلح الادعاء ولا تكمله."""

_JUDGE_USER_TEMPLATE_AR = """النص المصدر:
{source_text}

الادعاء المطلوب التحقق منه:
{claim}

أجب بصيغة JSON فقط."""


class ChatModelLike(Protocol):
    """Minimal interface this module needs — matches langchain chat models
    (ChatOpenAI/ChatAnthropic .invoke(messages) -> response with .content),
    but any object implementing this method works (e.g. a test stub)."""

    def invoke(self, messages: list) -> object: ...


@dataclass
class ClaimVerdict:
    sentence: str
    citation_markers: list[int]
    supported: bool
    verdict_detail: str
    cited_chunks_verified_by_lawyer: bool


@dataclass
class VerificationResult:
    claims: list[ClaimVerdict] = field(default_factory=list)
    uncited_claims: list[str] = field(default_factory=list)

    @property
    def all_supported(self) -> bool:
        return not self.uncited_claims and all(c.supported for c in self.claims)

    @property
    def any_unverified_lawyer_review(self) -> bool:
        """True if every grounded claim rests on chunks no lawyer has yet
        reviewed — used by the graph to decide whether to add an extra
        'this content has not been reviewed by a lawyer yet' banner."""
        return any(not c.cited_chunks_verified_by_lawyer for c in self.claims)


def _looks_like_substantive_claim(sentence: str) -> bool:
    """Filter out connective/boilerplate sentences (disclaimers, greetings)
    so we don't force citations onto non-substantive text. Conservative on
    purpose: when in doubt, treat it as substantive and require a citation."""
    stripped = sentence.strip()
    if len(stripped) < 8:
        return False
    boilerplate_markers = [
        "هذه المعلومات لا تُغني",
        "ليست بديلاً عن",
        "not a substitute",
        "for informational purposes",
    ]
    return not any(marker in stripped for marker in boilerplate_markers)


def _split_sentences(draft_text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(draft_text) if s.strip()]


def _judge_claim(
    llm: ChatModelLike, claim: str, source_text: str
) -> tuple[bool, str]:
    """Run the LLM-as-judge entailment check for one (claim, source) pair."""
    from langchain_core.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(content=_JUDGE_SYSTEM_PROMPT_AR),
        HumanMessage(
            content=_JUDGE_USER_TEMPLATE_AR.format(
                source_text=source_text, claim=claim
            )
        ),
    ]
    response = llm.invoke(messages)
    raw = getattr(response, "content", str(response))

    try:
        parsed = json.loads(raw)
        verdict = parsed.get("verdict", "no").lower()
        reason = parsed.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Judge returned non-JSON output, treating as unsupported: %r", raw)
        verdict, reason = "no", f"unparseable judge output: {raw[:200]}"

    supported = verdict == "yes"
    return supported, f"{verdict}: {reason}"


def verify_draft(
    draft_text: str,
    retrieved_chunks: list[RetrievedChunk],
    llm: ChatModelLike,
) -> VerificationResult:
    """
    Check every substantive sentence in `draft_text` against the specific
    chunk(s) it cites via [n] markers (1-indexed into `retrieved_chunks`).

    A sentence with NO citation marker is recorded as an uncited claim and
    counts against `all_supported` — the draft_answer node is expected to
    cite every factual sentence; an uncited factual sentence is exactly the
    failure mode this whole pipeline exists to catch.
    """
    result = VerificationResult()

    for sentence in _split_sentences(draft_text):
        if not _looks_like_substantive_claim(sentence):
            continue

        marker_ids = [int(m) for m in _CITATION_MARKER_RE.findall(sentence)]
        if not marker_ids:
            result.uncited_claims.append(sentence)
            continue

        cited_chunks = [
            retrieved_chunks[i - 1]
            for i in marker_ids
            if 0 < i <= len(retrieved_chunks)
        ]
        if not cited_chunks:
            # Marker points outside the retrieved set — treat as uncited.
            result.uncited_claims.append(sentence)
            continue

        # Require every cited chunk to support the claim (a partial/no on
        # any cited source fails the whole sentence — conservative by design).
        verdicts = [
            _judge_claim(llm, claim=sentence, source_text=chunk.text)
            for chunk in cited_chunks
        ]
        supported = all(v[0] for v in verdicts)
        detail = "; ".join(v[1] for v in verdicts)

        result.claims.append(
            ClaimVerdict(
                sentence=sentence,
                citation_markers=marker_ids,
                supported=supported,
                verdict_detail=detail,
                cited_chunks_verified_by_lawyer=all(
                    c.verified_by_lawyer for c in cited_chunks
                ),
            )
        )

    return result
