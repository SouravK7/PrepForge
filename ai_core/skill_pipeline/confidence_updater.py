"""
Competency confidence updater.

Updates competency confidence scores after each evaluation
using an exponential moving average formula. Also propagates
partial confidence updates to parent competencies.
"""

from __future__ import annotations

from datetime import datetime

from ai_core.shared.ai_logger import ai_logger
from ai_core.shared.config_loader import config
from schemas.competency_schema import CompetencyScore, CompetencyUpdate


class ConfidenceUpdater:
    """
    Updates competency confidence scores after each answer evaluation.

    Uses an exponential moving average:
        new_confidence = old + learning_rate * (score - old)

    A score above 0.5 increases confidence.
    A score below 0.5 decreases it.
    The learning rate controls how quickly confidence changes.
    """

    def __init__(self) -> None:
        """Load configuration."""
        self._learning_rate = config.get_float(
            "app_config", "competency.learning_rate", 0.3
        )
        self._min_confidence = config.get_float(
            "app_config", "competency.min_confidence", 0.0
        )
        self._max_confidence = config.get_float(
            "app_config", "competency.max_confidence", 1.0
        )

    def update(
        self,
        current_score: CompetencyScore,
        evaluation_score: float,
    ) -> tuple[CompetencyScore, CompetencyUpdate]:
        """
        Update a competency confidence score after one evaluation.

        Args:
            current_score: The user's current competency score record.
            evaluation_score: The weighted final score from evaluation 0-100.

        Returns:
            Tuple of (updated CompetencyScore, CompetencyUpdate record).
        """
        # Normalize evaluation score to 0.0-1.0
        normalized_score = evaluation_score / 100.0

        old_confidence = current_score.confidence
        old_elo = current_score.elo_rating

        # Exponential moving average update
        new_confidence = old_confidence + self._learning_rate * (
            normalized_score - old_confidence
        )
        new_confidence = self._clamp_confidence(new_confidence)

        delta = round(new_confidence - old_confidence, 4)
        new_evidence_count = current_score.evidence_count + 1

        # Build improvement trend over last 3 updates
        improvement_trend = self._compute_trend(
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            current_trend=current_score.improvement_trend,
        )

        # Build updated score record
        updated_score = CompetencyScore(
            user_id=current_score.user_id,
            competency_id=current_score.competency_id,
            confidence=round(new_confidence, 4),
            elo_rating=old_elo,  # Elo updated separately by EloEstimator
            evidence_count=new_evidence_count,
            last_assessed=datetime.utcnow(),
            improvement_trend=improvement_trend,
        )

        # Build update record
        update_record = CompetencyUpdate(
            competency_id=current_score.competency_id,
            old_confidence=old_confidence,
            new_confidence=round(new_confidence, 4),
            old_elo=old_elo,
            new_elo=old_elo,
            evidence_added=f"Evaluation score: {evaluation_score:.1f}/100",
            delta=delta,
        )

        # Log decision
        ai_logger.log_competency_update(
            user_id=current_score.user_id,
            competency_id=current_score.competency_id,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            delta=delta,
        )

        return updated_score, update_record

    def update_from_delta(
        self,
        current_score: CompetencyScore,
        competency_delta: float,
    ) -> tuple[CompetencyScore, CompetencyUpdate]:
        """
        Apply a pre-computed competency delta directly.

        Used when the EvaluationOrchestrator has already
        computed the delta and we just need to apply it.

        Args:
            current_score: Current competency score.
            competency_delta: Pre-computed delta from evaluation.

        Returns:
            Tuple of (updated CompetencyScore, CompetencyUpdate).
        """
        old_confidence = current_score.confidence
        new_confidence = self._clamp_confidence(
            old_confidence + competency_delta
        )

        delta = round(new_confidence - old_confidence, 4)

        improvement_trend = self._compute_trend(
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            current_trend=current_score.improvement_trend,
        )

        updated_score = CompetencyScore(
            user_id=current_score.user_id,
            competency_id=current_score.competency_id,
            confidence=round(new_confidence, 4),
            elo_rating=current_score.elo_rating,
            evidence_count=current_score.evidence_count + 1,
            last_assessed=datetime.utcnow(),
            improvement_trend=improvement_trend,
        )

        update_record = CompetencyUpdate(
            competency_id=current_score.competency_id,
            old_confidence=old_confidence,
            new_confidence=round(new_confidence, 4),
            old_elo=current_score.elo_rating,
            new_elo=current_score.elo_rating,
            evidence_added=f"Delta applied: {competency_delta:+.4f}",
            delta=delta,
        )

        ai_logger.log_competency_update(
            user_id=current_score.user_id,
            competency_id=current_score.competency_id,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            delta=delta,
        )

        return updated_score, update_record

    def create_initial_score(
        self,
        user_id: int,
        competency_id: str,
    ) -> CompetencyScore:
        """
        Create an initial competency score for a new user-competency pair.

        Args:
            user_id: User identifier.
            competency_id: Competency identifier.

        Returns:
            Initial CompetencyScore with zero confidence.
        """
        return CompetencyScore(
            user_id=user_id,
            competency_id=competency_id,
            confidence=0.0,
            elo_rating=config.get_float(
                "app_config", "elo.default_user_rating", 1000.0
            ),
            evidence_count=0,
            last_assessed=None,
            improvement_trend=0.0,
        )

    def _compute_trend(
        self,
        old_confidence: float,
        new_confidence: float,
        current_trend: float,
    ) -> float:
        """
        Compute improvement trend using exponential smoothing.

        Args:
            old_confidence: Previous confidence.
            new_confidence: Updated confidence.
            current_trend: Current running trend.

        Returns:
            Updated trend value. Positive means improving.
        """
        instant_delta = new_confidence - old_confidence
        smoothing = 0.5
        new_trend = smoothing * instant_delta + (1 - smoothing) * current_trend
        return round(new_trend, 4)

    def _clamp_confidence(self, value: float) -> float:
        """
        Clamp confidence to valid range.

        Args:
            value: Raw confidence value.

        Returns:
            Clamped value between min and max confidence.
        """
        return float(max(
            self._min_confidence,
            min(self._max_confidence, value)
        ))
