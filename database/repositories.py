"""
Repository pattern for all database operations.

Each repository handles one model and provides
typed methods for CRUD operations. No raw SQL
is written outside this file.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import (
    AIDecisionLog,
    Answer,
    BenchmarkRun,
    CompetencyScore,
    EvaluationRecord,
    InterviewSession,
    RecommendationRecord,
    Resume,
    User,
)
from schemas.competency_schema import CompetencyScore as CompetencyScoreSchema
from schemas.evaluation_schema import EvaluationOutput
from schemas.recommendation_schema import Recommendation


# ══════════════════════════════════════════════════════════════
# USER REPOSITORY
# ══════════════════════════════════════════════════════════════

class UserRepository:
    """
    Repository for User model CRUD operations.

    All user persistence operations go through this class.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize with database session.

        Args:
            session: SQLAlchemy session.
        """
        self._session = session

    def create(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        target_role: str = "",
        experience_level: str = "",
    ) -> User:
        """
        Create a new user.

        Args:
            username: Unique username.
            email: Unique email address.
            password: Plain text password (hashed before storage).
            full_name: User's display name.
            target_role: Desired job role.
            experience_level: Experience level string.

        Returns:
            Created User model instance.

        Raises:
            IntegrityError: If username or email already exists.
        """
        password_hash = self._hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            target_role=target_role,
            experience_level=experience_level,
        )
        self._session.add(user)
        self._session.flush()
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by primary key.

        Args:
            user_id: User primary key.

        Returns:
            User if found, None otherwise.
        """
        return self._session.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to look up.

        Returns:
            User if found, None otherwise.
        """
        return (
            self._session.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: Email to look up.

        Returns:
            User if found, None otherwise.
        """
        return (
            self._session.query(User)
            .filter(User.email == email)
            .first()
        )

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username to authenticate.
            password: Plain text password.

        Returns:
            User if credentials are valid and account is active.
            None otherwise.
        """
        user = self.get_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if user.password_hash != self._hash_password(password):
            return None
        return user

    def update_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        target_role: Optional[str] = None,
        experience_level: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update user profile fields.

        Args:
            user_id: User to update.
            full_name: New full name.
            target_role: New target role.
            experience_level: New experience level.

        Returns:
            Updated User if found, None otherwise.
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        if full_name is not None:
            user.full_name = full_name
        if target_role is not None:
            user.target_role = target_role
        if experience_level is not None:
            user.experience_level = experience_level

        user.updated_at = datetime.utcnow()
        self._session.flush()
        return user

    def deactivate(self, user_id: int) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User to deactivate.

        Returns:
            True if deactivated, False if user not found.
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        self._session.flush()
        return True

    def _hash_password(self, password: str) -> str:
        """Hash password with SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════
# SESSION REPOSITORY
# ══════════════════════════════════════════════════════════════

class SessionRepository:
    """
    Repository for InterviewSession CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def create(
        self,
        user_id: int,
        job_role: str,
        difficulty: str = "intermediate",
        experience_level: str = "",
        total_questions: int = 10,
    ) -> InterviewSession:
        """
        Create a new interview session.

        Args:
            user_id: User starting the session.
            job_role: Target job role for this session.
            difficulty: Session difficulty level.
            experience_level: User experience level.
            total_questions: Planned number of questions.

        Returns:
            Created InterviewSession.
        """
        interview_session = InterviewSession(
            user_id=user_id,
            job_role=job_role,
            difficulty=difficulty,
            experience_level=experience_level,
            status="in_progress",
            total_questions=total_questions,
        )
        self._session.add(interview_session)
        self._session.flush()
        return interview_session

    def get_by_id(self, session_id: int) -> Optional[InterviewSession]:
        """Get session by primary key."""
        return self._session.get(InterviewSession, session_id)

    def get_user_sessions(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[InterviewSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User to get sessions for.
            limit: Maximum sessions to return.

        Returns:
            Sessions sorted by started_at descending.
        """
        return (
            self._session.query(InterviewSession)
            .filter(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_completed_sessions(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[InterviewSession]:
        """Get only completed sessions for a user."""
        return (
            self._session.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
            )
            .order_by(InterviewSession.completed_at.desc())
            .limit(limit)
            .all()
        )

    def complete_session(
        self,
        session_id: int,
        overall_score: float,
        technical_score: float,
        hr_score: float,
        readiness_level: str,
        answered_questions: int,
    ) -> Optional[InterviewSession]:
        """
        Mark a session as completed with final scores.

        Args:
            session_id: Session to complete.
            overall_score: Weighted final score.
            technical_score: Average technical question score.
            hr_score: Average HR question score.
            readiness_level: Overall readiness assessment.
            answered_questions: How many questions were answered.

        Returns:
            Updated session if found, None otherwise.
        """
        interview_session = self.get_by_id(session_id)
        if not interview_session:
            return None

        interview_session.status = "completed"
        interview_session.overall_score = overall_score
        interview_session.technical_score = technical_score
        interview_session.hr_score = hr_score
        interview_session.readiness_level = readiness_level
        interview_session.answered_questions = answered_questions
        interview_session.completed_at = datetime.utcnow()

        self._session.flush()
        return interview_session

    def get_score_trend(
        self,
        user_id: int,
        job_role: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get score trend for dashboard visualization.

        Args:
            user_id: User to get trend for.
            job_role: Filter by role if specified.
            limit: Maximum data points.

        Returns:
            List of dicts with date and score.
        """
        query = (
            self._session.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
            )
        )

        if job_role:
            query = query.filter(InterviewSession.job_role == job_role)

        sessions = (
            query
            .order_by(InterviewSession.completed_at.asc())
            .limit(limit)
            .all()
        )

        return [
            {
                "date": s.completed_at.strftime("%Y-%m-%d") if s.completed_at else "",
                "score": s.overall_score,
                "role": s.job_role,
            }
            for s in sessions
        ]


# ══════════════════════════════════════════════════════════════
# ANSWER REPOSITORY
# ══════════════════════════════════════════════════════════════

class AnswerRepository:
    """
    Repository for Answer CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def create(
        self,
        session_id: int,
        user_id: int,
        question_id: str,
        competency_id: str,
        question_text: str,
        question_type: str,
        answer_text: str,
        time_taken: int = 0,
    ) -> Answer:
        """
        Save a user answer.

        Args:
            session_id: Interview session.
            user_id: User who answered.
            question_id: Question that was answered.
            competency_id: Competency being assessed.
            question_text: Full question text.
            question_type: technical or hr.
            answer_text: User's raw answer.
            time_taken: Seconds taken to answer.

        Returns:
            Created Answer record.
        """
        answer = Answer(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            competency_id=competency_id,
            question_text=question_text,
            question_type=question_type,
            answer_text=answer_text,
            time_taken=time_taken,
        )
        self._session.add(answer)
        self._session.flush()
        return answer

    def get_by_id(self, answer_id: int) -> Optional[Answer]:
        """Get answer by primary key."""
        return self._session.get(Answer, answer_id)

    def get_session_answers(self, session_id: int) -> list[Answer]:
        """Get all answers for a session ordered by time."""
        return (
            self._session.query(Answer)
            .filter(Answer.session_id == session_id)
            .order_by(Answer.submitted_at.asc())
            .all()
        )

    def get_user_answers_for_competency(
        self,
        user_id: int,
        competency_id: str,
        limit: int = 10,
    ) -> list[Answer]:
        """Get recent answers for a specific competency."""
        return (
            self._session.query(Answer)
            .filter(
                Answer.user_id == user_id,
                Answer.competency_id == competency_id,
            )
            .order_by(Answer.submitted_at.desc())
            .limit(limit)
            .all()
        )


# ══════════════════════════════════════════════════════════════
# EVALUATION REPOSITORY
# ══════════════════════════════════════════════════════════════

class EvaluationRepository:
    """
    Repository for EvaluationRecord CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def create_from_output(
        self,
        evaluation_output: EvaluationOutput,
        answer_id: int,
    ) -> EvaluationRecord:
        """
        Create evaluation record from EvaluationOutput schema.

        Args:
            evaluation_output: Complete evaluation from ensemble.
            answer_id: Database ID of the evaluated answer.

        Returns:
            Created EvaluationRecord.
        """
        record = EvaluationRecord(
            answer_id=answer_id,
            session_id=evaluation_output.session_id,
            user_id=evaluation_output.user_id,
            question_id=evaluation_output.question_id,
            competency_id=evaluation_output.competency_id,
            semantic_score=evaluation_output.scores.semantic,
            concept_score=evaluation_output.scores.concept,
            communication_score=evaluation_output.scores.communication,
            evidence_score=evaluation_output.scores.evidence,
            reasoning_score=evaluation_output.scores.reasoning,
            weighted_final=evaluation_output.scores.weighted_final,
            grade=evaluation_output.grade.value,
            readiness_level=evaluation_output.readiness_level.value,
            matched_concepts=json.dumps(
                evaluation_output.evidence.matched_concepts
            ),
            missing_concepts=json.dumps(
                evaluation_output.evidence.missing_concepts
            ),
            strengths=json.dumps(evaluation_output.evidence.strengths),
            weaknesses=json.dumps(evaluation_output.evidence.weaknesses),
            explanation=json.dumps({
                "semantic_reason": evaluation_output.explanation.semantic_reason,
                "concept_reason": evaluation_output.explanation.concept_reason,
                "communication_reason": evaluation_output.explanation.communication_reason,
                "evidence_reason": evaluation_output.explanation.evidence_reason,
                "reasoning_reason": evaluation_output.explanation.reasoning_reason,
                "overall_summary": evaluation_output.explanation.overall_summary,
                "improvement_tip": evaluation_output.explanation.improvement_tip,
            }),
            competency_delta=evaluation_output.competency_delta,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def get_by_id(self, evaluation_id: int) -> Optional[EvaluationRecord]:
        """Get evaluation by primary key."""
        return self._session.get(EvaluationRecord, evaluation_id)

    def get_session_evaluations(
        self, session_id: int
    ) -> list[EvaluationRecord]:
        """Get all evaluations for a session."""
        return (
            self._session.query(EvaluationRecord)
            .filter(EvaluationRecord.session_id == session_id)
            .order_by(EvaluationRecord.evaluated_at.asc())
            .all()
        )

    def get_average_scores_by_competency(
        self,
        user_id: int,
        competency_id: str,
    ) -> dict[str, float]:
        """
        Get average dimension scores for a user on one competency.

        Args:
            user_id: Target user.
            competency_id: Target competency.

        Returns:
            Dict of dimension name to average score.
        """
        evaluations = (
            self._session.query(EvaluationRecord)
            .filter(
                EvaluationRecord.user_id == user_id,
                EvaluationRecord.competency_id == competency_id,
            )
            .all()
        )

        if not evaluations:
            return {}

        count = len(evaluations)
        return {
            "semantic": sum(e.semantic_score for e in evaluations) / count,
            "concept": sum(e.concept_score for e in evaluations) / count,
            "communication": sum(e.communication_score for e in evaluations) / count,
            "evidence": sum(e.evidence_score for e in evaluations) / count,
            "reasoning": sum(e.reasoning_score for e in evaluations) / count,
            "weighted_final": sum(e.weighted_final for e in evaluations) / count,
        }

    def get_evaluation_for_answer(
        self, answer_id: int
    ) -> Optional[EvaluationRecord]:
        """Get the evaluation for a specific answer."""
        return (
            self._session.query(EvaluationRecord)
            .filter(EvaluationRecord.answer_id == answer_id)
            .first()
        )


# ══════════════════════════════════════════════════════════════
# COMPETENCY SCORE REPOSITORY
# ══════════════════════════════════════════════════════════════

class CompetencyScoreRepository:
    """
    Repository for CompetencyScore CRUD operations.

    One record per (user_id, competency_id) pair.
    Upsert pattern used for all updates.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def upsert(
        self,
        schema: CompetencyScoreSchema,
    ) -> CompetencyScore:
        """
        Create or update a competency score.

        If a record exists for (user_id, competency_id), update it.
        Otherwise create a new record.

        Args:
            schema: CompetencyScore Pydantic schema.

        Returns:
            Created or updated CompetencyScore model.
        """
        existing = self.get_by_user_and_competency(
            schema.user_id, schema.competency_id
        )

        if existing:
            existing.confidence = schema.confidence
            existing.elo_rating = schema.elo_rating
            existing.evidence_count = schema.evidence_count
            existing.improvement_trend = schema.improvement_trend
            existing.last_assessed = schema.last_assessed or datetime.utcnow()
            self._session.flush()
            return existing

        record = CompetencyScore(
            user_id=schema.user_id,
            competency_id=schema.competency_id,
            confidence=schema.confidence,
            elo_rating=schema.elo_rating,
            evidence_count=schema.evidence_count,
            improvement_trend=schema.improvement_trend,
            last_assessed=schema.last_assessed or datetime.utcnow(),
        )
        self._session.add(record)
        self._session.flush()
        return record

    def get_by_user_and_competency(
        self,
        user_id: int,
        competency_id: str,
    ) -> Optional[CompetencyScore]:
        """
        Get score for a specific user-competency pair.

        Args:
            user_id: User identifier.
            competency_id: Competency identifier.

        Returns:
            CompetencyScore if found, None otherwise.
        """
        return (
            self._session.query(CompetencyScore)
            .filter(
                CompetencyScore.user_id == user_id,
                CompetencyScore.competency_id == competency_id,
            )
            .first()
        )

    def get_all_for_user(
        self, user_id: int
    ) -> list[CompetencyScore]:
        """Get all competency scores for a user."""
        return (
            self._session.query(CompetencyScore)
            .filter(CompetencyScore.user_id == user_id)
            .order_by(CompetencyScore.confidence.desc())
            .all()
        )

    def get_weak_competencies(
        self,
        user_id: int,
        threshold: float = 0.5,
        limit: int = 5,
    ) -> list[CompetencyScore]:
        """
        Get competencies below the confidence threshold.

        Args:
            user_id: Target user.
            threshold: Confidence below which is weak.
            limit: Maximum to return.

        Returns:
            Weak competencies sorted by confidence ascending.
        """
        return (
            self._session.query(CompetencyScore)
            .filter(
                CompetencyScore.user_id == user_id,
                CompetencyScore.confidence < threshold,
            )
            .order_by(CompetencyScore.confidence.asc())
            .limit(limit)
            .all()
        )

    def to_schema_dict(
        self, user_id: int
    ) -> dict[str, CompetencyScoreSchema]:
        """
        Get all scores for a user as a schema dictionary.

        Args:
            user_id: Target user.

        Returns:
            Dict of competency_id to CompetencyScore schema.
        """
        records = self.get_all_for_user(user_id)
        return {
            r.competency_id: CompetencyScoreSchema(
                user_id=r.user_id,
                competency_id=r.competency_id,
                confidence=r.confidence,
                elo_rating=r.elo_rating,
                evidence_count=r.evidence_count,
                improvement_trend=r.improvement_trend,
                last_assessed=r.last_assessed,
            )
            for r in records
        }


# ══════════════════════════════════════════════════════════════
# RECOMMENDATION REPOSITORY
# ══════════════════════════════════════════════════════════════

class RecommendationRepository:
    """
    Repository for RecommendationRecord CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def create_from_schema(
        self,
        recommendation: Recommendation,
    ) -> RecommendationRecord:
        """
        Create a recommendation record from schema.

        Args:
            recommendation: Recommendation Pydantic schema.

        Returns:
            Created RecommendationRecord.
        """
        record = RecommendationRecord(
            user_id=recommendation.user_id,
            session_id=recommendation.session_id,
            competency_id=recommendation.competency_id,
            competency_name=recommendation.competency_name,
            title=recommendation.title,
            description=recommendation.description,
            resource_url=recommendation.resource.url if recommendation.resource else None,
            resource_type=recommendation.resource.resource_type.value if recommendation.resource else None,
            priority=recommendation.priority,
            week_number=recommendation.week_number,
            estimated_hours=recommendation.estimated_hours,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def bulk_create(
        self,
        recommendations: list[Recommendation],
    ) -> list[RecommendationRecord]:
        """
        Create multiple recommendation records at once.

        Args:
            recommendations: List of Recommendation schemas.

        Returns:
            List of created records.
        """
        records = []
        for rec in recommendations:
            records.append(self.create_from_schema(rec))
        return records

    def get_user_recommendations(
        self,
        user_id: int,
        completed: Optional[bool] = None,
        limit: int = 20,
    ) -> list[RecommendationRecord]:
        """
        Get recommendations for a user.

        Args:
            user_id: Target user.
            completed: Filter by completion status if provided.
            limit: Maximum to return.

        Returns:
            Recommendations ordered by priority and week.
        """
        query = (
            self._session.query(RecommendationRecord)
            .filter(RecommendationRecord.user_id == user_id)
        )

        if completed is not None:
            query = query.filter(
                RecommendationRecord.is_completed == completed
            )

        return (
            query
            .order_by(
                RecommendationRecord.week_number.asc(),
                RecommendationRecord.priority.desc(),
            )
            .limit(limit)
            .all()
        )

    def mark_completed(
        self,
        recommendation_id: int,
        user_id: int,
    ) -> bool:
        """
        Mark a recommendation as completed.

        Args:
            recommendation_id: Recommendation to complete.
            user_id: Must match the recommendation owner.

        Returns:
            True if marked, False if not found or wrong user.
        """
        record = (
            self._session.query(RecommendationRecord)
            .filter(
                RecommendationRecord.id == recommendation_id,
                RecommendationRecord.user_id == user_id,
            )
            .first()
        )

        if not record:
            return False

        record.is_completed = True
        record.completed_at = datetime.utcnow()
        self._session.flush()
        return True

    def get_completion_rate(self, user_id: int) -> float:
        """
        Get recommendation completion rate for a user.

        Args:
            user_id: Target user.

        Returns:
            Completion rate 0.0 to 1.0.
        """
        total = (
            self._session.query(RecommendationRecord)
            .filter(RecommendationRecord.user_id == user_id)
            .count()
        )

        if total == 0:
            return 0.0

        completed = (
            self._session.query(RecommendationRecord)
            .filter(
                RecommendationRecord.user_id == user_id,
                RecommendationRecord.is_completed == True,
            )
            .count()
        )

        return round(completed / total, 3)


# ══════════════════════════════════════════════════════════════
# BENCHMARK REPOSITORY
# ══════════════════════════════════════════════════════════════

class BenchmarkRepository:
    """
    Repository for BenchmarkRun CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def save_run(
        self,
        run_id: str,
        experiment_name: str,
        benchmark_file: str,
        evaluators_used: list[str],
        total_answers: int,
        mae: float,
        rmse: float,
        pearson_r: float,
        spearman_r: float,
        notes: str = "",
    ) -> BenchmarkRun:
        """
        Save a benchmark run result.

        Args:
            run_id: Unique run identifier.
            experiment_name: Experiment label.
            benchmark_file: Source benchmark file.
            evaluators_used: List of active evaluators.
            total_answers: Answers evaluated.
            mae: Mean Absolute Error.
            rmse: Root Mean Squared Error.
            pearson_r: Pearson correlation.
            spearman_r: Spearman correlation.
            notes: Optional run notes.

        Returns:
            Created BenchmarkRun record.
        """
        run = BenchmarkRun(
            run_id=run_id,
            experiment_name=experiment_name,
            benchmark_file=benchmark_file,
            evaluators_used=json.dumps(evaluators_used),
            total_answers=total_answers,
            mae=mae,
            rmse=rmse,
            pearson_r=pearson_r,
            spearman_r=spearman_r,
            notes=notes,
        )
        self._session.add(run)
        self._session.flush()
        return run

    def get_all_runs(self, limit: int = 20) -> list[BenchmarkRun]:
        """Get all benchmark runs ordered by date."""
        return (
            self._session.query(BenchmarkRun)
            .order_by(BenchmarkRun.run_at.desc())
            .limit(limit)
            .all()
        )

    def get_best_run(self) -> Optional[BenchmarkRun]:
        """Get the benchmark run with highest Pearson R."""
        return (
            self._session.query(BenchmarkRun)
            .order_by(BenchmarkRun.pearson_r.desc())
            .first()
        )


# ══════════════════════════════════════════════════════════════
# AI DECISION LOG REPOSITORY
# ══════════════════════════════════════════════════════════════

class AIDecisionLogRepository:
    """
    Repository for AIDecisionLog CRUD operations.

    Provides structured access to the AI audit trail.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        self._session = session

    def log(
        self,
        decision_type: str,
        input_summary: str = "",
        output_summary: str = "",
        reasoning: str = "",
        confidence: float = 1.0,
        session_id: Optional[str] = None,
    ) -> AIDecisionLog:
        """
        Write a new AI decision log entry.

        Args:
            decision_type: Type of AI decision (e.g. evaluation, recommendation).
            input_summary: Summary of the decision input.
            output_summary: Summary of the decision output.
            reasoning: Why the AI made this decision.
            confidence: Confidence in this decision 0.0-1.0.
            session_id: Optional session context.

        Returns:
            Created AIDecisionLog record.
        """
        entry = AIDecisionLog(
            session_id=session_id,
            decision_type=decision_type,
            input_summary=input_summary,
            output_summary=output_summary,
            reasoning=reasoning,
            confidence=confidence,
        )
        self._session.add(entry)
        self._session.flush()
        return entry

    def get_recent(
        self,
        decision_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[AIDecisionLog]:
        """
        Get recent decision logs.

        Args:
            decision_type: Filter by type if provided.
            limit: Maximum records to return.

        Returns:
            Recent logs ordered by time descending.
        """
        query = self._session.query(AIDecisionLog)
        if decision_type:
            query = query.filter(AIDecisionLog.decision_type == decision_type)
        return (
            query
            .order_by(AIDecisionLog.logged_at.desc())
            .limit(limit)
            .all()
        )

    def get_for_session(self, session_id: str) -> list[AIDecisionLog]:
        """Get all decision logs for a specific session."""
        return (
            self._session.query(AIDecisionLog)
            .filter(AIDecisionLog.session_id == session_id)
            .order_by(AIDecisionLog.logged_at.asc())
            .all()
        )
