"""
Elo-style skill estimation engine.

Adapts interview question difficulty based on demonstrated
competency performance using an Elo rating system.

Formula:
    expected = 1 / (1 + 10 ^ ((question_elo - skill_elo) / 400))
    new_skill_elo = old_elo + K * (actual - expected)

Where:
    expected = probability of performing well on this question
    actual   = normalized answer score (0.0 to 1.0)
    K        = sensitivity factor (32 by default)
"""

from __future__ import annotations

from ai_core.shared.config_loader import config
from schemas.competency_schema import CompetencyScore, CompetencyUpdate
from schemas.question_schema import DifficultyLevel


class EloEstimator:
    """
    Adaptive difficulty estimator using Elo rating system.

    Used by:
        - QuestionSelector to choose appropriate difficulty
        - ConfidenceUpdater to update Elo after each answer
    """

    def __init__(self) -> None:
        """Load Elo constants from config."""
        self._k_factor = config.get_float(
            "app_config", "elo.k_factor", 32.0
        )
        self._default_rating = config.get_float(
            "app_config", "elo.default_user_rating", 1000.0
        )
        self._beginner_rating = config.get_float(
            "app_config", "elo.beginner_question_rating", 900.0
        )
        self._intermediate_rating = config.get_float(
            "app_config", "elo.intermediate_question_rating", 1200.0
        )
        self._advanced_rating = config.get_float(
            "app_config", "elo.advanced_question_rating", 1500.0
        )
        self._expert_rating = config.get_float(
            "app_config", "elo.expert_question_rating", 1800.0
        )
        self._advanced_threshold = config.get_float(
            "app_config", "elo.advanced_threshold", 1400.0
        )
        self._intermediate_threshold = config.get_float(
            "app_config", "elo.intermediate_threshold", 1100.0
        )

    def compute_expected_score(
        self,
        skill_elo: float,
        question_elo: float,
    ) -> float:
        """
        Compute expected performance probability.

        The expected score represents the probability that
        a user with this skill Elo will perform well on
        a question with this difficulty Elo.

        Args:
            skill_elo: User's current Elo rating for this competency.
            question_elo: Question's difficulty Elo rating.

        Returns:
            Expected score 0.0 to 1.0.
        """
        exponent = (question_elo - skill_elo) / 400.0
        expected = 1.0 / (1.0 + 10.0 ** exponent)
        return float(expected)

    def update_elo(
        self,
        current_score: CompetencyScore,
        question_elo: float,
        actual_performance: float,
    ) -> tuple[float, float]:
        """
        Update user Elo rating after answering a question.

        Args:
            current_score: User's current competency score with Elo.
            question_elo: Difficulty Elo of the answered question.
            actual_performance: Normalized answer score 0.0-1.0.

        Returns:
            Tuple of (new_elo, elo_delta).
        """
        old_elo = current_score.elo_rating

        expected = self.compute_expected_score(old_elo, question_elo)

        # Elo update formula
        new_elo = old_elo + self._k_factor * (actual_performance - expected)

        # Keep Elo in reasonable bounds
        new_elo = float(max(400.0, min(2500.0, new_elo)))
        elo_delta = round(new_elo - old_elo, 2)

        return round(new_elo, 2), elo_delta

    def recommend_difficulty(
        self,
        skill_elo: float,
    ) -> DifficultyLevel:
        """
        Recommend question difficulty based on current skill Elo.

        Args:
            skill_elo: User's current Elo rating for this competency.

        Returns:
            Recommended DifficultyLevel.
        """
        if skill_elo >= self._advanced_threshold:
            return DifficultyLevel.ADVANCED
        elif skill_elo >= self._intermediate_threshold:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.BEGINNER

    def difficulty_to_elo(self, difficulty: DifficultyLevel) -> float:
        """
        Convert difficulty label to Elo rating.

        Args:
            difficulty: Question difficulty level.

        Returns:
            Corresponding Elo rating.
        """
        mapping = {
            DifficultyLevel.BEGINNER: self._beginner_rating,
            DifficultyLevel.INTERMEDIATE: self._intermediate_rating,
            DifficultyLevel.ADVANCED: self._advanced_rating,
            DifficultyLevel.EXPERT: self._expert_rating,
        }
        return mapping.get(difficulty, self._intermediate_rating)

    def elo_to_difficulty_label(self, elo: float) -> str:
        """
        Convert Elo rating to human-readable difficulty label.

        Args:
            elo: Elo rating value.

        Returns:
            Human-readable difficulty description.
        """
        if elo >= self._advanced_threshold:
            return "Advanced"
        elif elo >= self._intermediate_threshold:
            return "Intermediate"
        else:
            return "Beginner"

    def compute_readiness_percentage(
        self,
        skill_elo: float,
        target_elo: float = 1300.0,
    ) -> float:
        """
        Compute interview readiness as a percentage.

        Readiness is defined as how close the user's skill Elo
        is to the target role competency Elo.

        Args:
            skill_elo: User's current Elo rating.
            target_elo: Target Elo for role readiness.

        Returns:
            Readiness percentage 0.0 to 100.0.
        """
        min_elo = self._default_rating
        percentage = (skill_elo - min_elo) / (target_elo - min_elo) * 100.0
        return float(max(0.0, min(100.0, percentage)))

    def should_increase_difficulty(
        self,
        recent_scores: list[float],
        threshold: float = 0.75,
    ) -> bool:
        """
        Decide if difficulty should increase based on recent performance.

        Args:
            recent_scores: Last N normalized scores (0.0-1.0).
            threshold: Score average above which difficulty increases.

        Returns:
            True if difficulty should increase.
        """
        if not recent_scores:
            return False
        avg = sum(recent_scores) / len(recent_scores)
        return avg >= threshold

    def should_decrease_difficulty(
        self,
        recent_scores: list[float],
        threshold: float = 0.40,
    ) -> bool:
        """
        Decide if difficulty should decrease based on recent performance.

        Args:
            recent_scores: Last N normalized scores (0.0-1.0).
            threshold: Score average below which difficulty decreases.

        Returns:
            True if difficulty should decrease.
        """
        if not recent_scores:
            return False
        avg = sum(recent_scores) / len(recent_scores)
        return avg <= threshold
