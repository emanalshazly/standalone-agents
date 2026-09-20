"""
Sub-agents for the case-assistant / drafting track.

These are NOT used by the plain-language legal-literacy agent
(src/agents/legal/) — that agent keeps its simple, single-pass,
local-KB-only retrieval on purpose (see src/rag/legal_index.py docstring).

Sub-agents here are composed by src/graph/case_drafting_graph.py:

    research_subagent   -> iterative (ReAct-style) retrieval, local KB + web
    evidence_review_subagent -> checks user-supplied case facts against
                                 research results, flags gaps
    drafting_subagent   -> assembles a draft document, DRAFT-ONLY, always
                            citation-verified before being returned
"""

from src.subagents.research_subagent import ResearchResult, ResearchSubAgent
from src.subagents.evidence_review_subagent import (
    EvidenceReviewResult,
    EvidenceReviewSubAgent,
)
from src.subagents.drafting_subagent import DraftingResult, DraftingSubAgent

__all__ = [
    "ResearchResult",
    "ResearchSubAgent",
    "EvidenceReviewResult",
    "EvidenceReviewSubAgent",
    "DraftingResult",
    "DraftingSubAgent",
]
