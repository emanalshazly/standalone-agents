"""Case-assistant (drafting + evidence review) agent — separate track from
src/agents/legal/ (the plain-language literacy agent). See
PROJECT_OVERVIEW.md "Two-track architecture" for why."""

from src.agents.case_assistant.drafting_agent import CaseAssistantAgent, CaseDraftAnswer

__all__ = ["CaseAssistantAgent", "CaseDraftAnswer"]
