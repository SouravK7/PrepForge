"""
Similarity calculations.

Cosine similarity, Jaccard similarity, and other
measures used across evaluators.
"""

from __future__ import annotations

import numpy as np
from numpy.linalg import norm
from scipy.spatial.distance import cosine as scipy_cosine

from ai_core.shared.embedding_service import EmbeddingService
from ai_core.shared.text_processor import TextProcessor


class SimilarityCalculator:
    """
    Similarity calculations between texts.

    Provides cosine similarity, Jaccard similarity,
    token overlap, and other measures.
    """

    @staticmethod
    def cosine_similarity(
        text1: str,
        text2: str,
    ) -> float:
        """
        Compute cosine similarity between two texts using embeddings.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Cosine similarity score 0.0 to 1.0.
        """
        emb1 = EmbeddingService.embed_text(text1)
        emb2 = EmbeddingService.embed_text(text2)

        # Cosine similarity = 1 - cosine distance
        similarity = 1 - scipy_cosine(emb1, emb2)
        return float(max(0.0, min(1.0, similarity)))

    @staticmethod
    def jaccard_similarity(
        text1: str,
        text2: str,
    ) -> float:
        """
        Compute Jaccard similarity between two texts (token-based).

        Jaccard = |intersection| / |union|

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Jaccard similarity 0.0 to 1.0.
        """
        tokens1 = set(TextProcessor.preprocess(text1, remove_stops=False))
        tokens2 = set(TextProcessor.preprocess(text2, remove_stops=False))

        if not tokens1 and not tokens2:
            return 1.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def token_overlap(
        text1: str,
        text2: str,
    ) -> tuple[int, int, float]:
        """
        Compute token overlap between two texts.

        Args:
            text1: First text (reference).
            text2: Second text (candidate).

        Returns:
            Tuple of (overlapping_count, total_reference_tokens, overlap_ratio).
        """
        tokens1 = set(TextProcessor.preprocess(text1, remove_stops=False))
        tokens2 = set(TextProcessor.preprocess(text2, remove_stops=False))

        overlap = len(tokens1 & tokens2)
        total = len(tokens1)

        ratio = overlap / total if total > 0 else 0.0

        return overlap, total, ratio

    @staticmethod
    def concept_overlap(
        concepts: list[str],
        text: str,
    ) -> tuple[list[str], list[str], float]:
        """
        Check which concepts appear in a text.

        Args:
            concepts: List of required concepts.
            text: Text to check.

        Returns:
            Tuple of (found_concepts, missing_concepts, coverage_ratio).
        """
        text_lower = text.lower()
        found = []
        missing = []

        for concept in concepts:
            if concept.lower() in text_lower:
                found.append(concept)
            else:
                missing.append(concept)

        coverage = len(found) / len(concepts) if concepts else 0.0

        return found, missing, coverage

    @staticmethod
    def vector_similarity(
        vec1: np.ndarray,
        vec2: np.ndarray,
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity 0.0 to 1.0.
        """
        if len(vec1) == 0 or len(vec2) == 0:
            return 0.0

        norm1 = norm(vec1)
        norm2 = norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(max(0.0, min(1.0, similarity)))
