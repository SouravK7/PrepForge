"""
Abstract base class for all evaluators.

Every evaluator in the ensemble extends this class.
Enforces a consistent interface across all evaluators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from schemas.answer_schema import AnswerInput


@dataclass
class DimensionScore:
    """
    Score from a single evaluator dimension.

    Attributes:
        score: Numeric score 0.0 to 100.0.
        label: Short label for this dimension.
        reason: Human-readable explanation of this score.
        evidence: Specific evidence from the answer that
                  supports this score.
    """

    score: float
    label: str
    reason: str
    evidence: list[str]


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.

    Every evaluator receives an AnswerInput and returns
    a DimensionScore for its specific dimension.
    Evaluators must not load models directly.
    Evaluators must not access the database.
    Evaluators must not contain business logic.
    """

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """
        Name of the evaluation dimension.

        Returns:
            Dimension name e.g. semantic, concept, communication.
        """
        ...

    @abstractmethod
    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Evaluate one dimension of an answer.

        Args:
            answer_input: Complete answer context including
                          question, sample answer, required concepts,
                          rubric id, and user answer text.

        Returns:
            DimensionScore with score, reason, and evidence.
        """
        ...

    def _normalize_score(self, raw: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """
        Normalize a raw score to 0-100 range.

        Args:
            raw: Raw score value.
            minimum: Minimum possible raw value.
            maximum: Maximum possible raw value.

        Returns:
            Score in 0.0 to 100.0 range.
        """
        if maximum == minimum:
            return 0.0
        normalized = (raw - minimum) / (maximum - minimum)
        return float(max(0.0, min(100.0, normalized * 100.0)))

    def _clamp(self, value: float, low: float = 0.0, high: float = 100.0) -> float:
        """
        Clamp a value to a range.

        Args:
            value: Value to clamp.
            low: Lower bound.
            high: Upper bound.

        Returns:
            Clamped value.
        """
        return float(max(low, min(high, value)))
