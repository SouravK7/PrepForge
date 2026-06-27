"""
Learning roadmap generator.

Creates a week-by-week personalized learning plan from
identified skill gaps ordered by priority and dependency.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from ai_core.recommendation_pipeline.resource_matcher import ResourceMatcher
from ai_core.shared.ai_logger import ai_logger
from schemas.competency_schema import CompetencyGap
from schemas.recommendation_schema import (
    LearningRoadmap,
    Recommendation,
    WeeklyPlan,
)


class RoadmapGenerator:
    """
    Generates week-by-week personalized learning roadmaps.

    Takes a prioritized list of skill gaps and produces
    a structured roadmap assigning gaps to weekly learning
    goals with matching resources.
    """

    # Estimated hours per resource type
    RESOURCE_HOURS: dict[str, float] = {
        "documentation": 2.0,
        "course": 5.0,
        "article": 1.0,
        "practice": 3.0,
        "book": 8.0,
        "video": 2.0,
    }

    # Max gaps addressed per week
    MAX_GAPS_PER_WEEK = 2

    def __init__(self) -> None:
        """Initialize resource matcher."""
        self._matcher = ResourceMatcher()

    def generate(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        target_role: str,
        max_weeks: int = 8,
    ) -> LearningRoadmap:
        """
        Generate a complete personalized learning roadmap.

        Args:
            user_id: User this roadmap is for.
            session_id: Interview session that triggered this.
            gaps: Prioritized skill gaps from SkillGapAnalyzer.
            target_role: Target job role.
            max_weeks: Maximum roadmap length in weeks.

        Returns:
            LearningRoadmap with week-by-week plans.
        """
        if not gaps:
            return LearningRoadmap(
                user_id=user_id,
                session_id=session_id,
                target_role=target_role,
                total_weeks=0,
                weekly_plans=[],
                estimated_readiness_date=None,
            )

        # Group gaps into weeks
        weekly_plans = self._build_weekly_plans(
            user_id=user_id,
            session_id=session_id,
            gaps=gaps,
            max_weeks=max_weeks,
        )

        total_weeks = len(weekly_plans)
        readiness_date = self._estimate_readiness_date(total_weeks)

        roadmap = LearningRoadmap(
            user_id=user_id,
            session_id=session_id,
            target_role=target_role,
            total_weeks=total_weeks,
            weekly_plans=weekly_plans,
            estimated_readiness_date=readiness_date,
        )

        # Log decision
        ai_logger.log_recommendation_generated(
            user_id=user_id,
            competency_id="roadmap",
            resource_id=None,
            reasoning=(
                f"Generated {total_weeks}-week roadmap for "
                f"{len(gaps)} skill gaps targeting {target_role}"
            ),
        )

        return roadmap

    def _build_weekly_plans(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        max_weeks: int,
    ) -> list[WeeklyPlan]:
        """
        Build weekly plans by assigning gaps to weeks.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            gaps: Prioritized gaps to address.
            max_weeks: Maximum number of weeks.

        Returns:
            List of WeeklyPlan objects.
        """
        weekly_plans = []
        week_number = 1
        gap_index = 0

        while gap_index < len(gaps) and week_number <= max_weeks:
            # Take up to MAX_GAPS_PER_WEEK gaps for this week
            week_gaps = gaps[gap_index:gap_index + self.MAX_GAPS_PER_WEEK]
            gap_index += self.MAX_GAPS_PER_WEEK

            # Primary gap for this week
            primary_gap = week_gaps[0]

            # Generate recommendations for all gaps in this week
            week_recommendations = []
            for gap in week_gaps:
                recs = self._generate_recommendations_for_gap(
                    gap=gap,
                    user_id=user_id,
                    session_id=session_id,
                    week_number=week_number,
                )
                week_recommendations.extend(recs)

            # Compute total estimated hours
            total_hours = sum(r.estimated_hours for r in week_recommendations)

            # Build week goal
            goal = self._generate_week_goal(primary_gap, week_gaps)

            plan = WeeklyPlan(
                week_number=week_number,
                focus_competency=primary_gap.competency_id,
                focus_competency_name=primary_gap.competency_name,
                recommendations=week_recommendations,
                estimated_hours=round(total_hours, 1),
                goal=goal,
            )
            weekly_plans.append(plan)
            week_number += 1

        return weekly_plans

    def _generate_recommendations_for_gap(
        self,
        gap: CompetencyGap,
        user_id: int,
        session_id: int,
        week_number: int,
    ) -> list[Recommendation]:
        """
        Generate recommendations for a single gap.

        Args:
            gap: Competency gap to address.
            user_id: User identifier.
            session_id: Session identifier.
            week_number: Which week these belong to.

        Returns:
            List of Recommendation objects.
        """
        resources = self._matcher.match_for_gap(gap, top_n=2)
        recommendations = []

        for resource in resources:
            hours = self.RESOURCE_HOURS.get(
                resource.resource_type.value, 2.0
            )

            rec = Recommendation(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                session_id=session_id,
                competency_id=gap.competency_id,
                competency_name=gap.competency_name,
                title=f"Study: {resource.title}",
                description=(
                    f"Addresses gap in {gap.competency_name} "
                    f"(current confidence: {gap.current_confidence:.0%}, "
                    f"gap: {gap.gap:.0%}). {resource.description}"
                ),
                resource=resource,
                priority=gap.priority.value,
                week_number=week_number,
                estimated_hours=hours,
            )
            recommendations.append(rec)

            ai_logger.log_recommendation_generated(
                user_id=user_id,
                competency_id=gap.competency_id,
                resource_id=resource.id,
                reasoning=(
                    f"Gap: {gap.gap:.2f}, Priority: {gap.priority.value}, "
                    f"Relevance: {gap.role_relevance:.2f}"
                ),
            )

        # If no resources found, generate a practice recommendation
        if not recommendations:
            rec = Recommendation(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                session_id=session_id,
                competency_id=gap.competency_id,
                competency_name=gap.competency_name,
                title=f"Practice: {gap.competency_name}",
                description=(
                    f"Practice explaining {gap.competency_name} concepts. "
                    f"Focus on: {gap.recommended_action}"
                ),
                resource=None,
                priority=gap.priority.value,
                week_number=week_number,
                estimated_hours=2.0,
            )
            recommendations.append(rec)

        return recommendations

    def _generate_week_goal(
        self,
        primary_gap: CompetencyGap,
        all_week_gaps: list[CompetencyGap],
    ) -> str:
        """
        Generate a clear goal statement for the week.

        Args:
            primary_gap: Primary focus gap for the week.
            all_week_gaps: All gaps addressed this week.

        Returns:
            Goal statement string.
        """
        if len(all_week_gaps) == 1:
            return (
                f"By end of this week, be able to clearly explain "
                f"{primary_gap.competency_name} concepts and provide "
                f"a real-world example during an interview."
            )
        else:
            secondary = all_week_gaps[1]
            return (
                f"By end of this week, improve {primary_gap.competency_name} "
                f"and {secondary.competency_name}. "
                f"Practice explaining both with concrete examples."
            )

    def _estimate_readiness_date(self, total_weeks: int) -> str:
        """
        Estimate the date the user will be interview-ready.

        Args:
            total_weeks: Total weeks in the roadmap.

        Returns:
            Formatted date string.
        """
        target_date = datetime.utcnow() + timedelta(weeks=total_weeks)
        return target_date.strftime("%B %d, %Y")
