"""
Embedding cache to avoid recomputing embeddings.

Sentence Transformers are expensive. Cache embeddings
in memory to avoid recomputation within a session.
"""

from __future__ import annotations

import hashlib
from typing import Optional

import numpy as np


class EmbeddingCache:
    """
    In-memory embedding cache.

    Caches embeddings by text hash to avoid recomputing
    identical embeddings within a session or across sessions.
    """

    def __init__(self, max_size: int = 10000) -> None:
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of cached embeddings.
        """
        self.max_size = max_size
        self._cache: dict[str, np.ndarray] = {}

    def _hash_text(self, text: str) -> str:
        """
        Hash text to create cache key.

        Args:
            text: Text to hash.

        Returns:
            Hex hash of the text.
        """
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for text.

        Args:
            text: Text to lookup.

        Returns:
            Cached embedding if exists, None otherwise.
        """
        key = self._hash_text(text)
        return self._cache.get(key)

    def put(self, text: str, embedding: np.ndarray) -> None:
        """
        Cache an embedding.

        If cache is full, the oldest entry is discarded (simple FIFO).

        Args:
            text: Original text.
            embedding: Computed embedding vector.
        """
        if len(self._cache) >= self.max_size:
            # Simple FIFO: remove first (oldest) key
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        key = self._hash_text(text)
        self._cache[key] = embedding

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._cache = {}

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def contains(self, text: str) -> bool:
        """Check if text is cached."""
        key = self._hash_text(text)
        return key in self._cache


# Global cache instance
embedding_cache = EmbeddingCache()
