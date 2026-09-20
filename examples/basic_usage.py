"""
Basic Usage Example - Egyptian Legal-Literacy Agent

Requires OPENAI_API_KEY (or ANTHROPIC_API_KEY with llm_provider="anthropic")
and network access to download the embedding/reranker models on first run.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.legal.legal_agent import EgyptianLegalAgent


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY before running this example.")
        return

    agent = EgyptianLegalAgent()

    questions = [
        "هل يجوز لصاحب العمل تجديد فترة الاختبار؟",
        "How many days of annual leave am I entitled to in my second year?",
        "هل يمكن للوكيل مساعدتي في قضية جنائية؟",  # out-of-scope, should hand off
    ]

    for q in questions:
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        answer = agent.query(q)
        print(f"\nA: {answer.answer}")
        print(f"\nhandoff_required={answer.handoff_required}  "
              f"lawyer_review_pending={answer.lawyer_review_pending}")
        if answer.citations:
            print("Citations:")
            for c in answer.citations:
                print(f"  - {c}")


if __name__ == "__main__":
    main()
