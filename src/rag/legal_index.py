"""
Egyptian Legal RAG Index - فهرس الاسترجاع القانوني

Replaces the old src/core/rag_system.py. Two things were fake in the old
implementation and are real here:

1. Re-ranking used to be a hand-tuned weighted sum
   (relevance*0.7 + recency*0.2 + source_boost*0.1). Here it is a real
   cross-encoder (BAAI/bge-reranker-v2-m3, multilingual/Arabic-capable)
   run via LlamaIndex's FlagEmbeddingReranker.
2. Every retrieved chunk now carries MANDATORY citation metadata
   (law name, article number, article-number confidence, source URLs,
   verified_by_lawyer flag) instead of an optional `source: "Unknown"`
   field. src/verification/citation_verifier.py depends on this metadata
   being present and honest — a chunk with verified_by_lawyer=False must
   never be silently presented as settled law.

Two things worth knowing if you touch this file (found by actually running
the insert path end-to-end with a stub embedding, not just unit-testing
`_load_seed_nodes` in isolation, which is all the original PR's tests did):

- Chroma's flat metadata (via llama_index's `flat_metadata=True` default)
  only accepts str/int/float/None values — a raw `list[str]` for
  `source_urls` raises `ValueError` the first time a node is actually
  inserted. `source_urls` is therefore stored as a JSON string
  (`_encode_urls`/`_decode_urls`) and decoded back on retrieval.
- llama_index reconstructs a node's `.metadata` on retrieval from an
  embedded `_node_content` JSON blob (see `metadata_dict_to_node`), NOT
  from Chroma's flat metadata row directly. A naive
  `collection.update(ids=..., metadatas=[...])` to flip
  `verified_by_lawyer` would silently have no effect on what `retrieve()`
  returns. `mark_entry_verified()` instead deletes and re-inserts the
  chunks through the normal `insert_nodes` path, which rebuilds
  `_node_content` correctly.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.schema import TextNode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

try:
    from llama_index.postprocessor.flag_embedding_reranker import (
        FlagEmbeddingReranker,
    )

    _HAS_RERANKER = True
except ImportError:  # pragma: no cover - optional heavy dependency
    _HAS_RERANKER = False

import chromadb

logger = logging.getLogger(__name__)

# Bookkeeping keys llama_index adds to Chroma's flat metadata row (see
# node_to_metadata_dict) — never treat these as our own custom fields.
_BOOKKEEPING_METADATA_KEYS = {
    "_node_content",
    "_node_type",
    "document_id",
    "doc_id",
    "ref_doc_id",
}


def _encode_urls(urls: list[str]) -> str:
    """Chroma's flat metadata only accepts str/int/float/None — a raw list
    raises ValueError at insert time. Store as a JSON string instead."""
    return json.dumps(urls, ensure_ascii=False)


def _decode_urls(value) -> list[str]:
    if isinstance(value, list):  # already decoded (e.g. in tests)
        return value
    try:
        return json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return []


@dataclass
class RetrievedChunk:
    """A single retrieved knowledge chunk with mandatory citation metadata."""

    entry_id: str
    text: str
    language: str
    law_name_ar: str
    law_name_en: str
    article_number: str
    article_number_confidence: str
    source_urls: list[str]
    verified_by_lawyer: bool
    rerank_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def citation_label(self) -> str:
        """Short human-readable citation, e.g. 'Labor Law 14/2025, Art. 104'."""
        if self.article_number_confidence in (
            "no_article_number_found_in_search",
            "unconfirmed",
        ):
            return f"{self.law_name_en} (article number unconfirmed)"
        if self.article_number_confidence == "CONFLICTING_ACROSS_SOURCES":
            return f"{self.law_name_en}, Art. {self.article_number} [DISPUTED — verify]"
        return f"{self.law_name_en}, Art. {self.article_number}"


class EgyptianLegalIndex:
    """
    Thin, honest wrapper around a LlamaIndex VectorStoreIndex + reranker,
    scoped to the Egyptian legal-literacy seed corpus.
    """

    def __init__(
        self,
        persist_directory: str = "./src/knowledge/vectors/legal_eg",
        collection_name: str = "egypt_legal_literacy",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        seed_json_paths: Optional[list[str]] = None,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        default_seed_dir = (
            Path(__file__).resolve().parent.parent / "knowledge" / "legal_eg"
        )
        # Any file matching *_seed.json is picked up automatically — adding
        # a new law's seed content is a new file, not a code change here.
        self.seed_json_paths = seed_json_paths or sorted(
            str(p) for p in default_seed_dir.glob("*_seed.json")
        )

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
        # No implicit default LLM: draft generation is done explicitly by the
        # graph's draft_answer node, not silently by LlamaIndex's query engine.
        Settings.llm = None

        self._chroma_client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._chroma_client.get_or_create_collection(
            collection_name
        )
        self._vector_store = ChromaVectorStore(chroma_collection=self._collection)
        self._storage_context = StorageContext.from_defaults(
            vector_store=self._vector_store
        )

        if self._collection.count() > 0:
            logger.info(
                "Loaded existing collection with %d chunks", self._collection.count()
            )
            self._index = VectorStoreIndex.from_vector_store(self._vector_store)
            existing_entry_ids = self._get_existing_entry_ids()
        else:
            logger.info("Empty collection — building index from seed corpus")
            self._index = VectorStoreIndex([], storage_context=self._storage_context)
            existing_entry_ids = set()

        # Idempotent per-file insert: a seed file added after the collection
        # was first built only contributes entry_ids not already present —
        # dropping in a new *_seed.json is safe to run against a populated
        # collection without duplicating or rebuilding existing chunks.
        for seed_path in self.seed_json_paths:
            candidate_nodes = self._load_seed_nodes(seed_path)
            new_nodes = [
                n
                for n in candidate_nodes
                if n.metadata["entry_id"] not in existing_entry_ids
            ]
            if new_nodes:
                logger.info(
                    "Inserting %d new seed nodes from %s", len(new_nodes), seed_path
                )
                self._index.insert_nodes(new_nodes)
                existing_entry_ids.update(n.metadata["entry_id"] for n in new_nodes)

        self._reranker = None
        if _HAS_RERANKER:
            try:
                self._reranker = FlagEmbeddingReranker(
                    model=reranker_model, top_n=4
                )
            except Exception:
                logger.warning(
                    "Could not load reranker model %s — falling back to "
                    "retriever-order results without cross-encoder reranking. "
                    "This is a degraded mode, not a silent heuristic swap-in.",
                    reranker_model,
                    exc_info=True,
                )

    @staticmethod
    def _load_seed_nodes(seed_json_path: str) -> list[TextNode]:
        """
        Build one TextNode per (entry, language) so retrieval works whether
        the user asks in Arabic or English, while both nodes for an entry
        carry the SAME citation metadata (entry_id, article_number, etc.).
        """
        with open(seed_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        law = data["_meta"]["law"]
        nodes: list[TextNode] = []

        for entry in data["entries"]:
            shared_metadata = {
                "entry_id": entry["id"],
                "law_name_ar": law["name_ar"],
                "law_name_en": law["name_en"],
                "official_gazette_date": law["official_gazette_date"],
                "effective_date": law["effective_date"],
                "article_number": entry["article_number"],
                "article_number_confidence": entry["article_number_confidence"],
                "source_urls": _encode_urls(data["_meta"]["secondary_sources_consulted"]),
                "verified_by_lawyer": entry["verified_by_lawyer"],
                "topic_ar": entry["topic_ar"],
                "topic_en": entry["topic_en"],
            }

            nodes.append(
                TextNode(
                    text=entry["summary_ar"],
                    metadata={**shared_metadata, "language": "ar"},
                )
            )
            nodes.append(
                TextNode(
                    text=entry["summary_en"],
                    metadata={**shared_metadata, "language": "en"},
                )
            )

        logger.info(
            "Loaded %d seed nodes (%d entries x 2 languages) — ALL flagged "
            "verified_by_lawyer=%s pending human legal review",
            len(nodes),
            len(data["entries"]),
            {n.metadata["verified_by_lawyer"] for n in nodes},
        )
        return nodes

    def _get_existing_entry_ids(self) -> set[str]:
        result = self._collection.get(include=["metadatas"])
        return {
            m["entry_id"] for m in result["metadatas"] if m and "entry_id" in m
        }

    def retrieve(
        self,
        query: str,
        top_k_retrieve: int = 8,
        top_k_after_rerank: int = 4,
    ) -> list[RetrievedChunk]:
        """Retrieve + (if available) cross-encoder rerank chunks for a query."""
        retriever = VectorIndexRetriever(
            index=self._index, similarity_top_k=top_k_retrieve
        )
        nodes_with_scores = retriever.retrieve(query)

        if self._reranker is not None:
            self._reranker.top_n = top_k_after_rerank
            nodes_with_scores = self._reranker.postprocess_nodes(
                nodes_with_scores, query_str=query
            )
        else:
            nodes_with_scores = nodes_with_scores[:top_k_after_rerank]

        results: list[RetrievedChunk] = []
        for nws in nodes_with_scores:
            md = nws.node.metadata
            results.append(
                RetrievedChunk(
                    entry_id=md["entry_id"],
                    text=nws.node.get_content(),
                    language=md["language"],
                    law_name_ar=md["law_name_ar"],
                    law_name_en=md["law_name_en"],
                    article_number=md["article_number"],
                    article_number_confidence=md["article_number_confidence"],
                    source_urls=_decode_urls(md["source_urls"]),
                    verified_by_lawyer=md["verified_by_lawyer"],
                    rerank_score=float(nws.score) if nws.score is not None else 0.0,
                    metadata=md,
                )
            )
        return results

    def add_verified_chunk(
        self,
        entry_id: str,
        text: str,
        language: str,
        law_name_ar: str,
        law_name_en: str,
        article_number: str,
        source_urls: list[str],
        reviewer: str,
    ) -> None:
        """
        Add a chunk that a human reviewer has approved (via
        src/feedback/curation_pipeline.py). This is the ONLY path by which
        `verified_by_lawyer=True` chunks enter the index — never set from
        model output directly.
        """
        node = TextNode(
            text=text,
            metadata={
                "entry_id": entry_id,
                "language": language,
                "law_name_ar": law_name_ar,
                "law_name_en": law_name_en,
                "article_number": article_number,
                "article_number_confidence": "lawyer_verified",
                "source_urls": _encode_urls(source_urls),
                "verified_by_lawyer": True,
                "reviewer": reviewer,
            },
        )
        self._index.insert_nodes([node])
        logger.info(
            "Inserted lawyer-verified chunk entry_id=%s reviewer=%s",
            entry_id,
            reviewer,
        )

    def mark_entry_verified(
        self, entry_id: str, reviewer: str, source_urls: list[str]
    ) -> int:
        """
        Confirm an EXISTING seed entry (both ar+en chunks) as reviewed and
        correct as written — distinct from `add_verified_chunk`, which
        models a user/lawyer proposing NEW or CORRECTED text via
        src/feedback/curation_pipeline.py. Routing a plain "yes, this is
        right" confirmation through that flow would pollute the review
        queue with fake corrections; this method is the honest, separate
        path for that case.

        Implementation note: this deletes and re-inserts the matching
        chunks rather than calling `collection.update()` on their metadata
        in place. llama_index reconstructs a node's `.metadata` on
        retrieval from an embedded `_node_content` JSON blob, not from
        Chroma's flat metadata row — a flat-only update would silently not
        change what `retrieve()` returns. Delete+reinsert goes through the
        same `insert_nodes` path the rest of this class already uses, which
        rebuilds `_node_content` correctly.
        """
        matches = self._collection.get(
            where={"entry_id": entry_id}, include=["metadatas", "documents"]
        )
        if not matches["ids"]:
            logger.warning(
                "mark_entry_verified: no chunks found for entry_id=%s", entry_id
            )
            return 0

        self._collection.delete(ids=matches["ids"])

        new_nodes = []
        for text, old_metadata in zip(matches["documents"], matches["metadatas"]):
            custom_metadata = {
                k: v
                for k, v in old_metadata.items()
                if k not in _BOOKKEEPING_METADATA_KEYS
            }
            custom_metadata["verified_by_lawyer"] = True
            custom_metadata["reviewer"] = reviewer
            custom_metadata["article_number_confidence"] = "lawyer_verified"
            custom_metadata["source_urls"] = _encode_urls(source_urls)
            new_nodes.append(TextNode(text=text, metadata=custom_metadata))

        self._index.insert_nodes(new_nodes)
        logger.info(
            "Marked %d chunk(s) verified_by_lawyer=True for entry_id=%s (reviewer=%s)",
            len(new_nodes),
            entry_id,
            reviewer,
        )
        return len(new_nodes)
