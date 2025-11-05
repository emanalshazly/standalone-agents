"""
Tests for Base Agent
"""

import pytest
from src.core.base_agent import BaseAgent, AgentContext, AgentResponse


class TestAgent(BaseAgent):
    """Test agent implementation"""

    def _define_capabilities(self):
        return ["test_capability"]

    def _get_system_prompt(self, language="en"):
        return "Test system prompt"

    def _extract_pain_points(self, query, context):
        return ["test_pain_point"]


def test_agent_initialization():
    """Test agent initialization"""
    agent = TestAgent(
        agent_name="TestAgent",
        domain="test",
        enable_rag=False,
        enable_learning=False
    )

    assert agent.agent_name == "TestAgent"
    assert agent.domain == "test"
    assert "test_capability" in agent.capabilities


def test_agent_context():
    """Test agent context creation"""
    context = AgentContext(
        user_id="user123",
        session_id="session1",
        language="en",
        domain="test"
    )

    assert context.user_id == "user123"
    assert context.language == "en"


def test_language_detection():
    """Test language detection"""
    agent = TestAgent(
        agent_name="TestAgent",
        domain="test",
        enable_rag=False,
        enable_learning=False
    )

    # Arabic text
    assert agent._detect_language("مرحبا كيف حالك") == "ar"

    # English text
    assert agent._detect_language("Hello how are you") == "en"
