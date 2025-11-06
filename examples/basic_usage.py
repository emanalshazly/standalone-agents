"""
Basic Usage Examples - أمثلة الاستخدام الأساسية
Demonstrates basic agent usage across different domains
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.medical.medical_agent import MedicalAgent
from src.agents.legal.legal_agent import LegalAgent
from src.agents.finance.finance_agent import FinanceAgent
from src.core.base_agent import AgentContext


def example_medical_agent():
    """Example: Using Medical Agent"""
    print("\n" + "=" * 50)
    print("🏥 Medical Agent Example")
    print("=" * 50 + "\n")

    # Initialize agent
    agent = MedicalAgent()

    # Arabic query
    context_ar = AgentContext(
        user_id="user123",
        session_id="session1",
        language="ar",
        domain="medical"
    )

    response = agent.query(
        "ما هي أعراض مرض السكري؟",
        context=context_ar
    )

    print("Question (Arabic): ما هي أعراض مرض السكري؟")
    print(f"\nResponse:\n{response.content}")
    print(f"\nConfidence: {response.confidence:.2f}")
    print(f"Sources: {len(response.sources)}")

    # English query
    context_en = AgentContext(
        user_id="user123",
        session_id="session2",
        language="en",
        domain="medical"
    )

    response = agent.query(
        "What are the symptoms of diabetes?",
        context=context_en
    )

    print("\n" + "-" * 50)
    print("Question (English): What are the symptoms of diabetes?")
    print(f"\nResponse:\n{response.content}")
    print(f"\nConfidence: {response.confidence:.2f}")


def example_finance_agent():
    """Example: Using Finance Agent"""
    print("\n" + "=" * 50)
    print("💰 Finance Agent Example")
    print("=" * 50 + "\n")

    agent = FinanceAgent()

    context = AgentContext(
        user_id="user456",
        session_id="finance1",
        language="ar",
        domain="finance"
    )

    response = agent.query(
        "كيف أبدأ في الادخار الشهري؟",
        context=context
    )

    print("Question: كيف أبدأ في الادخار الشهري؟")
    print(f"\nResponse:\n{response.content}")
    print(f"\nConfidence: {response.confidence:.2f}")


def example_legal_agent():
    """Example: Using Legal Agent"""
    print("\n" + "=" * 50)
    print("⚖️ Legal Agent Example")
    print("=" * 50 + "\n")

    agent = LegalAgent()

    context = AgentContext(
        user_id="user789",
        session_id="legal1",
        language="ar",
        domain="legal"
    )

    response = agent.query(
        "ما هي حقوقي في عقد العمل؟",
        context=context
    )

    print("Question: ما هي حقوقي في عقد العمل؟")
    print(f"\nResponse:\n{response.content}")
    print(f"\nConfidence: {response.confidence:.2f}")


def example_with_feedback():
    """Example: Learning from feedback"""
    print("\n" + "=" * 50)
    print("🎯 Learning from Feedback Example")
    print("=" * 50 + "\n")

    agent = MedicalAgent()

    context = AgentContext(
        user_id="user999",
        session_id="feedback1",
        language="en",
        domain="medical"
    )

    # Initial query
    query = "How to manage stress?"
    response = agent.query(query, context)

    print(f"Query: {query}")
    print(f"Response: {response.content[:200]}...")

    # Provide feedback
    feedback = {
        "rating": 4.5,
        "text": "Very helpful!",
        "corrections": None
    }

    agent.learn_from_feedback(
        query=query,
        response=response.content,
        feedback=feedback
    )

    print("\n✓ Feedback recorded for continuous learning")

    # Check learning insights
    if agent.learning_system:
        insights = agent.learning_system.get_learning_insights()
        print(f"\nLearning Stats:")
        print(f"- Total interactions: {insights['total_interactions']}")
        print(f"- Average rating: {insights['feedback_stats']['average_rating']:.2f}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("🤖 Standalone Domain Agents - Usage Examples")
    print("=" * 70)

    # Note: Set your API keys before running
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️ WARNING: OPENAI_API_KEY not set!")
        print("Set it using: export OPENAI_API_KEY='your-key-here'")
        print("\nRunning examples with mock responses...\n")

    try:
        example_medical_agent()
        example_finance_agent()
        example_legal_agent()
        example_with_feedback()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure to set your API keys and install dependencies.")


if __name__ == "__main__":
    main()
