"""
Recommendation orchestrator.

Coordinates the full recommendation pipeline:
1. Takes skill gaps from SkillGapAnalyzer
2. Matches resources via ResourceMatcher
3. Generates learning roadmap via RoadmapGenerator
4. Suggests practice questions via PracticeGenerator
5. Returns complete recommendation output
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_core.recommendation_pipeline.resource_matcher import ResourceMatcher
from ai_core.recommendation_pipeline.roadmap_generator import RoadmapGenerator
from ai_core.recommendation_pipeline.practice_generator import PracticeGenerator
from schemas.competency_schema import CompetencyGap
from schemas.question_schema import Question
from schemas.recommendation_schema import LearningRoadmap, Recommendation, Resource


@dataclass
class RecommendationOutput:
    """
    Complete output from the recommendation pipeline.

    Attributes:
        roadmap: Week-by-week personalized learning plan.
        top_resources: Most relevant resources for immediate action.
        practice_questions: Suggested questions for weak competencies.
        quick_wins: Resources for near-ready competencies.
        critical_recommendations: High-priority items only.
    """

    roadmap: LearningRoadmap
    top_resources: list[Resource]
    practice_questions: dict[str, list[Question]]
    quick_wins: list[Recommendation]
    critical_recommendations: list[Recommendation]


class Recommender:
    """
    Orchestrates the complete recommendation pipeline.

    Entry point for all recommendation generation.
    Takes gaps and produces a complete recommendation package.

    Usage:
        recommender = Recommender()
        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )
    """

    def __init__(self) -> None:
        """Initialize all recommendation components."""
        self._matcher = ResourceMatcher()
        self._roadmap_generator = RoadmapGenerator()
        self._practice_generator = PracticeGenerator()

    def recommend(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        target_role: str,
        max_weeks: int = 8,
        session_question_ids: list[str] | None = None,
    ) -> RecommendationOutput:
        """
        Generate complete personalized recommendations.

        Args:
            user_id: User to generate recommendations for.
            session_id: Interview session that triggered this.
            gaps: Prioritized skill gaps from SkillGapAnalyzer.
            target_role: Target job role.
            max_weeks: Maximum roadmap length in weeks.
            session_question_ids: Questions already asked this session.

        Returns:
            RecommendationOutput with all recommendation types.
        """
        if not gaps:
            return self._empty_output(user_id, session_id, target_role)

        # Generate full roadmap
        roadmap = self._roadmap_generator.generate(
            user_id=user_id,
            session_id=session_id,
            gaps=gaps,
            target_role=target_role,
            max_weeks=max_weeks,
        )

        # Get top resources across all gaps
        top_resources = self._get_top_resources(gaps, top_n=5)

        # Get practice questions for weak competencies
        weak_gaps = [g for g in gaps if g.current_confidence < 0.4][:3]
        practice_questions = self._practice_generator.get_practice_for_multiple_gaps(
            gaps=weak_gaps,
            questions_per_gap=2,
            exclude_ids=session_question_ids or [],
        )

        # Extract quick wins
        quick_wins = self._extract_quick_wins(roadmap)

        # Extract critical recommendations
        critical = self._extract_critical(roadmap)

        return RecommendationOutput(
            roadmap=roadmap,
            top_resources=top_resources,
            practice_questions=practice_questions,
            quick_wins=quick_wins,
            critical_recommendations=critical,
        )

    def recommend_next_steps(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        top_n: int = 3,
    ) -> list[Recommendation]:
        """
        Generate only the immediate next step recommendations.

        A lighter version for quick feedback after evaluation.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            gaps: Prioritized skill gaps.
            top_n: Number of immediate recommendations.

        Returns:
            List of top-priority Recommendations.
        """
        if not gaps:
            return []

        recommendations = []
        top_gaps = gaps[:top_n]

        for i, gap in enumerate(top_gaps):
            resources = self._matcher.match_for_gap(gap, top_n=1)
            resource = resources[0] if resources else None

            hours = 2.0
            if resource:
                hours = self._roadmap_generator.RESOURCE_HOURS.get(
                    resource.resource_type.value, 2.0
                )

            import uuid
            rec = Recommendation(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                session_id=session_id,
                competency_id=gap.competency_id,
                competency_name=gap.competency_name,
                title=(
                    f"Improve {gap.competency_name}"
                    if not resource
                    else f"Study: {resource.title}"
                ),
                description=gap.recommended_action,
                resource=resource,
                priority=gap.priority.value,
                week_number=i + 1,
                estimated_hours=hours,
            )
            recommendations.append(rec)

        return recommendations

    def _get_top_resources(
        self,
        gaps: list[CompetencyGap],
        top_n: int = 5,
    ) -> list[Resource]:
        """
        Get top unique resources across all gaps.

        Args:
            gaps: All skill gaps.
            top_n: Maximum resources to return.

        Returns:
            Unique resources sorted by gap priority.
        """
        seen_ids: set[str] = set()
        top_resources: list[Resource] = []

        for gap in gaps:
            resources = self._matcher.match_for_gap(gap, top_n=2)
            for resource in resources:
                if resource.id not in seen_ids:
                    seen_ids.add(resource.id)
                    top_resources.append(resource)

                if len(top_resources) >= top_n:
                    break

            if len(top_resources) >= top_n:
                break

        return top_resources

    def _extract_quick_wins(
        self,
        roadmap: LearningRoadmap,
    ) -> list[Recommendation]:
        """
        Extract quick win recommendations from roadmap.

        Quick wins are recommendations with estimated 1-2 hours.

        Args:
            roadmap: Full learning roadmap.

        Returns:
            Short-duration recommendations.
        """
        quick = []
        for plan in roadmap.weekly_plans:
            for rec in plan.recommendations:
                if rec.estimated_hours <= 2.0:
                    quick.append(rec)
        return quick[:3]

    def _extract_critical(
        self,
        roadmap: LearningRoadmap,
    ) -> list[Recommendation]:
        """
        Extract critical high-priority recommendations.

        Args:
            roadmap: Full learning roadmap.

        Returns:
            High-priority recommendations only.
        """
        critical = []
        for plan in roadmap.weekly_plans[:2]:  # Only first 2 weeks
            for rec in plan.recommendations:
                if rec.priority == "high":
                    critical.append(rec)
        return critical

    def _empty_output(
        self,
        user_id: int,
        session_id: int,
        target_role: str,
    ) -> RecommendationOutput:
        """Create empty output when no gaps exist."""
        return RecommendationOutput(
            roadmap=LearningRoadmap(
                user_id=user_id,
                session_id=session_id,
                target_role=target_role,
                total_weeks=0,
                weekly_plans=[],
            ),
            top_resources=[],
            practice_questions={},
            quick_wins=[],
            critical_recommendations=[],
        )
