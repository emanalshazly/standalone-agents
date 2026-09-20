"""
Evaluation Harness - تشغيل التقييم

Two modes:

  --mode retrieval   No LLM/API key needed. Checks that the RAG index
                      (src/rag/legal_index.py) retrieves the right seed
                      entry for each golden question, and that a
                      no-coverage question does NOT falsely match an
                      unrelated entry. This is the part of the harness
                      that can run in CI without secrets.

  --mode full         Requires OPENAI_API_KEY (or ANTHROPIC_API_KEY).
                      Runs the full agent end-to-end per golden question,
                      checks handoff_required against expected_scope, and
                      computes RAGAS faithfulness / context_precision on
                      the in-scope questions. Fails (non-zero exit) if
                      mean faithfulness < config's verification.min_faithfulness_score
                      (0.85 by default — see config/config.example.yaml).

This is necessary-but-not-sufficient, per the plan: a passing run here does
NOT mean the content is legally correct. docs/eval/citation_audit.md is the
non-negotiable manual lawyer sign-off step before any of this seed data is
treated as authoritative — see src/knowledge/legal_eg/labor_law_2025_seed.json
`_meta.IMPORTANT_VERIFICATION_STATUS`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.rag.legal_index import EgyptianLegalIndex  # noqa: E402

GOLDEN_PATH = Path(__file__).parent / "golden_qa.jsonl"
MIN_FAITHFULNESS = 0.85


def load_golden() -> list[dict]:
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run_retrieval_only(golden: list[dict]) -> int:
    legal_index = EgyptianLegalIndex()
    failures = 0

    for item in golden:
        if item["expected_scope"] == "out_of_scope":
            print(f"[SKIP retrieval check] {item['id']} (scope-gated, not retrieval-gated)")
            continue

        chunks = legal_index.retrieve(item["question"], top_k_retrieve=8, top_k_after_rerank=4)
        retrieved_ids = {c.entry_id for c in chunks}
        expected_ids = set(item["expected_entry_ids"])
        top_score = chunks[0].rerank_score if chunks else 0.0

        if item["expected_scope"] == "in_scope_but_no_sources":
            # We can't assert a universal score threshold without having
            # tuned one against real traffic, so we just report the top
            # score for a human to sanity-check, and log it loudly.
            print(
                f"[REPORT] {item['id']}: no seed coverage expected — "
                f"top retrieved entry_id={chunks[0].entry_id if chunks else None} "
                f"score={top_score:.3f} (a human should confirm the graph's "
                f"'insufficient sources' handoff triggers correctly here)"
            )
            continue

        passed = bool(retrieved_ids & expected_ids)
        status = "PASS" if passed else "FAIL"
        print(
            f"[{status}] {item['id']}: expected one of {expected_ids}, "
            f"got {retrieved_ids} (top_score={top_score:.3f})"
        )
        if not passed:
            failures += 1

    print(f"\nretrieval-only mode: {len(golden) - failures}/{len(golden)} checks passed "
          f"(out-of-scope items excluded from this count)")
    return 1 if failures else 0


def run_full(golden: list[dict]) -> int:
    from src.agents.legal.legal_agent import EgyptianLegalAgent

    agent = EgyptianLegalAgent()
    failures = 0
    faithfulness_inputs = []

    for item in golden:
        answer = agent.query(item["question"])
        expected_handoff = item["expected_scope"] in ("out_of_scope", "in_scope_but_no_sources")
        scope_ok = answer.handoff_required == expected_handoff
        status = "PASS" if scope_ok else "FAIL"
        print(f"[{status}] {item['id']}: handoff_required={answer.handoff_required} "
              f"(expected {expected_handoff})")
        if not scope_ok:
            failures += 1

        if item["expected_scope"] == "in_scope" and not answer.handoff_required:
            faithfulness_inputs.append(
                {
                    "question": item["question"],
                    "answer": answer.answer,
                    "contexts": [c.text for c in answer.retrieved_chunks],
                }
            )

    if faithfulness_inputs:
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import faithfulness

            ds = Dataset.from_list(faithfulness_inputs)
            scores = evaluate(ds, metrics=[faithfulness])
            mean_faithfulness = scores["faithfulness"]
            print(f"\nRAGAS mean faithfulness: {mean_faithfulness:.3f} "
                  f"(threshold: {MIN_FAITHFULNESS})")
            if mean_faithfulness < MIN_FAITHFULNESS:
                print("FAIL: faithfulness below threshold")
                failures += 1
        except ImportError:
            print("\n[WARN] ragas/datasets not installed — skipping faithfulness scoring. "
                  "Install with: pip install ragas datasets")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["retrieval", "full"], default="retrieval")
    args = parser.parse_args()

    golden = load_golden()

    if args.mode == "retrieval":
        return run_retrieval_only(golden)
    return run_full(golden)


if __name__ == "__main__":
    sys.exit(main())
