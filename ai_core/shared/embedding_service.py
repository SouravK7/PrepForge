"""
Centralized embedding service.

All embedding generation must go through this service.
Handles model loading, caching, and batch processing.
"""

from __future__ import annotations

import numpy as np

from ai_core.shared.embedding_cache import embedding_cache
from ai_core.shared.model_manager import model_manager


class EmbeddingService:
    """
    Centralized embedding generation service.

    All embeddings must go through this service.
    Handles caching, model loading, and ensures consistency.
    """

    @staticmethod
    def embed_text(text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Checks cache first. If not cached, generates embedding,
        caches it, and returns it.

        Args:
            text: Text to embed.

        Returns:
            Embedding as numpy array of shape (384,) for all-MiniLM-L6-v2.

        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Check cache
        cached = embedding_cache.get(text)
        if cached is not None:
            return cached

        # Generate embedding
        model = model_manager.get_embedding_model()
        embedding = model.encode(text.strip(), convert_to_numpy=True)

        # Cache for future use
        embedding_cache.put(text, embedding)

        return embedding

    @staticmethod
    def embed_batch(texts: list[str]) -> list[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings.

        Raises:
            ValueError: If any text is empty.
        """
        if not texts:
            return []

        embeddings: list[np.ndarray | None] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Check which are cached
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Empty text at index {i}")

            cached = embedding_cache.get(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch embed uncached texts
        if uncached_texts:
            model = model_manager.get_embedding_model()
            uncached_embeddings = model.encode(
                uncached_texts,
                convert_to_numpy=True,
            )

            # Cache and insert uncached embeddings
            for local_idx, (orig_idx, emb) in enumerate(
                zip(uncached_indices, uncached_embeddings)
            ):
                embedding_cache.put(uncached_texts[local_idx], emb)
                embeddings[orig_idx] = emb

        return embeddings  # type: ignore[return-value]

    @staticmethod
    def cache_stats() -> dict[str, int]:
        """Get embedding cache statistics."""
        return {
            "cached_embeddings": embedding_cache.size(),
            "max_cache_size": embedding_cache.max_size,
        }

    @staticmethod
    def clear_cache() -> None:
        """Clear embedding cache. For testing only."""
        embedding_cache.clear()
