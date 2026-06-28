"""
Report service.

Generates complete interview session reports
combining evaluations, gaps, and recommendations.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from database.repositories import (
    SessionRepository,
    EvaluationRepository,
    RecommendationRepository,
)
from services.evaluation_service import EvaluationService
from services.competency_service import CompetencyService
from schemas.evaluation_schema import ReadinessEnum
from schemas.report_schema import InterviewReport, SessionSummary


class ReportService:
    """
    Generates structured interview session reports.

    Combines evaluation outputs, skill gaps, and recommendations
    into a complete InterviewReport schema for display and export.
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
        self._rec_repo = RecommendationRepository(db_session)
        self._eval_service = EvaluationService(db_session)
        self._competency_service = CompetencyService(db_session)

    def generate_session_report(
        self,
        session_id: int,
        user_id: int,
    ) -> InterviewReport:
        """
        Generate a complete report for a finished session.

        Args:
            session_id: Completed session to report on.
            user_id: User who completed the session.

        Returns:
            InterviewReport with all evaluation and recommendation data.

        Raises:
            ValueError: If session not found or not completed.
        """
        # Load session
        interview_session = self._session_repo.get_by_id(session_id)
        if not interview_session:
            raise ValueError(f"Session not found: {session_id}")
        if interview_session.status != "completed":
            raise ValueError(f"Session {session_id} is not completed yet")

        # Load evaluations
        evaluations = self._eval_service.get_session_evaluations(session_id)

        # Build session summary
        summary = self._build_summary(interview_session, evaluations)

        # Get skill gaps
        gaps = self._competency_service.get_skill_gaps(
            user_id=user_id,
            job_role=interview_session.job_role,
            top_n=5,
        )

        return InterviewReport(
            session_summary=summary,
            evaluations=evaluations,
            skill_gaps=gaps,
            roadmap=None,
            generated_at=datetime.utcnow(),
        )

    def generate_full_report(
        self,
        session_id: int,
        user_id: int,
        include_roadmap: bool = True,
    ) -> InterviewReport:
        """
        Generate report with optional roadmap.

        Same as generate_session_report but optionally
        includes the full learning roadmap.

        Args:
            session_id: Completed session to report on.
            user_id: User who completed the session.
            include_roadmap: Whether to include the learning roadmap.

        Returns:
            InterviewReport with optional roadmap.
        """
        from services.recommendation_service import RecommendationService

        report = self.generate_session_report(session_id, user_id)

        if include_roadmap and report.skill_gaps:
            rec_service = RecommendationService(self._db)
            interview_session = self._session_repo.get_by_id(session_id)
            roadmap = rec_service.get_roadmap(
                user_id=user_id,
                session_id=session_id,
                gaps=report.skill_gaps,
                target_role=interview_session.job_role,
            )
            report.roadmap = roadmap

        return report

    def get_session_summary(
        self,
        session_id: int,
    ) -> SessionSummary:
        """
        Get a lightweight session summary without full evaluation details.

        Args:
            session_id: Target session.

        Returns:
            SessionSummary schema.

        Raises:
            ValueError: If session not found.
        """
        interview_session = self._session_repo.get_by_id(session_id)
        if not interview_session:
            raise ValueError(f"Session not found: {session_id}")

        evaluations = self._eval_service.get_session_evaluations(session_id)
        return self._build_summary(interview_session, evaluations)

    def _build_summary(
        self,
        interview_session,
        evaluations: list,
    ) -> SessionSummary:
        """
        Build a SessionSummary from session record and evaluations.

        Args:
            interview_session: Database InterviewSession record.
            evaluations: List of EvaluationOutput schemas.

        Returns:
            SessionSummary schema.
        """
        # Extract strengths and weaknesses from evaluations
        all_strengths: list[str] = []
        all_weaknesses: list[str] = []

        for ev in evaluations:
            all_strengths.extend(ev.evidence.strengths)
            all_weaknesses.extend(ev.evidence.weaknesses)

        top_strengths = list(dict.fromkeys(all_strengths))[:3]
        top_weaknesses = list(dict.fromkeys(all_weaknesses))[:3]

        # Compute duration
        duration_minutes = 0
        if interview_session.started_at and interview_session.completed_at:
            delta = interview_session.completed_at - interview_session.started_at
            duration_minutes = max(0, int(delta.total_seconds() / 60))

        readiness = ReadinessEnum(
            interview_session.readiness_level or "poor"
        )

        return SessionSummary(
            session_id=interview_session.id,
            user_id=interview_session.user_id,
            job_role=interview_session.job_role,
            overall_score=interview_session.overall_score or 0.0,
            readiness_level=readiness,
            technical_score=interview_session.technical_score,
            hr_score=interview_session.hr_score,
            total_questions=interview_session.answered_questions or 0,
            duration_minutes=duration_minutes,
            started_at=interview_session.started_at,
            completed_at=interview_session.completed_at,
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
        )
