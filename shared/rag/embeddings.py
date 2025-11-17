"""
Embedding generation utilities
"""

import logging
from typing import List, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for text using various models

    Supports:
    - OpenAI embeddings
    - Sentence Transformers
    - Custom fine-tuned models
    - Caching for efficiency
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_enabled: bool = True
    ):
        """
        Initialize embedding generator

        Args:
            model_name: Name of embedding model
            cache_enabled: Whether to cache embeddings
        """
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, List[float]] = {}
        self.dimension = 384  # Default for all-MiniLM-L6-v2

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        # Check cache
        if self.cache_enabled and text in self._cache:
            return self._cache[text]

        # Generate embedding (placeholder)
        embedding = self._generate_embedding(text)

        # Cache result
        if self.cache_enabled:
            self._cache[text] = embedding

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if self.cache_enabled and text in self._cache:
                embeddings.append(self._cache[text])
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = self._generate_embeddings_batch(uncached_texts)

            # Insert into results and cache
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings[idx] = embedding
                if self.cache_enabled:
                    self._cache[texts[idx]] = embedding

        return embeddings

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using model"""

        # Placeholder implementation
        # In production, would use actual embedding model
        logger.debug(f"Generating embedding for text of length {len(text)}")

        # Return random vector for demonstration
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(self.dimension).tolist()

    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch"""

        logger.info(f"Generating embeddings for batch of {len(texts)} texts")

        # Placeholder - in production would use batch processing
        return [self._generate_embedding(text) for text in texts]

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between -1 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""

        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self._cache),
            "model_name": self.model_name,
            "dimension": self.dimension
        }

    def clear_cache(self):
        """Clear embedding cache"""
        self._cache.clear()
        logger.info("Embedding cache cleared")
