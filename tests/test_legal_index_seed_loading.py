"""
Tests for EgyptianLegalIndex._load_seed_nodes — the seed-JSON parsing logic,
tested in isolation from the embedding model / vector store (which need a
model download and are covered by tests/eval/run_eval.py --mode retrieval
instead, since that requires network access this unit test suite should not
depend on).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.legal_index import EgyptianLegalIndex

SEED_PATH = str(
    Path(__file__).parent.parent
    / "src"
    / "knowledge"
    / "legal_eg"
    / "labor_law_2025_seed.json"
)


def test_seed_produces_two_nodes_per_entry():
    nodes = EgyptianLegalIndex._load_seed_nodes(SEED_PATH)
    entry_ids = {n.metadata["entry_id"] for n in nodes}

    # 7 entries in the seed file x 2 languages (ar, en) each
    assert len(entry_ids) == 7
    assert len(nodes) == 14


def test_every_seed_node_is_flagged_unverified():
    """Every seed entry MUST be verified_by_lawyer=False — only
    src/feedback/curation_pipeline.py's approve() path may set this True.
    A regression here would silently present unreviewed AI-compiled legal
    summaries as lawyer-verified, which is the exact failure mode this
    project's citation-verification architecture exists to prevent."""
    nodes = EgyptianLegalIndex._load_seed_nodes(SEED_PATH)
    assert all(n.metadata["verified_by_lawyer"] is False for n in nodes)


def test_every_seed_node_has_mandatory_citation_fields():
    nodes = EgyptianLegalIndex._load_seed_nodes(SEED_PATH)
    required_fields = {
        "entry_id",
        "law_name_ar",
        "law_name_en",
        "article_number",
        "article_number_confidence",
        "source_urls",
        "verified_by_lawyer",
        "language",
    }
    for node in nodes:
        missing = required_fields - node.metadata.keys()
        assert not missing, f"node {node.metadata.get('entry_id')} missing {missing}"
        assert node.metadata["source_urls"], "source_urls must not be empty"


def test_disputed_notice_period_entry_is_flagged():
    """The notice-period entry has a known article-number conflict across
    secondary sources (156 vs 123) — this must remain visibly flagged so
    the citation label surfaces it (see RetrievedChunk.citation_label)."""
    nodes = EgyptianLegalIndex._load_seed_nodes(SEED_PATH)
    notice_nodes = [n for n in nodes if n.metadata["entry_id"] == "notice_period_indefinite"]
    assert notice_nodes
    assert all(
        n.metadata["article_number_confidence"] == "CONFLICTING_ACROSS_SOURCES"
        for n in notice_nodes
    )
