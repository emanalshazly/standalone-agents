"""
Tests for src/feedback/curation_pipeline.py — a real SQLite-backed review
queue, exercised end-to-end (no mocking needed, no LLM/API key required).
This replaces the deleted src/core/learning_system.py, whose pickle/JSON
"learning" had no equivalent real test coverage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.curation_pipeline import CurationPipeline


def test_submitted_correction_starts_pending(tmp_path):
    pipeline = CurationPipeline(db_path=str(tmp_path / "queue.db"))

    review_id = pipeline.submit_correction(
        query="ما هي فترة الاختبار القصوى؟",
        draft_answer="فترة الاختبار غير محدودة.",
        user_correction="فترة الاختبار لا تتجاوز ثلاثة أشهر بحسب المادة 104.",
    )

    pending = pipeline.list_pending()
    assert len(pending) == 1
    assert pending[0].id == review_id
    assert pending[0].status == "pending"
    assert pending[0].reviewer is None


def test_approve_marks_reviewed_and_removes_from_pending(tmp_path):
    pipeline = CurationPipeline(db_path=str(tmp_path / "queue.db"))
    review_id = pipeline.submit_correction(
        query="q", draft_answer="wrong", user_correction="corrected text"
    )

    pipeline.approve(
        review_id=review_id,
        reviewer="Eman Alshazly (test lawyer)",
        law_name_ar="قانون العمل رقم 14 لسنة 2025",
        law_name_en="Labor Law No. 14 of 2025",
        article_number="104",
        source_urls=["https://example.com/gazette"],
        legal_index=None,  # no vector index in this unit test
    )

    assert pipeline.list_pending() == []


def test_reject_marks_rejected_and_removes_from_pending(tmp_path):
    pipeline = CurationPipeline(db_path=str(tmp_path / "queue.db"))
    review_id = pipeline.submit_correction(
        query="q", draft_answer="wrong", user_correction="also wrong"
    )

    pipeline.reject(review_id=review_id, reviewer="reviewer", notes="not accurate either")

    assert pipeline.list_pending() == []


def test_approve_unknown_id_raises(tmp_path):
    pipeline = CurationPipeline(db_path=str(tmp_path / "queue.db"))
    try:
        pipeline.approve(
            review_id=9999,
            reviewer="x",
            law_name_ar="x",
            law_name_en="x",
            article_number="1",
            source_urls=[],
        )
        assert False, "expected ValueError for unknown review_id"
    except ValueError:
        pass
