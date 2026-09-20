"""
Tests for EgyptianLegalIndex's seed-JSON parsing and metadata-encoding
logic, tested in isolation from the embedding model / vector store (which
need a model download and are covered by tests/eval/run_eval.py
--mode retrieval instead, since that requires network access this unit
test suite should not depend on).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.legal_index import EgyptianLegalIndex, _decode_urls, _encode_urls

SEED_DIR = Path(__file__).parent.parent / "src" / "knowledge" / "legal_eg"
LABOR_SEED_PATH = str(SEED_DIR / "labor_law_2025_seed.json")
RENTAL_SEED_PATH = str(SEED_DIR / "rental_law_2025_seed.json")
CONSUMER_SEED_PATH = str(SEED_DIR / "consumer_protection_2018_seed.json")

ALL_SEED_PATHS = [LABOR_SEED_PATH, RENTAL_SEED_PATH, CONSUMER_SEED_PATH]
EXPECTED_ENTRY_COUNTS = {
    LABOR_SEED_PATH: 7,
    RENTAL_SEED_PATH: 6,
    CONSUMER_SEED_PATH: 6,
}


def test_seed_produces_two_nodes_per_entry():
    nodes = EgyptianLegalIndex._load_seed_nodes(LABOR_SEED_PATH)
    entry_ids = {n.metadata["entry_id"] for n in nodes}

    # 7 entries in the seed file x 2 languages (ar, en) each
    assert len(entry_ids) == 7
    assert len(nodes) == 14


def test_every_seed_node_is_flagged_unverified():
    """Every seed entry MUST be verified_by_lawyer=False — only
    src/feedback/curation_pipeline.py's approve() path or
    EgyptianLegalIndex.mark_entry_verified() may set this True.
    A regression here would silently present unreviewed AI-compiled legal
    summaries as lawyer-verified, which is the exact failure mode this
    project's citation-verification architecture exists to prevent."""
    for path in ALL_SEED_PATHS:
        nodes = EgyptianLegalIndex._load_seed_nodes(path)
        assert all(n.metadata["verified_by_lawyer"] is False for n in nodes), path


def test_every_seed_node_has_mandatory_citation_fields():
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
    for path in ALL_SEED_PATHS:
        nodes = EgyptianLegalIndex._load_seed_nodes(path)
        for node in nodes:
            missing = required_fields - node.metadata.keys()
            assert not missing, f"{path}: node {node.metadata.get('entry_id')} missing {missing}"
            assert node.metadata["source_urls"], "source_urls must not be empty"
            # source_urls must be JSON-encoded (a raw list crashes Chroma's
            # flat-metadata insert — see legal_index.py module docstring)
            assert isinstance(node.metadata["source_urls"], str)
            decoded = json.loads(node.metadata["source_urls"])
            assert isinstance(decoded, list) and decoded


def test_disputed_notice_period_entry_is_flagged():
    """The notice-period entry has a known article-number conflict across
    secondary sources (156 vs 123) — this must remain visibly flagged so
    the citation label surfaces it (see RetrievedChunk.citation_label)."""
    nodes = EgyptianLegalIndex._load_seed_nodes(LABOR_SEED_PATH)
    notice_nodes = [n for n in nodes if n.metadata["entry_id"] == "notice_period_indefinite"]
    assert notice_nodes
    assert all(
        n.metadata["article_number_confidence"] == "CONFLICTING_ACROSS_SOURCES"
        for n in notice_nodes
    )


def test_all_three_seed_files_load_with_expected_entry_counts():
    """Each *_seed.json file loads independently and produces the expected
    number of distinct entries (x2 for ar/en) — this is what the multi-file
    loader in EgyptianLegalIndex.__init__ iterates over."""
    for path, expected_entries in EXPECTED_ENTRY_COUNTS.items():
        nodes = EgyptianLegalIndex._load_seed_nodes(path)
        entry_ids = {n.metadata["entry_id"] for n in nodes}
        assert len(entry_ids) == expected_entries, path
        assert len(nodes) == expected_entries * 2, path


def test_default_seed_glob_finds_all_three_seed_files():
    """EgyptianLegalIndex.__init__ defaults seed_json_paths to a glob of
    *_seed.json in the knowledge dir when none is passed explicitly — this
    checks that glob actually resolves to all three files on disk, without
    instantiating the full class (which needs the embedding model)."""
    found = sorted(str(p) for p in SEED_DIR.glob("*_seed.json"))
    assert sorted(ALL_SEED_PATHS) == found


def test_entry_ids_are_unique_across_all_seed_files():
    """entry_id is used as the idempotency key in EgyptianLegalIndex.__init__
    and as the lookup key in mark_entry_verified — a collision across two
    different laws' seed files would silently merge unrelated content."""
    seen: dict[str, str] = {}
    for path in ALL_SEED_PATHS:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data["entries"]:
            entry_id = entry["id"]
            assert entry_id not in seen, (
                f"duplicate entry_id {entry_id!r} in {path} and {seen.get(entry_id)}"
            )
            seen[entry_id] = path


def test_encode_decode_urls_round_trip():
    urls = ["https://example.com/a", "https://example.com/b"]
    encoded = _encode_urls(urls)
    assert isinstance(encoded, str)
    assert _decode_urls(encoded) == urls


def test_decode_urls_handles_already_decoded_list():
    """Defensive: some call sites (tests, future refactors) might pass an
    already-decoded list rather than a JSON string — must not crash."""
    assert _decode_urls(["https://example.com"]) == ["https://example.com"]


def test_decode_urls_handles_garbage_gracefully():
    assert _decode_urls("not valid json") == []
    assert _decode_urls(None) == []
    assert _decode_urls("") == []
