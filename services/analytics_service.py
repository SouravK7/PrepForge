"""
Analytics service.

Computes performance statistics and dashboard data
for users. All data comes from the database.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.repositories import (
    SessionRepository,
    EvaluationRepository,
    CompetencyScoreRepository,
    RecommendationRepository,
)


class AnalyticsService:
    """
    Computes performance analytics and dashboard statistics.

    Aggregates data from multiple repositories to produce
    visualizable metrics for the dashboard.
    """

    def __init__(self, db_session: Session) -> None:
        """
        Initialize with database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._session_repo = SessionRepository(db_session)
        self._eval_repo = EvaluationRepository(db_session)
        self._score_repo = CompetencyScoreRepository(db_session)
        self._rec_repo = RecommendationRepository(db_session)

    def get_dashboard_stats(self, user_id: int) -> dict:
        """
        Get complete dashboard statistics for a user.

        Args:
            user_id: Target user.

        Returns:
            Dict with all dashboard data including overview, trends,
            competency breakdown, and recommendation status.
        """
        sessions = self._session_repo.get_completed_sessions(user_id, limit=50)

        if not sessions:
            return self._empty_dashboard()

        scores = [s.overall_score for s in sessions if s.overall_score]
        total_sessions = len(sessions)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        best_score = max(scores) if scores else 0.0
        latest_score = scores[0] if scores else 0.0

        # Improvement rate: latest minus oldest
        improvement = 0.0
        if len(scores) >= 2:
            improvement = round(scores[0] - scores[-1], 2)

        # Score trend for chart
        score_trend = self._session_repo.get_score_trend(user_id)

        # Competency breakdown
        competency_scores = self._score_repo.get_all_for_user(user_id)
        top_competencies = [
            {
                "competency_id": s.competency_id,
                "confidence": round(s.confidence * 100, 1),
                "evidence_count": s.evidence_count,
            }
            for s in sorted(
                competency_scores,
                key=lambda x: x.confidence,
                reverse=True,
            )[:5]
        ]

        weak_competencies = [
            {
                "competency_id": s.competency_id,
                "confidence": round(s.confidence * 100, 1),
                "evidence_count": s.evidence_count,
            }
            for s in sorted(
                competency_scores,
                key=lambda x: x.confidence,
            )[:5]
        ]

        # Recommendation stats
        completion_rate = self._rec_repo.get_completion_rate(user_id)
        pending_recs = self._rec_repo.get_user_recommendations(
            user_id, completed=False, limit=3
        )

        # Role breakdown
        role_scores: dict[str, list[float]] = {}
        for s in sessions:
            if s.job_role not in role_scores:
                role_scores[s.job_role] = []
            if s.overall_score:
                role_scores[s.job_role].append(s.overall_score)

        role_avg = {
            role: round(sum(score_list) / len(score_list), 2)
            for role, score_list in role_scores.items()
            if score_list
        }

        return {
            "overview": {
                "total_sessions": total_sessions,
                "avg_score": round(avg_score, 2),
                "best_score": round(best_score, 2),
                "latest_score": round(latest_score, 2),
                "improvement": improvement,
            },
            "score_trend": score_trend,
            "top_competencies": top_competencies,
            "weak_competencies": weak_competencies,
            "recommendation_completion_rate": round(completion_rate * 100, 1),
            "pending_recommendations": [
                {
                    "title": r.title,
                    "priority": r.priority,
                    "week_number": r.week_number,
                }
                for r in pending_recs
            ],
            "role_performance": role_avg,
        }

    def get_score_trend(
        self,
        user_id: int,
        job_role: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get score trend data for chart visualization.

        Args:
            user_id: Target user.
            job_role: Filter by role if specified.
            limit: Maximum data points.

        Returns:
            List of score data points with date and score.
        """
        return self._session_repo.get_score_trend(
            user_id=user_id,
            job_role=job_role,
            limit=limit,
        )

    def get_competency_radar_data(
        self,
        user_id: int,
    ) -> dict:
        """
        Get competency scores formatted for radar chart.

        Args:
            user_id: Target user.

        Returns:
            Dict with labels and values for radar chart.
        """
        scores = self._score_repo.get_all_for_user(user_id)

        labels = [
            s.competency_id
            .replace("comp_se_", "")
            .replace("comp_da_", "")
            .replace("comp_ai_", "")
            .replace("_", " ")
            .title()
            for s in scores[:8]
        ]
        values = [round(s.confidence * 100, 1) for s in scores[:8]]

        return {
            "labels": labels,
            "values": values,
        }

    def _empty_dashboard(self) -> dict:
        """
        Return empty dashboard structure for users with no sessions.

        Returns:
            Dict with zeroed-out dashboard data.
        """
        return {
            "overview": {
                "total_sessions": 0,
                "avg_score": 0.0,
                "best_score": 0.0,
                "latest_score": 0.0,
                "improvement": 0.0,
            },
            "score_trend": [],
            "top_competencies": [],
            "weak_competencies": [],
            "recommendation_completion_rate": 0.0,
            "pending_recommendations": [],
            "role_performance": {},
        }
