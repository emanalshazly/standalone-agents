"""
Case-Assistant Graph - رسم بياني وكيل المساعدة القضائية

Separate from src/graph/legal_graph.py (the plain-language literacy agent)
by design — see PROJECT_OVERVIEW.md "Two-track architecture". This graph
backs the higher-risk drafting/evidence-review track:

    classify_case_scope -> [out of scope?] -> handoff
                         -> research (ReAct loop, local KB + web)
                              -> [nothing found at all?] -> handoff
                         -> evidence_review
                         -> drafting (citation-verified, bounded retries)
                              -> [blocked?] -> handoff
                         -> finalize -> END

Reuses the same IN_SCOPE_TOPICS/OUT_OF_SCOPE_TOPICS declared in
src/graph/legal_graph.py as the single source of truth for what this
project will and will not touch (still no criminal law, no tax, no
generic litigation strategy beyond labor/civil contract disputes) — the
case-assistant track answers "help me prepare my labor/contract dispute
paperwork", not "represent me in any legal matter".
"""

from __future__ import annotations

import json
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from src.graph.legal_graph import IN_SCOPE_TOPICS, OUT_OF_SCOPE_TOPICS
from src.rag.legal_index import EgyptianLegalIndex
from src.subagents.drafting_subagent import DraftingResult, DraftingSubAgent
from src.subagents.evidence_review_subagent import (
    EvidenceReviewResult,
    EvidenceReviewSubAgent,
)
from src.subagents.research_subagent import ResearchResult, ResearchSubAgent
from src.tools.web_search import SearchProvider

logger = logging.getLogger(__name__)

_SCOPE_JUDGE_SYSTEM_PROMPT = f"""أنت مصنّف نطاق لأداة مساعدة صياغة نزاعات عمالية/مدنية بسيطة في مصر \
(وليست تمثيلاً قانونياً كاملاً). ضمن هذه المواضيع فقط: {IN_SCOPE_TOPICS}.
ممنوع صراحة: {OUT_OF_SCOPE_TOPICS}، وأي طلب لاستراتيجية تقاضٍ معقدة أو تمثيل أمام محكمة جنائية.
أجب حصراً بصيغة JSON: {{"in_scope": true|false, "language": "ar"|"en", "reason": "سبب موجز"}}."""


class CaseDraftingState(TypedDict, total=False):
    case_facts: str
    document_type: str
    language: str
    in_scope: bool
    scope_reason: str
    research: ResearchResult
    evidence_review: EvidenceReviewResult
    drafting_result: DraftingResult
    final_output: str
    handoff_required: bool
    handoff_reason: str


def _detect_language_heuristic(text: str) -> str:
    arabic_chars = sum(1 for c in text if "؀" <= c <= "ۿ")
    return "ar" if arabic_chars > len(text) * 0.3 else "en"


def make_classify_case_scope_node(llm):
    def classify_case_scope(state: CaseDraftingState) -> dict:
        from langchain_core.messages import HumanMessage, SystemMessage

        case_facts = state["case_facts"]
        language = _detect_language_heuristic(case_facts)

        messages = [
            SystemMessage(content=_SCOPE_JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=case_facts),
        ]
        response = llm.invoke(messages)
        raw = getattr(response, "content", str(response))
        try:
            parsed = json.loads(raw)
            in_scope = bool(parsed.get("in_scope", False))
            reason = parsed.get("reason", "")
            language = parsed.get("language", language)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Case-scope classifier returned non-JSON, defaulting to out_of_scope: %r", raw)
            in_scope, reason = False, "scope classifier failed to parse — defaulting to safe refusal"

        return {"language": language, "in_scope": in_scope, "scope_reason": reason}

    return classify_case_scope


def make_research_node(research_subagent: ResearchSubAgent):
    def research(state: CaseDraftingState) -> dict:
        result = research_subagent.run(state["case_facts"])
        return {"research": result}

    return research


def make_evidence_review_node(evidence_subagent: EvidenceReviewSubAgent):
    def evidence_review(state: CaseDraftingState) -> dict:
        result = evidence_subagent.run(state["case_facts"], state["research"])
        return {"evidence_review": result}

    return evidence_review


def make_drafting_node(drafting_subagent: DraftingSubAgent):
    def drafting(state: CaseDraftingState) -> dict:
        result = drafting_subagent.draft(
            case_facts=state["case_facts"],
            research=state["research"],
            evidence_review=state["evidence_review"],
            document_type=state.get("document_type", "مذكرة شكوى"),
            language=state.get("language", "ar"),
        )
        return {"drafting_result": result}

    return drafting


def finalize(state: CaseDraftingState) -> dict:
    return {"final_output": state["drafting_result"].draft_text, "handoff_required": False}


def handoff(state: CaseDraftingState) -> dict:
    language = state.get("language", "ar")
    reason = (
        state.get("handoff_reason")
        or state.get("scope_reason")
        or (state.get("drafting_result").block_reason if state.get("drafting_result") else "")
    )
    if language == "ar":
        message = (
            "لا يمكن لهذه الأداة إعداد مسودة لهذه الحالة "
            f"({reason}). يُرجى التواصل مع محامٍ مرخّص مباشرة."
        )
    else:
        message = (
            f"This tool cannot prepare a draft for this case ({reason}). "
            "Please consult a licensed lawyer directly."
        )
    return {"final_output": message, "handoff_required": True}


def _route_after_classify(state: CaseDraftingState) -> str:
    return "research" if state.get("in_scope") else "handoff"


def _route_after_research(state: CaseDraftingState) -> str:
    research: ResearchResult = state["research"]
    if not research.final_local_chunks and not research.final_web_results:
        return "handoff"
    return "evidence_review"


def _route_after_drafting(state: CaseDraftingState) -> str:
    drafting_result: DraftingResult = state["drafting_result"]
    return "handoff" if drafting_result.blocked else "finalize"


def build_case_drafting_graph(
    legal_index: EgyptianLegalIndex,
    search_provider: SearchProvider,
    llm,
    verifier_llm=None,
    max_research_iterations: int = 3,
    max_draft_retries: int = 2,
):
    verifier_llm = verifier_llm or llm

    research_subagent = ResearchSubAgent(
        legal_index=legal_index,
        search_provider=search_provider,
        llm=llm,
        max_iterations=max_research_iterations,
    )
    evidence_subagent = EvidenceReviewSubAgent(llm=llm)
    drafting_subagent = DraftingSubAgent(
        llm=llm, verifier_llm=verifier_llm, max_retries=max_draft_retries
    )

    graph = StateGraph(CaseDraftingState)
    graph.add_node("classify_case_scope", make_classify_case_scope_node(llm))
    graph.add_node("research", make_research_node(research_subagent))
    graph.add_node("evidence_review", make_evidence_review_node(evidence_subagent))
    graph.add_node("drafting", make_drafting_node(drafting_subagent))
    graph.add_node("finalize", finalize)
    graph.add_node("handoff", handoff)

    graph.set_entry_point("classify_case_scope")
    graph.add_conditional_edges(
        "classify_case_scope",
        _route_after_classify,
        {"research": "research", "handoff": "handoff"},
    )
    graph.add_conditional_edges(
        "research",
        _route_after_research,
        {"evidence_review": "evidence_review", "handoff": "handoff"},
    )
    graph.add_edge("evidence_review", "drafting")
    graph.add_conditional_edges(
        "drafting",
        _route_after_drafting,
        {"finalize": "finalize", "handoff": "handoff"},
    )
    graph.add_edge("finalize", END)
    graph.add_edge("handoff", END)

    return graph.compile()
