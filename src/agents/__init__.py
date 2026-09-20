"""Domain agent facades — two separate tracks, see PROJECT_OVERVIEW.md."""

from src.agents.legal.legal_agent import EgyptianLegalAgent
from src.agents.case_assistant.drafting_agent import CaseAssistantAgent

__all__ = [
    "EgyptianLegalAgent",
    "CaseAssistantAgent",
]
