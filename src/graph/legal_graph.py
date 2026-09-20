"""
Legal Agent Graph - رسم بياني الوكيل القانوني

Replaces src/core/orchestrator.py and src/core/base_agent.py's linear
query() flow with a real LangGraph StateGraph:

    classify_intent -> [out of scope?] -> handoff
                     -> retrieve -> [no sources?] -> handoff
                                  -> draft_answer -> verify_citations
                                       ^                  |
                                       |--- retry <=2 ----| [unsupported?]
                                                           v
                                                   [still unsupported?] -> handoff
                                                           |
                                                      add_disclaimer -> END

Every branch is an explicit conditional edge, not a dict lookup. The
citation-verification gate can send the draft back for correction, and can
ultimately refuse to answer rather than emit an unverified claim — this is
the architectural core of the whole pivot (see src/verification/).
"""

from __future__ import annotations

import json
import logging
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.rag.legal_index import EgyptianLegalIndex, RetrievedChunk
from src.verification.citation_verifier import VerificationResult, verify_draft

logger = logging.getLogger(__name__)

MAX_DRAFT_RETRIES = 2

IN_SCOPE_TOPICS = [
    "employment_contracts",
    "labor_rights",
    "rental_and_lease_contracts",
    "consumer_contracts",
    "basic_civil_contract_terms",
]
OUT_OF_SCOPE_TOPICS = [
    "criminal_law",
    "litigation_strategy",
    "court_filings",
    "tax_law",
]

_SCOPE_JUDGE_SYSTEM_PROMPT = f"""أنت مصنّف نطاق لوكيل قانوني يجيب فقط عن أسئلة "محو الأمية القانونية" البسيطة \
للأفراد والشركات الصغيرة في مصر، ضمن هذه المواضيع فقط: {IN_SCOPE_TOPICS}.
هذا الوكيل ممنوع صراحة من الإجابة على: {OUT_OF_SCOPE_TOPICS}، وممنوع من صياغة استراتيجية تقاضي \
أو تمثيل قانوني رسمي.
أجب حصراً بصيغة JSON: {{"in_scope": true|false, "language": "ar"|"en", "reason": "سبب موجز"}}."""


class LegalAgentState(TypedDict, total=False):
    query: str
    language: str
    in_scope: bool
    scope_reason: str
    retrieved_chunks: list[RetrievedChunk]
    draft_answer: str
    draft_retry_count: int
    last_verification_feedback: str
    verification: Optional[VerificationResult]
    final_answer: str
    handoff_required: bool
    handoff_reason: str
    lawyer_review_pending: bool


def _detect_language_heuristic(text: str) -> str:
    """Cheap script-based detection — no confidence theater, just counting
    Arabic-range characters, same approach as the old base_agent.py but
    used only for a UI default, never presented as a correctness signal."""
    arabic_chars = sum(1 for c in text if "؀" <= c <= "ۿ")
    return "ar" if arabic_chars > len(text) * 0.3 else "en"


def make_classify_intent_node(llm):
    def classify_intent(state: LegalAgentState) -> dict:
        from langchain_core.messages import HumanMessage, SystemMessage

        query = state["query"]
        language = _detect_language_heuristic(query)

        messages = [
            SystemMessage(content=_SCOPE_JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]
        response = llm.invoke(messages)
        raw = getattr(response, "content", str(response))
        try:
            parsed = json.loads(raw)
            in_scope = bool(parsed.get("in_scope", False))
            reason = parsed.get("reason", "")
            language = parsed.get("language", language)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Scope classifier returned non-JSON, defaulting to out_of_scope: %r", raw)
            in_scope, reason = False, "scope classifier failed to parse — defaulting to safe refusal"

        return {"language": language, "in_scope": in_scope, "scope_reason": reason}

    return classify_intent


def make_retrieve_node(legal_index: EgyptianLegalIndex):
    def retrieve(state: LegalAgentState) -> dict:
        chunks = legal_index.retrieve(state["query"])
        return {"retrieved_chunks": chunks}

    return retrieve


def make_draft_answer_node(llm):
    def draft_answer(state: LegalAgentState) -> dict:
        from langchain_core.messages import HumanMessage, SystemMessage

        chunks = state["retrieved_chunks"]
        language = state.get("language", "ar")
        retry_feedback = state.get("last_verification_feedback", "")

        sources_block = "\n".join(
            f"[{i+1}] ({c.citation_label}) {c.text}" for i, c in enumerate(chunks)
        )

        system_prompt = (
            "أنت مساعد لمحو الأمية القانونية في مصر. اكتب إجابة بلغة بسيطة تعتمد حصراً على "
            "المصادر المرقّمة أدناه. كل جملة تحتوي على معلومة قانونية (رقم، مدة، شرط) يجب أن "
            "تنتهي بعلامة استشهاد مثل [1] تشير إلى رقم المصدر المستخدم. لا تضف أي معلومة غير "
            "موجودة في المصادر. إذا كانت المصادر غير كافية للإجابة، قل ذلك صراحة بدل التخمين."
            if language == "ar"
            else "You are an Egyptian legal-literacy assistant. Write a plain-language answer "
            "based ONLY on the numbered sources below. Every sentence containing a legal fact "
            "(a number, a duration, a condition) MUST end with a citation marker like [1] "
            "pointing to the source used. Do not add any information not present in the "
            "sources. If the sources are insufficient, say so explicitly instead of guessing."
        )

        if retry_feedback:
            system_prompt += (
                f"\n\nمحاولة سابقة فشلت التحقق منها للسبب التالي، صحّح ذلك: {retry_feedback}"
                if language == "ar"
                else f"\n\nA previous attempt failed verification for this reason, fix it: {retry_feedback}"
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"المصادر:\n{sources_block}\n\nسؤال المستخدم: {state['query']}"
                if language == "ar"
                else f"Sources:\n{sources_block}\n\nUser question: {state['query']}"
            ),
        ]
        response = llm.invoke(messages)
        draft = getattr(response, "content", str(response))

        return {
            "draft_answer": draft,
            "draft_retry_count": state.get("draft_retry_count", 0) + 1,
        }

    return draft_answer


def make_verify_citations_node(llm):
    def verify_citations(state: LegalAgentState) -> dict:
        result = verify_draft(
            draft_text=state["draft_answer"],
            retrieved_chunks=state["retrieved_chunks"],
            llm=llm,
        )
        feedback_parts = []
        for uncited in result.uncited_claims:
            feedback_parts.append(f"uncited claim: '{uncited[:120]}'")
        for claim in result.claims:
            if not claim.supported:
                feedback_parts.append(
                    f"unsupported claim '{claim.sentence[:120]}': {claim.verdict_detail}"
                )

        return {
            "verification": result,
            "last_verification_feedback": "; ".join(feedback_parts),
        }

    return verify_citations


def add_disclaimer(state: LegalAgentState) -> dict:
    language = state.get("language", "ar")
    verification: VerificationResult = state["verification"]

    lawyer_review_banner = ""
    if verification.any_unverified_lawyer_review:
        lawyer_review_banner = (
            "\n\n⚠️ تنبيه: المعلومات أعلاه مبنية على مصادر ثانوية (تحليلات قانونية) ولم "
            "يراجعها محامٍ مصري مرخّص بعد مقارنةً بنص الجريدة الرسمية. لا تعتمد عليها في "
            "قرار قانوني نهائي دون مراجعة محامٍ."
            if language == "ar"
            else "\n\n⚠️ Note: the information above is based on secondary legal-analysis "
            "sources and has not yet been reviewed by a licensed Egyptian lawyer against "
            "the primary Official Gazette text. Do not rely on it for a final legal "
            "decision without a lawyer's review."
        )

    standard_disclaimer = (
        "\n\nهذه المعلومات لا تُغني عن استشارة محامٍ مرخّص وليست بديلاً عن التمثيل القانوني."
        if language == "ar"
        else "\n\nThis information is not a substitute for consulting a licensed lawyer "
        "and does not constitute legal representation."
    )

    final_answer = state["draft_answer"] + standard_disclaimer + lawyer_review_banner
    return {
        "final_answer": final_answer,
        "lawyer_review_pending": verification.any_unverified_lawyer_review,
        "handoff_required": False,
    }


def handoff(state: LegalAgentState) -> dict:
    language = state.get("language", "ar")
    reason = state.get("handoff_reason", state.get("scope_reason", ""))

    if language == "ar":
        message = (
            "لا يمكن لهذا الوكيل الإجابة على هذا السؤال بثقة كافية "
            f"({reason}). يُرجى التواصل مع محامٍ مرخّص لمناقشة حالتك."
        )
    else:
        message = (
            "This agent cannot answer this question with sufficient confidence "
            f"({reason}). Please consult a licensed lawyer about your situation."
        )
    return {"final_answer": message, "handoff_required": True}


def _route_after_classify(state: LegalAgentState) -> str:
    return "retrieve" if state.get("in_scope") else "handoff"


def _route_after_retrieve(state: LegalAgentState) -> str:
    chunks = state.get("retrieved_chunks") or []
    if not chunks:
        return "handoff"
    return "draft_answer"


def _route_after_verify(state: LegalAgentState) -> str:
    verification: VerificationResult = state["verification"]
    if verification.all_supported:
        return "add_disclaimer"
    if state.get("draft_retry_count", 0) < MAX_DRAFT_RETRIES:
        return "draft_answer"
    return "handoff"


def build_legal_graph(legal_index: EgyptianLegalIndex, llm, verifier_llm=None):
    """
    Compile the LangGraph app. `llm` drafts and classifies scope;
    `verifier_llm` (defaults to `llm`) runs the citation entailment checks —
    kept separate so a cheaper/more deterministic model can be used for
    verification if desired.
    """
    verifier_llm = verifier_llm or llm

    graph = StateGraph(LegalAgentState)
    graph.add_node("classify_intent", make_classify_intent_node(llm))
    graph.add_node("retrieve", make_retrieve_node(legal_index))
    graph.add_node("draft_answer", make_draft_answer_node(llm))
    graph.add_node("verify_citations", make_verify_citations_node(verifier_llm))
    graph.add_node("add_disclaimer", add_disclaimer)
    graph.add_node("handoff", handoff)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {"retrieve": "retrieve", "handoff": "handoff"},
    )
    graph.add_conditional_edges(
        "retrieve",
        _route_after_retrieve,
        {"draft_answer": "draft_answer", "handoff": "handoff"},
    )
    graph.add_edge("draft_answer", "verify_citations")
    graph.add_conditional_edges(
        "verify_citations",
        _route_after_verify,
        {
            "add_disclaimer": "add_disclaimer",
            "draft_answer": "draft_answer",
            "handoff": "handoff",
        },
    )
    graph.add_edge("add_disclaimer", END)
    graph.add_edge("handoff", END)

    return graph.compile()
