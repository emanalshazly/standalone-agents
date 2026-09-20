"""
Research Sub-Agent - وكيل البحث (حلقة ReAct)

Implements the iterative "loop system" requested for the case-assistant
track: search -> judge sufficiency -> refine query -> search again, bounded
by max_iterations. This is a REAL loop driven by an LLM sufficiency
judgment each round, not a fixed single retrieval call like the
legal-literacy agent's `retrieve` node.

Combines two sources, kept explicitly distinguishable downstream:
  - EgyptianLegalIndex (local): may include lawyer-verified chunks.
  - web_search (via src/tools/web_search.py): always tagged
    trust_tier="web_unverified" — it is a hint to investigate further, not
    a citable authority on its own. The drafting sub-agent must not treat a
    web result the same way it treats a lawyer-verified local chunk.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.rag.legal_index import EgyptianLegalIndex, RetrievedChunk
from src.tools.web_search import SearchProvider, WebSearchResult

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 3

_SUFFICIENCY_SYSTEM_PROMPT = """أنت تُقيّم كفاية نتائج بحث قانوني. أجب حصراً بصيغة JSON:
{"sufficient": true|false, "gap": "وصف موجز لما هو ناقص إن لم تكن كافية", "refined_query": "استعلام بحث معدّل إن لم تكن كافية"}
اعتبر النتائج كافية فقط إذا كانت تغطي السؤال بشكل مباشر مع مصدر واحد على الأقل محدد (اسم قانون/مادة أو مصدر موثوق)."""


@dataclass
class ResearchIteration:
    query: str
    local_chunks: list[RetrievedChunk]
    web_results: list[WebSearchResult]
    sufficient: bool
    gap: str


@dataclass
class ResearchResult:
    original_query: str
    iterations: list[ResearchIteration] = field(default_factory=list)

    @property
    def final_local_chunks(self) -> list[RetrievedChunk]:
        return self.iterations[-1].local_chunks if self.iterations else []

    @property
    def final_web_results(self) -> list[WebSearchResult]:
        return self.iterations[-1].web_results if self.iterations else []

    @property
    def sufficient(self) -> bool:
        return bool(self.iterations) and self.iterations[-1].sufficient

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)


def _parse_sufficiency_response(raw: str) -> tuple[bool, str, Optional[str]]:
    """Pure parsing logic, unit-testable without an LLM call."""
    try:
        parsed = json.loads(raw)
        sufficient = bool(parsed.get("sufficient", False))
        gap = parsed.get("gap", "")
        refined_query = parsed.get("refined_query") or None
        return sufficient, gap, refined_query
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Sufficiency judge returned non-JSON, treating as insufficient: %r", raw)
        return False, f"unparseable judge output: {raw[:200]}", None


def _should_stop(iteration_index: int, max_iterations: int, sufficient: bool) -> bool:
    """Pure loop-termination logic, unit-testable in isolation."""
    if sufficient:
        return True
    return iteration_index >= max_iterations - 1


class ResearchSubAgent:
    def __init__(
        self,
        legal_index: EgyptianLegalIndex,
        search_provider: SearchProvider,
        llm,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ):
        self.legal_index = legal_index
        self.search_provider = search_provider
        self.llm = llm
        self.max_iterations = max_iterations

    def _judge_sufficiency(
        self,
        original_query: str,
        current_query: str,
        local_chunks: list[RetrievedChunk],
        web_results: list[WebSearchResult],
    ) -> tuple[bool, str, Optional[str]]:
        from langchain_core.messages import HumanMessage, SystemMessage

        sources_block = "\n".join(
            [f"[محلي] {c.citation_label}: {c.text}" for c in local_chunks]
            + [f"[ويب غير موثّق] {w.title} ({w.url}): {w.snippet}" for w in web_results]
        ) or "(لا توجد نتائج)"

        messages = [
            SystemMessage(content=_SUFFICIENCY_SYSTEM_PROMPT),
            HumanMessage(
                content=f"السؤال الأصلي: {original_query}\n"
                f"استعلام البحث الحالي: {current_query}\n\nالنتائج:\n{sources_block}"
            ),
        ]
        response = self.llm.invoke(messages)
        raw = getattr(response, "content", str(response))
        return _parse_sufficiency_response(raw)

    def run(self, query: str) -> ResearchResult:
        result = ResearchResult(original_query=query)
        current_query = query

        for i in range(self.max_iterations):
            local_chunks = self.legal_index.retrieve(current_query)
            web_results = self.search_provider.search(current_query)

            sufficient, gap, refined_query = self._judge_sufficiency(
                original_query=query,
                current_query=current_query,
                local_chunks=local_chunks,
                web_results=web_results,
            )

            result.iterations.append(
                ResearchIteration(
                    query=current_query,
                    local_chunks=local_chunks,
                    web_results=web_results,
                    sufficient=sufficient,
                    gap=gap,
                )
            )

            if _should_stop(i, self.max_iterations, sufficient):
                if not sufficient:
                    logger.warning(
                        "Research loop exhausted %d iterations without sufficient "
                        "sources for query %r (last gap: %s)",
                        self.max_iterations,
                        query,
                        gap,
                    )
                break

            current_query = refined_query or current_query

        return result
