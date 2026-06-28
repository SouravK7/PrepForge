"""
Recommendation service.

Orchestrates recommendation generation and persistence.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ai_core.recommendation_pipeline import Recommender
from ai_core.recommendation_pipeline.recommender import RecommendationOutput
from database.repositories import (
    RecommendationRepository,
    CompetencyScoreRepository,
)
from schemas.competency_schema import CompetencyGap
from schemas.recommendation_schema import LearningRoadmap, Recommendation


class RecommendationService:
    """
    Generates and persists personalized recommendations.

    Orchestrates the recommendation pipeline and saves
    all generated recommendations to the database.
    """

    def __init__(self, db_session: Session) -> None:
        """
        Initialize with database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._rec_repo = RecommendationRepository(db_session)
        self._score_repo = CompetencyScoreRepository(db_session)
        self._recommender = Recommender()

    def generate_and_save(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        target_role: str,
        session_question_ids: list[str] | None = None,
    ) -> RecommendationOutput:
        """
        Generate recommendations and save to database.

        Args:
            user_id: Target user.
            session_id: Interview session that triggered this.
            gaps: Prioritized skill gaps.
            target_role: Target job role.
            session_question_ids: Questions asked this session.

        Returns:
            Complete RecommendationOutput.
        """
        output = self._recommender.recommend(
            user_id=user_id,
            session_id=session_id,
            gaps=gaps,
            target_role=target_role,
            session_question_ids=session_question_ids or [],
        )

        # Persist all recommendations from roadmap
        all_recs: list[Recommendation] = []
        for plan in output.roadmap.weekly_plans:
            all_recs.extend(plan.recommendations)

        if all_recs:
            self._rec_repo.bulk_create(all_recs)

        return output

    def get_roadmap(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        target_role: str,
    ) -> LearningRoadmap:
        """
        Get the learning roadmap without saving.

        Used for preview before confirming.

        Args:
            user_id: Target user.
            session_id: Interview session.
            gaps: Skill gaps to address.
            target_role: Target role.

        Returns:
            LearningRoadmap.
        """
        output = self._recommender.recommend(
            user_id=user_id,
            session_id=session_id,
            gaps=gaps,
            target_role=target_role,
        )
        return output.roadmap

    def get_user_recommendations(
        self,
        user_id: int,
        completed: bool | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Get persisted recommendations for a user.

        Args:
            user_id: Target user.
            completed: Filter by completion status.
            limit: Maximum to return.

        Returns:
            List of recommendation dicts.
        """
        records = self._rec_repo.get_user_recommendations(
            user_id=user_id,
            completed=completed,
            limit=limit,
        )

        return [
            {
                "id": r.id,
                "competency_id": r.competency_id,
                "competency_name": r.competency_name,
                "title": r.title,
                "description": r.description,
                "resource_url": r.resource_url,
                "resource_type": r.resource_type,
                "priority": r.priority,
                "week_number": r.week_number,
                "estimated_hours": r.estimated_hours,
                "is_completed": r.is_completed,
            }
            for r in records
        ]

    def mark_completed(
        self,
        recommendation_id: int,
        user_id: int,
    ) -> bool:
        """
        Mark a recommendation as completed.

        Args:
            recommendation_id: Target recommendation.
            user_id: User marking complete.

        Returns:
            True if successful.
        """
        return self._rec_repo.mark_completed(recommendation_id, user_id)

    def get_next_steps(
        self,
        user_id: int,
        session_id: int,
        gaps: list[CompetencyGap],
        top_n: int = 3,
    ) -> list[Recommendation]:
        """
        Get immediate next step recommendations.

        Args:
            user_id: Target user.
            session_id: Current session.
            gaps: Identified gaps.
            top_n: Number of steps to return.

        Returns:
            List of immediate Recommendations.
        """
        return self._recommender.recommend_next_steps(
            user_id=user_id,
            session_id=session_id,
            gaps=gaps,
            top_n=top_n,
        )
