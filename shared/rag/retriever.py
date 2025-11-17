"""
Hybrid retrieval strategies
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """Search mode options"""
    DENSE = "dense"  # Vector/semantic search
    SPARSE = "sparse"  # BM25/keyword search
    HYBRID = "hybrid"  # Combination


@dataclass
class SearchResult:
    """Search result representation"""
    content: str
    doc_id: str
    chunk_id: str
    score: float
    metadata: Dict[str, Any]
    search_mode: SearchMode


class HybridRetriever:
    """
    Hybrid retrieval combining dense and sparse search

    Features:
    - Dense vector search for semantic similarity
    - Sparse BM25 search for keyword matching
    - Reciprocal Rank Fusion for result merging
    - Configurable ranking strategies
    """

    def __init__(
        self,
        vector_store,
        keyword_index,
        alpha: float = 0.5
    ):
        """
        Initialize hybrid retriever

        Args:
            vector_store: Vector database for dense search
            keyword_index: Index for sparse search (e.g., BM25)
            alpha: Weight for combining scores (0=sparse, 1=dense)
        """
        self.vector_store = vector_store
        self.keyword_index = keyword_index
        self.alpha = alpha

    async def search(
        self,
        query: str,
        top_k: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Execute hybrid search

        Args:
            query: Search query
            top_k: Number of results to return
            mode: Search mode
            filters: Metadata filters

        Returns:
            List of search results
        """
        if mode == SearchMode.DENSE:
            return await self._dense_search(query, top_k, filters)

        elif mode == SearchMode.SPARSE:
            return await self._sparse_search(query, top_k, filters)

        else:  # HYBRID
            dense_results = await self._dense_search(query, top_k * 2, filters)
            sparse_results = await self._sparse_search(query, top_k * 2, filters)

            # Merge using Reciprocal Rank Fusion
            merged = self._reciprocal_rank_fusion(
                dense_results,
                sparse_results,
                top_k
            )

            return merged

    async def _dense_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform dense vector search"""

        logger.debug(f"Dense search for: {query}")

        # Placeholder implementation
        # In production, would query actual vector store
        results = [
            SearchResult(
                content=f"Dense result {i} for: {query}",
                doc_id=f"doc_{i}",
                chunk_id=f"chunk_{i}",
                score=0.9 - (i * 0.1),
                metadata={"search_type": "dense"},
                search_mode=SearchMode.DENSE
            )
            for i in range(min(top_k, 5))
        ]

        return results

    async def _sparse_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform sparse keyword search"""

        logger.debug(f"Sparse search for: {query}")

        # Placeholder implementation
        # In production, would use BM25 or similar
        results = [
            SearchResult(
                content=f"Sparse result {i} for: {query}",
                doc_id=f"doc_{i+10}",
                chunk_id=f"chunk_{i+10}",
                score=0.85 - (i * 0.1),
                metadata={"search_type": "sparse"},
                search_mode=SearchMode.SPARSE
            )
            for i in range(min(top_k, 5))
        ]

        return results

    def _reciprocal_rank_fusion(
        self,
        results1: List[SearchResult],
        results2: List[SearchResult],
        top_k: int,
        k: int = 60
    ) -> List[SearchResult]:
        """
        Merge results using Reciprocal Rank Fusion

        RRF Score = sum(1 / (k + rank_i)) for each list

        Args:
            results1: First result list
            results2: Second result list
            top_k: Number of final results
            k: RRF constant (typically 60)

        Returns:
            Merged and ranked results
        """
        scores: Dict[str, tuple[SearchResult, float]] = {}

        # Calculate RRF scores
        for rank, result in enumerate(results1, 1):
            key = result.chunk_id
            score = 1.0 / (k + rank)

            if key in scores:
                scores[key] = (result, scores[key][1] + score)
            else:
                scores[key] = (result, score)

        for rank, result in enumerate(results2, 1):
            key = result.chunk_id
            score = 1.0 / (k + rank)

            if key in scores:
                scores[key] = (scores[key][0], scores[key][1] + score)
            else:
                scores[key] = (result, score)

        # Sort by RRF score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x[1],
            reverse=True
        )

        # Update scores and return top_k
        final_results = []
        for result, rrf_score in sorted_results[:top_k]:
            result.score = rrf_score
            result.search_mode = SearchMode.HYBRID
            final_results.append(result)

        return final_results

    def _weighted_combination(
        self,
        results1: List[SearchResult],
        results2: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        Merge results using weighted score combination

        Args:
            results1: Dense search results
            results2: Sparse search results
            top_k: Number of final results

        Returns:
            Merged results
        """
        scores: Dict[str, tuple[SearchResult, float]] = {}

        # Combine with weights
        for result in results1:
            key = result.chunk_id
            weighted_score = result.score * self.alpha
            scores[key] = (result, weighted_score)

        for result in results2:
            key = result.chunk_id
            weighted_score = result.score * (1 - self.alpha)

            if key in scores:
                combined_score = scores[key][1] + weighted_score
                scores[key] = (scores[key][0], combined_score)
            else:
                scores[key] = (result, weighted_score)

        # Sort and return
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x[1],
            reverse=True
        )

        final_results = []
        for result, score in sorted_results[:top_k]:
            result.score = score
            result.search_mode = SearchMode.HYBRID
            final_results.append(result)

        return final_results
