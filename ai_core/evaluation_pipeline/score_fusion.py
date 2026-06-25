"""
Score fusion engine.

Combines scores from all evaluators using config-driven weights.
Different weight profiles for technical vs HR questions.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
from ai_core.shared.config_loader import config
from schemas.evaluation_schema import (
    EvaluationScores,
    GradeEnum,
    ReadinessEnum,
)
from schemas.question_schema import QuestionType


@dataclass
class FusionInput:
    """
    All dimension scores ready for fusion.

    Attributes:
        semantic: Score from SemanticEvaluator.
        concept: Score from ConceptEvaluator.
        communication: Score from CommunicationEvaluator.
        evidence: Score from EvidenceEvaluator.
        reasoning: Score from ReasoningEvaluator.
        question_type: technical or hr (determines weight profile).
    """

    semantic: DimensionScore
    concept: DimensionScore
    communication: DimensionScore
    evidence: DimensionScore
    reasoning: DimensionScore
    question_type: QuestionType


class ScoreFusion:
    """
    Combines individual evaluator scores into a final weighted score.

    Weight profiles are loaded from configs/scoring_weights.yaml.
    No weights are hardcoded in this file.
    Technical and HR questions use different weight profiles.
    """

    def __init__(self) -> None:
        """Load weight profiles from config."""
        self._technical_weights = self._load_weights("technical")
        self._hr_weights = self._load_weights("hr")
        self._grade_boundaries = self._load_grades()
        self._readiness_boundaries = self._load_readiness()

    def _load_weights(self, profile: str) -> dict[str, float]:
        """
        Load scoring weights for a profile.

        Args:
            profile: "technical" or "hr".

        Returns:
            Dictionary of dimension name to weight.
        """
        weights = {
            "semantic": config.get_float(
                "scoring_weights", f"{profile}.semantic", 0.2
            ),
            "concept": config.get_float(
                "scoring_weights", f"{profile}.concept", 0.35
            ),
            "communication": config.get_float(
                "scoring_weights", f"{profile}.communication", 0.15
            ),
            "evidence": config.get_float(
                "scoring_weights", f"{profile}.evidence", 0.15
            ),
            "reasoning": config.get_float(
                "scoring_weights", f"{profile}.reasoning", 0.15
            ),
        }

        # Validate weights sum to approximately 1.0
        total = sum(weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(
                f"Scoring weights for '{profile}' must sum to 1.0, got {total:.3f}"
            )

        return weights

    def _load_grades(self) -> dict[str, float]:
        """Load grade boundaries from config."""
        return {
            "A": config.get_float("scoring_weights", "grades.A", 90.0),
            "B": config.get_float("scoring_weights", "grades.B", 75.0),
            "C": config.get_float("scoring_weights", "grades.C", 60.0),
            "D": config.get_float("scoring_weights", "grades.D", 40.0),
        }

    def _load_readiness(self) -> dict[str, float]:
        """Load readiness boundaries from config."""
        return {
            "excellent": config.get_float("scoring_weights", "readiness.excellent", 85.0),
            "good": config.get_float("scoring_weights", "readiness.good", 70.0),
            "average": config.get_float("scoring_weights", "readiness.average", 50.0),
        }

    def fuse(self, fusion_input: FusionInput) -> EvaluationScores:
        """
        Combine all dimension scores into a weighted final score.

        Args:
            fusion_input: All dimension scores and question type.

        Returns:
            EvaluationScores with all scores and weighted final.
        """
        weights = (
            self._technical_weights
            if fusion_input.question_type == QuestionType.TECHNICAL
            else self._hr_weights
        )

        weighted_final = (
            fusion_input.semantic.score * weights["semantic"]
            + fusion_input.concept.score * weights["concept"]
            + fusion_input.communication.score * weights["communication"]
            + fusion_input.evidence.score * weights["evidence"]
            + fusion_input.reasoning.score * weights["reasoning"]
        )

        return EvaluationScores(
            semantic=fusion_input.semantic.score,
            concept=fusion_input.concept.score,
            communication=fusion_input.communication.score,
            evidence=fusion_input.evidence.score,
            reasoning=fusion_input.reasoning.score,
            weighted_final=round(weighted_final, 2),
        )

    def get_grade(self, weighted_final: float) -> GradeEnum:
        """
        Map a weighted final score to a letter grade.

        Args:
            weighted_final: Score 0-100.

        Returns:
            GradeEnum letter grade A through F.
        """
        if weighted_final >= self._grade_boundaries["A"]:
            return GradeEnum.A
        elif weighted_final >= self._grade_boundaries["B"]:
            return GradeEnum.B
        elif weighted_final >= self._grade_boundaries["C"]:
            return GradeEnum.C
        elif weighted_final >= self._grade_boundaries["D"]:
            return GradeEnum.D
        else:
            return GradeEnum.F

    def get_readiness(self, weighted_final: float) -> ReadinessEnum:
        """
        Map a weighted final score to a readiness level.

        Args:
            weighted_final: Score 0-100.

        Returns:
            ReadinessEnum qualitative readiness level.
        """
        if weighted_final >= self._readiness_boundaries["excellent"]:
            return ReadinessEnum.EXCELLENT
        elif weighted_final >= self._readiness_boundaries["good"]:
            return ReadinessEnum.GOOD
        elif weighted_final >= self._readiness_boundaries["average"]:
            return ReadinessEnum.AVERAGE
        else:
            return ReadinessEnum.POOR
