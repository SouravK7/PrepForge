"""
Semantic evaluator.

Measures how semantically similar the user's answer is
to the reference sample answer using sentence embeddings.
"""

from __future__ import annotations

from ai_core.evaluation_pipeline.base_evaluator import BaseEvaluator, DimensionScore
from ai_core.shared.similarity import SimilarityCalculator
from schemas.answer_schema import AnswerInput


class SemanticEvaluator(BaseEvaluator):
    """
    Evaluates semantic similarity between user answer and sample answer.

    Uses Sentence Transformers to compute cosine similarity.
    A high score means the user's answer conveys similar meaning
    to the reference answer, not just identical words.
    """

    @property
    def dimension_name(self) -> str:
        """Dimension name for this evaluator."""
        return "semantic"

    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Compute semantic similarity between user answer and sample answer.

        Args:
            answer_input: Contains user_answer and sample_answer.

        Returns:
            DimensionScore with similarity score and explanation.
        """
        user_answer = answer_input.user_answer.strip()
        sample_answer = answer_input.sample_answer.strip()

        # Compute cosine similarity via embeddings
        similarity = SimilarityCalculator.cosine_similarity(
            user_answer,
            sample_answer,
        )

        # Convert to 0-100 score
        score = self._clamp(similarity * 100.0)

        # Also compute token overlap for additional context
        _, _, token_ratio = SimilarityCalculator.token_overlap(
            sample_answer,
            user_answer,
        )

        # Build explanation
        reason, evidence = self._build_explanation(score, similarity, token_ratio)

        return DimensionScore(
            score=round(score, 2),
            label="Semantic Relevance",
            reason=reason,
            evidence=evidence,
        )

    def _build_explanation(
        self,
        score: float,
        similarity: float,
        token_ratio: float,
    ) -> tuple[str, list[str]]:
        """
        Build human-readable explanation for the semantic score.

        Args:
            score: Final score 0-100.
            similarity: Raw cosine similarity 0.0-1.0.
            token_ratio: Token overlap ratio.

        Returns:
            Tuple of (reason text, evidence list).
        """
        evidence = [
            f"Cosine similarity with reference answer: {similarity:.2%}",
            f"Token overlap with reference answer: {token_ratio:.2%}",
        ]

        if score >= 85:
            reason = (
                "Your answer is highly relevant and conveys meaning very "
                "similar to the reference answer. The core ideas are well "
                "captured and expressed clearly."
            )
        elif score >= 70:
            reason = (
                "Your answer is relevant and covers the main idea, "
                "but some aspects of the reference answer are not "
                "fully addressed. Consider deepening your response."
            )
        elif score >= 50:
            reason = (
                "Your answer is partially relevant. It touches on some "
                "correct points but misses key aspects of the expected "
                "answer. Review the topic more thoroughly."
            )
        elif score >= 30:
            reason = (
                "Your answer has limited relevance to the question. "
                "The response veers off-topic or addresses a different "
                "aspect than what was asked."
            )
        else:
            reason = (
                "Your answer does not align well with the expected response. "
                "It may be too brief, off-topic, or missing the core concept "
                "the question was targeting."
            )

        return reason, evidence
