"""LangGraph-based orchestration.

Two separate graphs, deliberately not merged into one (see
PROJECT_OVERVIEW.md "Two-track architecture"):

  legal_graph.py         -> plain-language legal-literacy Q&A (lower risk)
  case_drafting_graph.py -> case-assistant drafting/evidence-review track
                             (higher risk: research loop with live web
                             search, evidence gap analysis, document
                             drafting — always DRAFT-ONLY, never filed)
"""

from src.graph.legal_graph import LegalAgentState, build_legal_graph
from src.graph.case_drafting_graph import CaseDraftingState, build_case_drafting_graph

__all__ = [
    "LegalAgentState",
    "build_legal_graph",
    "CaseDraftingState",
    "build_case_drafting_graph",
]
