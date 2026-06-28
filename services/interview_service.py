"""
Interview service.

Manages the complete interview session lifecycle:
- Starting a new session
- Selecting the next question adaptively
- Recording that a question was asked
- Completing a session with final scores
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ai_core.skill_pipeline.elo_estimator import EloEstimator
from ai_core.question_pipeline.question_selector import QuestionSelector
from database.repositories import (
    SessionRepository,
    CompetencyScoreRepository,
)
from schemas.question_schema import Question, InterviewPhase


@dataclass
class SessionStartResult:
    """
    Result of starting a new interview session.

    Attributes:
        session_id: Created session database ID.
        job_role: Target role for this session.
        blueprint: Interview phase blueprint.
        first_question: First question to ask.
    """

    session_id: int
    job_role: str
    blueprint: list[dict]
    first_question: Optional[Question]


@dataclass
class NextQuestionResult:
    """
    Result of requesting the next interview question.

    Attributes:
        question: Next question to ask. None if session complete.
        phase: Interview phase this question belongs to.
        question_number: Current question number (1-based).
        total_questions: Total planned questions.
        is_complete: True if no more questions.
    """

    question: Optional[Question]
    phase: InterviewPhase
    question_number: int
    total_questions: int
    is_complete: bool


class InterviewService:
    """
    Manages interview session lifecycle.

    Coordinates question selection, session state,
    and adaptive difficulty through the Elo estimator.
    """

    # Interview blueprint phase distribution
    PHASE_BLUEPRINT = [
        {"phase": InterviewPhase.INTRODUCTION, "count": 1, "type": "hr"},
        {"phase": InterviewPhase.RESUME_VERIFICATION, "count": 1, "type": "technical"},
        {"phase": InterviewPhase.CORE_TECHNICAL, "count": 5, "type": "technical"},
        {"phase": InterviewPhase.SCENARIO, "count": 1, "type": "technical"},
        {"phase": InterviewPhase.BEHAVIORAL, "count": 1, "type": "hr"},
        {"phase": InterviewPhase.CLOSING, "count": 1, "type": "hr"},
    ]

    def __init__(self, db_session: Session) -> None:
        """
        Initialize with database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._session_repo = SessionRepository(db_session)
        self._competency_repo = CompetencyScoreRepository(db_session)
        self._elo_estimator = EloEstimator()
        self._question_selector = QuestionSelector()

    def start_session(
        self,
        user_id: int,
        job_role: str,
        difficulty: str = "intermediate",
        experience_level: str = "",
        total_questions: int = 10,
    ) -> SessionStartResult:
        """
        Start a new interview session.

        Creates the session record, loads the question blueprint,
        and selects the first question.

        Args:
            user_id: User starting the session.
            job_role: Target job role e.g. "Software Engineer".
            difficulty: Session difficulty level.
            experience_level: User experience level.
            total_questions: Total questions planned.

        Returns:
            SessionStartResult with session_id and first question.
        """
        # Create session in database
        interview_session = self._session_repo.create(
            user_id=user_id,
            job_role=job_role,
            difficulty=difficulty,
            experience_level=experience_level,
            total_questions=total_questions,
        )

        # Select first question (introduction/HR phase)
        first_question = self._question_selector.select_first_question(
            job_role=job_role,
            phase=InterviewPhase.INTRODUCTION,
        )

        blueprint = [
            {
                "phase": phase["phase"].value,
                "count": phase["count"],
                "type": phase["type"],
            }
            for phase in self.PHASE_BLUEPRINT
        ]

        return SessionStartResult(
            session_id=interview_session.id,
            job_role=job_role,
            blueprint=blueprint,
            first_question=first_question,
        )

    def get_next_question(
        self,
        session_id: int,
        user_id: int,
        job_role: str,
        asked_question_ids: list[str],
        last_score: Optional[float] = None,
        last_competency_id: Optional[str] = None,
        question_number: int = 1,
        total_questions: int = 10,
    ) -> NextQuestionResult:
        """
        Select the next adaptive question for the session.

        Uses Elo-based difficulty adaptation to select a question
        appropriate for the user's current skill level.

        Args:
            session_id: Active interview session ID.
            user_id: User being interviewed.
            job_role: Target job role.
            asked_question_ids: Questions already asked this session.
            last_score: Score from the most recent answer (0-100).
            last_competency_id: Competency just evaluated.
            question_number: Current question number (1-based).
            total_questions: Total planned questions.

        Returns:
            NextQuestionResult with next question or completion signal.
        """
        if question_number > total_questions:
            return NextQuestionResult(
                question=None,
                phase=InterviewPhase.CLOSING,
                question_number=question_number,
                total_questions=total_questions,
                is_complete=True,
            )

        # Determine current phase
        phase = self._determine_phase(question_number, total_questions)

        # Get user skill Elo for adaptive difficulty
        skill_elo = 1000.0
        if last_competency_id:
            score = self._competency_repo.get_by_user_and_competency(
                user_id, last_competency_id
            )
            if score:
                skill_elo = score.elo_rating

        # Recommend difficulty based on Elo
        recommended_difficulty = self._elo_estimator.recommend_difficulty(skill_elo)

        # Select question
        question = self._question_selector.select_question(
            job_role=job_role,
            phase=phase,
            difficulty=recommended_difficulty,
            exclude_ids=asked_question_ids,
        )

        is_complete = question is None and question_number >= total_questions

        return NextQuestionResult(
            question=question,
            phase=phase,
            question_number=question_number,
            total_questions=total_questions,
            is_complete=is_complete,
        )

    def complete_session(
        self,
        session_id: int,
        evaluation_scores: list[float],
        technical_scores: list[float],
        hr_scores: list[float],
        answered_questions: int,
    ) -> dict:
        """
        Complete a session and persist final scores.

        Args:
            session_id: Session to complete.
            evaluation_scores: All weighted final scores.
            technical_scores: Technical question scores only.
            hr_scores: HR question scores only.
            answered_questions: Total answers submitted.

        Returns:
            Dict with final session summary data.
        """
        overall = (
            sum(evaluation_scores) / len(evaluation_scores)
            if evaluation_scores else 0.0
        )
        technical = (
            sum(technical_scores) / len(technical_scores)
            if technical_scores else 0.0
        )
        hr = (
            sum(hr_scores) / len(hr_scores)
            if hr_scores else 0.0
        )
        readiness = self._score_to_readiness(overall)

        self._session_repo.complete_session(
            session_id=session_id,
            overall_score=round(overall, 2),
            technical_score=round(technical, 2),
            hr_score=round(hr, 2),
            readiness_level=readiness,
            answered_questions=answered_questions,
        )

        return {
            "session_id": session_id,
            "overall_score": round(overall, 2),
            "technical_score": round(technical, 2),
            "hr_score": round(hr, 2),
            "readiness_level": readiness,
            "answered_questions": answered_questions,
        }

    def get_session_history(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get completed session history for a user.

        Args:
            user_id: Target user.
            limit: Maximum sessions to return.

        Returns:
            List of session summary dicts.
        """
        sessions = self._session_repo.get_completed_sessions(user_id, limit)
        return [
            {
                "session_id": s.id,
                "job_role": s.job_role,
                "overall_score": s.overall_score,
                "readiness_level": s.readiness_level,
                "answered_questions": s.answered_questions,
                "completed_at": (
                    s.completed_at.strftime("%Y-%m-%d %H:%M")
                    if s.completed_at else ""
                ),
            }
            for s in sessions
        ]

    def _determine_phase(
        self,
        question_number: int,
        total_questions: int,
    ) -> InterviewPhase:
        """
        Determine which interview phase we are in.

        Args:
            question_number: Current question number (1-based).
            total_questions: Total planned questions.

        Returns:
            InterviewPhase for this position.
        """
        if question_number == 1:
            return InterviewPhase.INTRODUCTION
        elif question_number == 2:
            return InterviewPhase.RESUME_VERIFICATION
        elif question_number >= total_questions:
            return InterviewPhase.CLOSING
        elif question_number >= total_questions - 1:
            return InterviewPhase.BEHAVIORAL
        else:
            return InterviewPhase.CORE_TECHNICAL

    def _score_to_readiness(self, score: float) -> str:
        """
        Map numeric score to readiness label.

        Args:
            score: Overall score 0-100.

        Returns:
            Readiness level string.
        """
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "average"
        else:
            return "poor"
