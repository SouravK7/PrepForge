"""
SQLAlchemy database models.

Defines all database tables as SQLAlchemy ORM classes.
All tables follow the schema defined in ARCHITECTURE_FREEZE_v1.md.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """
    User account table.

    Stores authentication credentials and profile information.
    All interview sessions and scores belong to a user.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(200), nullable=True)
    target_role = Column(String(100), nullable=True)
    experience_level = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    competency_scores = relationship("CompetencyScore", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRecord", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"


class InterviewSession(Base):
    """
    Interview session table.

    Tracks one complete interview attempt by a user.
    Contains aggregate scores computed after session completion.
    """

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=True)
    experience_level = Column(String(100), nullable=True)
    status = Column(String(50), default="in_progress", nullable=False)
    overall_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    hr_score = Column(Float, default=0.0)
    readiness_level = Column(String(50), nullable=True)
    total_questions = Column(Integer, default=0)
    answered_questions = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationRecord", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session id={self.id} role={self.job_role} status={self.status}>"


class Answer(Base):
    """
    User answer table.

    Stores the raw text of each answer submitted during an interview session.
    Linked to one session, one user, and one question.
    """

    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(100), nullable=False)
    competency_id = Column(String(100), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)
    answer_text = Column(Text, nullable=False)
    time_taken = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("InterviewSession", back_populates="answers")
    evaluation = relationship("EvaluationRecord", back_populates="answer", uselist=False)

    def __repr__(self) -> str:
        return f"<Answer id={self.id} question={self.question_id}>"


class EvaluationRecord(Base):
    """
    AI evaluation output table.

    Stores the complete output from the evaluation ensemble
    for each answer. One evaluation per answer.
    """

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(100), nullable=False)
    competency_id = Column(String(100), nullable=False, index=True)

    # Scores
    semantic_score = Column(Float, default=0.0)
    concept_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    evidence_score = Column(Float, default=0.0)
    reasoning_score = Column(Float, default=0.0)
    weighted_final = Column(Float, default=0.0)
    grade = Column(String(5), nullable=True)
    readiness_level = Column(String(50), nullable=True)

    # Evidence and explanation stored as JSON strings
    matched_concepts = Column(Text, nullable=True)
    missing_concepts = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    competency_delta = Column(Float, default=0.0)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    answer = relationship("Answer", back_populates="evaluation")
    session = relationship("InterviewSession", back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id} score={self.weighted_final}>"


class CompetencyScore(Base):
    """
    Competency confidence score table.

    Tracks each user's Elo rating and confidence score
    per competency. Updated after every evaluation.
    One record per (user_id, competency_id) pair.
    """

    __tablename__ = "competency_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, default=0.0)
    elo_rating = Column(Float, default=1000.0)
    evidence_count = Column(Integer, default=0)
    improvement_trend = Column(Float, default=0.0)
    last_assessed = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "competency_id", name="uq_user_competency"),
    )

    # Relationships
    user = relationship("User", back_populates="competency_scores")

    def __repr__(self) -> str:
        return (
            f"<CompetencyScore user={self.user_id} "
            f"comp={self.competency_id} "
            f"conf={self.confidence:.2f}>"
        )


class RecommendationRecord(Base):
    """
    Recommendation table.

    Stores personalized learning recommendations
    generated after each interview session.
    """

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id = Column(String(100), nullable=False, index=True)
    competency_name = Column(String(200), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    resource_url = Column(String(500), nullable=True)
    resource_type = Column(String(50), nullable=True)
    priority = Column(String(20), default="medium")
    week_number = Column(Integer, default=1)
    estimated_hours = Column(Float, default=2.0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} comp={self.competency_id}>"


class Resume(Base):
    """
    Resume storage table.

    Stores parsed resume data for a user.
    One active resume per user at a time.
    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(300), nullable=False)
    raw_text = Column(Text, nullable=True)
    extracted_skills = Column(Text, nullable=True)
    extracted_education = Column(Text, nullable=True)
    extracted_experience = Column(Text, nullable=True)
    resume_quality_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    parsed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} user={self.user_id} file={self.file_name}>"


class BenchmarkRun(Base):
    """
    Benchmark run result table.

    Stores metrics from each benchmark validation run.
    Used to track evaluator improvement over time.
    """

    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)
    experiment_name = Column(String(200), nullable=False)
    benchmark_file = Column(String(200), nullable=False)
    evaluators_used = Column(Text, nullable=True)
    total_answers = Column(Integer, default=0)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    pearson_r = Column(Float, nullable=True)
    spearman_r = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<BenchmarkRun id={self.id} "
            f"experiment={self.experiment_name} "
            f"pearson={self.pearson_r}>"
        )


class AIDecisionLog(Base):
    """
    AI decision audit log table.

    Every significant AI decision is logged here for
    transparency, debugging, and audit purposes.
    """

    __tablename__ = "ai_decision_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=True, index=True)
    decision_type = Column(String(100), nullable=False, index=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AIDecisionLog id={self.id} type={self.decision_type}>"
