"""LangGraph-based orchestration for the Egyptian legal-literacy agent.

Replaces src/core/orchestrator.py (a plain dict lookup dressed up as
"multi-agent collaboration strategies") with a real state machine that has
actual branching logic: scope gating, a citation-verification gate that can
loop the draft back for correction or refuse to answer, and an explicit
human-handoff path.
"""

from src.graph.legal_graph import LegalAgentState, build_legal_graph

__all__ = ["LegalAgentState", "build_legal_graph"]
