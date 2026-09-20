"""
Case-Assistant Agent - وكيل المساعدة القضائية

Public facade over src/graph/case_drafting_graph.py. Kept as a SEPARATE
class from src/agents/legal/legal_agent.py's EgyptianLegalAgent on purpose:
different risk tier, different scope-gate wording, different (louder)
disclaimers, and a research loop that touches the live web — none of
which should leak into the simpler literacy agent by accident of a shared
base class. See PROJECT_OVERVIEW.md "Two-track architecture".

This agent explicitly:
  - never claims to represent the user or to have filed anything
  - always returns DRAFT-ONLY output (see DraftingSubAgent._finalize)
  - refuses (hands off) criminal-law-adjacent, tax, and other topics
    declared out of scope in src/graph/legal_graph.py's OUT_OF_SCOPE_TOPICS
  - treats web search results as strictly lower-trust than the local,
    partially-lawyer-reviewed knowledge base
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.graph.case_drafting_graph import build_case_drafting_graph
from src.rag.legal_index import EgyptianLegalIndex
from src.subagents.evidence_review_subagent import EvidenceGap
from src.tools.web_search import WebSearchResult, get_search_provider


@dataclass
class CaseDraftAnswer:
    draft_text: str
    language: str
    handoff_required: bool
    research_iterations: int
    evidence_gaps: list[EvidenceGap] = field(default_factory=list)
    web_sources_consulted: list[WebSearchResult] = field(default_factory=list)


def _build_chat_model(provider: str, model_name: str, temperature: float):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model_name, temperature=temperature)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model_name, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: {provider}")


class CaseAssistantAgent:
    """Drafting + evidence-review assistant for Egyptian labor/civil
    contract disputes. NOT a substitute for a lawyer; every output is
    marked DRAFT-ONLY and must be reviewed before any real-world use."""

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.2,
        legal_index: EgyptianLegalIndex | None = None,
        max_research_iterations: int = 3,
        max_draft_retries: int = 2,
    ):
        self.llm = _build_chat_model(llm_provider, model_name, temperature)
        self.legal_index = legal_index or EgyptianLegalIndex()
        self.search_provider = get_search_provider()
        self._graph = build_case_drafting_graph(
            legal_index=self.legal_index,
            search_provider=self.search_provider,
            llm=self.llm,
            max_research_iterations=max_research_iterations,
            max_draft_retries=max_draft_retries,
        )

    def prepare_draft(
        self, case_facts: str, document_type: str = "مذكرة شكوى"
    ) -> CaseDraftAnswer:
        result = self._graph.invoke(
            {"case_facts": case_facts, "document_type": document_type}
        )

        research = result.get("research")
        evidence_review = result.get("evidence_review")

        return CaseDraftAnswer(
            draft_text=result.get("final_output", ""),
            language=result.get("language", "ar"),
            handoff_required=result.get("handoff_required", True),
            research_iterations=research.iteration_count if research else 0,
            evidence_gaps=evidence_review.gaps if evidence_review else [],
            web_sources_consulted=research.final_web_results if research else [],
        )
