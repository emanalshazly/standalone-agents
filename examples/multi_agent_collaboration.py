"""
Multi-Agent Collaboration Example - مثال التعاون بين الوكلاء
Demonstrates how multiple agents work together to solve complex queries
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import AgentOrchestrator, CollaborationStrategy
from src.core.base_agent import AgentContext
from src.agents.medical.medical_agent import MedicalAgent
from src.agents.finance.finance_agent import FinanceAgent
from src.agents.legal.legal_agent import LegalAgent


def example_consensus_collaboration():
    """Example: Multiple agents reaching consensus"""
    print("\n" + "=" * 70)
    print("🤝 Consensus Collaboration Example")
    print("=" * 70 + "\n")

    # Initialize orchestrator
    orchestrator = AgentOrchestrator(max_workers=3)

    # Register agents
    medical = MedicalAgent()
    finance = FinanceAgent()

    orchestrator.register_agent(
        agent_name="medical",
        agent=medical,
        domains=["medical", "health"]
    )

    orchestrator.register_agent(
        agent_name="finance",
        agent=finance,
        domains=["finance", "money"]
    )

    # Complex query requiring both domains
    context = AgentContext(
        user_id="user123",
        session_id="collab1",
        language="ar"
    )

    query = "كيف أخطط مالياً لتكاليف علاج مرض مزمن؟"

    print(f"Query: {query}")
    print("\n(This query requires both medical and finance expertise)\n")

    response = orchestrator.collaborative_query(
        user_query=query,
        context=context,
        required_agents=["medical", "finance"],
        strategy=CollaborationStrategy.CONSENSUS
    )

    print(f"Strategy: {response.collaboration_strategy}")
    print(f"Contributing Agents: {', '.join(response.contributing_agents)}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"\nCombined Response:\n{response.primary_response}")


def example_hierarchical_collaboration():
    """Example: Lead agent coordinating others"""
    print("\n" + "=" * 70)
    print("📊 Hierarchical Collaboration Example")
    print("=" * 70 + "\n")

    orchestrator = AgentOrchestrator()

    # Register agents
    legal = LegalAgent()
    finance = FinanceAgent()

    orchestrator.register_agent("legal", legal, domains=["legal"])
    orchestrator.register_agent("finance", finance, domains=["finance"])

    context = AgentContext(
        user_id="user456",
        session_id="hier1",
        language="ar"
    )

    query = "ما هي الجوانب المالية والقانونية لبدء مشروع صغير؟"

    print(f"Query: {query}\n")

    response = orchestrator.collaborative_query(
        user_query=query,
        context=context,
        required_agents=["legal", "finance"],
        strategy=CollaborationStrategy.HIERARCHICAL
    )

    print(f"Lead Agent: {response.metadata.get('lead_agent')}")
    print(f"\nSynthesized Response:\n{response.primary_response}")


def example_parallel_collaboration():
    """Example: Agents working in parallel"""
    print("\n" + "=" * 70)
    print("⚡ Parallel Collaboration Example")
    print("=" * 70 + "\n")

    orchestrator = AgentOrchestrator(enable_parallel=True)

    medical = MedicalAgent()
    finance = FinanceAgent()
    legal = LegalAgent()

    orchestrator.register_agent("medical", medical)
    orchestrator.register_agent("finance", finance)
    orchestrator.register_agent("legal", legal)

    context = AgentContext(
        user_id="user789",
        session_id="parallel1",
        language="en"
    )

    query = "I need comprehensive advice on managing my health insurance benefits"

    print(f"Query: {query}\n")
    print("Processing in parallel with multiple agents...\n")

    response = orchestrator.collaborative_query(
        user_query=query,
        context=context,
        required_agents=["medical", "finance", "legal"],
        strategy=CollaborationStrategy.PARALLEL
    )

    print(f"Agents involved: {len(response.contributing_agents)}")
    print("\nResponses from each agent:")
    print("-" * 70)

    for agent_name, agent_response in response.agent_responses.items():
        print(f"\n## {agent_name}:")
        print(f"{agent_response.content[:300]}...")
        print(f"Confidence: {agent_response.confidence:.2f}")


def main():
    """Run all collaboration examples"""
    print("\n" + "=" * 70)
    print("🤖 Multi-Agent Collaboration Examples")
    print("Revolutionary agent cooperation for complex problems")
    print("=" * 70)

    try:
        example_consensus_collaboration()
        example_hierarchical_collaboration()
        example_parallel_collaboration()

        print("\n" + "=" * 70)
        print("✅ All collaboration examples completed!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
