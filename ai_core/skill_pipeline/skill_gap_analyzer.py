"""
Skill gap analyzer.

Identifies competency gaps between a user's current confidence
scores and the target confidence required for role readiness.
Outputs prioritized gap list for the recommendation engine.
"""

from __future__ import annotations

from ai_core.shared.config_loader import config
from schemas.competency_schema import (
    Competency,
    CompetencyGap,
    CompetencyScore,
    PriorityEnum,
)


class SkillGapAnalyzer:
    """
    Identifies and prioritizes skill gaps for a user.

    Compares current competency confidence scores against
    the target readiness threshold and ranks gaps by
    both size and role relevance.
    """

    def __init__(self) -> None:
        """Load thresholds from config."""
        self._readiness_threshold = config.get_float(
            "app_config", "competency.readiness_threshold", 0.7
        )
        self._high_priority_threshold = config.get_float(
            "app_config", "skill_gap.high_priority_threshold", 0.4
        )
        self._medium_priority_threshold = config.get_float(
            "app_config", "skill_gap.medium_priority_threshold", 0.2
        )

    def analyze(
        self,
        competencies: list[Competency],
        competency_scores: dict[str, CompetencyScore],
        target_role: str,
        min_relevance: float = 0.3,
    ) -> list[CompetencyGap]:
        """
        Analyze all competencies and return prioritized gap list.

        Args:
            competencies: All competency definitions for this role.
            competency_scores: Map of competency_id to CompetencyScore.
            target_role: Job role for relevance weighting.
            min_relevance: Minimum role relevance to include.

        Returns:
            List of CompetencyGap sorted by weighted priority descending.
        """
        gaps: list[CompetencyGap] = []

        for competency in competencies:
            role_relevance = competency.role_relevance.get(target_role, 0.0)

            if role_relevance < min_relevance:
                continue

            score = competency_scores.get(competency.id)
            current_confidence = score.confidence if score else 0.0

            gap = max(0.0, self._readiness_threshold - current_confidence)

            if gap <= 0.001:
                # Competency already at or above readiness threshold
                continue

            priority = self._compute_priority(gap, role_relevance)
            action = self._generate_action(competency, current_confidence, gap)

            competency_gap = CompetencyGap(
                competency_id=competency.id,
                competency_name=competency.name,
                current_confidence=round(current_confidence, 3),
                required_confidence=self._readiness_threshold,
                gap=round(gap, 3),
                priority=priority,
                role_relevance=role_relevance,
                recommended_action=action,
            )
            gaps.append(competency_gap)

        # Sort by weighted priority: gap * role_relevance
        gaps.sort(
            key=lambda g: g.gap * g.role_relevance,
            reverse=True,
        )

        return gaps

    def analyze_single(
        self,
        competency: Competency,
        score: CompetencyScore | None,
        target_role: str,
    ) -> CompetencyGap | None:
        """
        Analyze gap for a single competency.

        Args:
            competency: Competency definition.
            score: User's current score for this competency.
            target_role: Target job role.

        Returns:
            CompetencyGap if gap exists, None if at or above threshold.
        """
        role_relevance = competency.role_relevance.get(target_role, 0.0)
        current_confidence = score.confidence if score else 0.0
        gap = max(0.0, self._readiness_threshold - current_confidence)

        if gap <= 0.001:
            return None

        priority = self._compute_priority(gap, role_relevance)
        action = self._generate_action(competency, current_confidence, gap)

        return CompetencyGap(
            competency_id=competency.id,
            competency_name=competency.name,
            current_confidence=round(current_confidence, 3),
            required_confidence=self._readiness_threshold,
            gap=round(gap, 3),
            priority=priority,
            role_relevance=role_relevance,
            recommended_action=action,
        )

    def get_critical_gaps(
        self,
        gaps: list[CompetencyGap],
    ) -> list[CompetencyGap]:
        """
        Filter only high-priority gaps.

        Args:
            gaps: All identified gaps.

        Returns:
            Only high-priority gaps.
        """
        return [g for g in gaps if g.priority == PriorityEnum.HIGH]

    def get_quick_wins(
        self,
        gaps: list[CompetencyGap],
        max_gap: float = 0.25,
    ) -> list[CompetencyGap]:
        """
        Identify competencies close to readiness threshold.

        Quick wins are competencies where the user is nearly ready
        and a small improvement will make them interview-ready.

        Args:
            gaps: All identified gaps.
            max_gap: Maximum gap to be considered a quick win.

        Returns:
            Gaps that are quick wins sorted by gap ascending.
        """
        quick_wins = [g for g in gaps if g.gap <= max_gap]
        return sorted(quick_wins, key=lambda g: g.gap)

    def compute_overall_readiness(
        self,
        competencies: list[Competency],
        competency_scores: dict[str, CompetencyScore],
        target_role: str,
    ) -> float:
        """
        Compute overall interview readiness as a percentage.

        Weighted average of competency confidence scores,
        weighted by role relevance.

        Args:
            competencies: All competency definitions.
            competency_scores: Map of competency_id to score.
            target_role: Target job role.

        Returns:
            Readiness percentage 0.0 to 100.0.
        """
        total_weight = 0.0
        weighted_confidence = 0.0

        for competency in competencies:
            role_relevance = competency.role_relevance.get(target_role, 0.0)
            if role_relevance < 0.3:
                continue

            score = competency_scores.get(competency.id)
            confidence = score.confidence if score else 0.0

            weighted_confidence += confidence * role_relevance
            total_weight += role_relevance

        if total_weight == 0:
            return 0.0

        readiness = (weighted_confidence / total_weight) * 100.0
        return round(float(min(100.0, readiness)), 2)

    def _compute_priority(
        self,
        gap: float,
        role_relevance: float,
    ) -> PriorityEnum:
        """
        Compute gap priority from gap size and role relevance.

        Args:
            gap: Confidence gap 0.0-1.0.
            role_relevance: Role relevance weight 0.0-1.0.

        Returns:
            PriorityEnum level.
        """
        weighted = gap * role_relevance

        if weighted >= self._high_priority_threshold * 0.7:
            return PriorityEnum.HIGH
        elif weighted >= self._medium_priority_threshold * 0.5:
            return PriorityEnum.MEDIUM
        else:
            return PriorityEnum.LOW

    def _generate_action(
        self,
        competency: Competency,
        current_confidence: float,
        gap: float,
    ) -> str:
        """
        Generate a specific recommended action for this gap.

        Args:
            competency: Competency with gap.
            current_confidence: Current confidence score.
            gap: Gap size.

        Returns:
            One-line actionable recommendation.
        """
        if current_confidence < 0.1:
            return (
                f"Start learning {competency.name} from fundamentals. "
                f"Focus on: {', '.join(competency.required_concepts[:3])}."
            )
        elif gap >= 0.4:
            return (
                f"Significantly improve {competency.name}. "
                f"Review all required concepts and practice explaining them clearly."
            )
        elif gap >= 0.2:
            return (
                f"Strengthen {competency.name} by practising "
                f"missed concepts: "
                f"{', '.join(competency.required_concepts[:3])}."
            )
        else:
            return (
                f"Polish {competency.name} with one more practice session "
                f"focusing on depth and real-world examples."
            )
