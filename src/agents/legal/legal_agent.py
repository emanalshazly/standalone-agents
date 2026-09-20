"""
Egyptian Legal-Literacy Agent - وكيل محو الأمية القانونية المصري

Thin public facade over the LangGraph pipeline in src/graph/legal_graph.py.
This replaces the old MedicalAgent-style class inheriting from
src/core/base_agent.py's BaseAgent (deleted in this pivot) — there is no
more shared "generic domain agent" base class, because this project is
now scoped to exactly one domain, on purpose (see PROJECT_OVERVIEW.md).

Notably absent compared to the old BaseAgent: a `confidence` float. The
old implementation computed `confidence` as `0.5 + 0.1*len(sources) +
0.1*len(response>100)` — a number with no relationship to correctness.
This class instead exposes `lawyer_review_pending` (are the underlying
sources lawyer-verified?) and `handoff_required` (did the graph refuse to
answer?), which are real, mechanically-grounded signals.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.graph.legal_graph import build_legal_graph
from src.rag.legal_index import EgyptianLegalIndex, RetrievedChunk


@dataclass
class LegalAnswer:
    answer: str
    language: str
    handoff_required: bool
    lawyer_review_pending: bool
    citations: list[str] = field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)


def _build_chat_model(provider: str, model_name: str, temperature: float):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model_name, temperature=temperature)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model_name, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: {provider}")


class EgyptianLegalAgent:
    """Plain-language Egyptian contract/labor-rights Q&A, citation-verified.

    Explicitly OUT OF SCOPE (see src/graph/legal_graph.py OUT_OF_SCOPE_TOPICS
    and config/config.example.yaml `scope:`): criminal law, litigation
    strategy, court filings, tax law. Queries in those areas are routed to
    human handoff, not answered.
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.2,
        legal_index: EgyptianLegalIndex | None = None,
    ):
        self.llm = _build_chat_model(llm_provider, model_name, temperature)
        self.legal_index = legal_index or EgyptianLegalIndex()
        self._graph = build_legal_graph(self.legal_index, self.llm)

    def query(self, text: str) -> LegalAnswer:
        result = self._graph.invoke({"query": text, "draft_retry_count": 0})

        chunks = result.get("retrieved_chunks", [])
        return LegalAnswer(
            answer=result.get("final_answer", ""),
            language=result.get("language", "ar"),
            handoff_required=result.get("handoff_required", False),
            lawyer_review_pending=result.get("lawyer_review_pending", False),
            citations=[c.citation_label for c in chunks],
            retrieved_chunks=chunks,
        )
