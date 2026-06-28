"""
Database package.

Provides SQLAlchemy models, session management,
and repository pattern for all persistence operations.

Usage:
    from database import get_session, init_db
    from database.repositories import (
        UserRepository,
        SessionRepository,
        AnswerRepository,
        EvaluationRepository,
        CompetencyScoreRepository,
        RecommendationRepository,
    )
"""

from database.db_setup import init_db, get_session, engine
from database.repositories import (
    UserRepository,
    SessionRepository,
    AnswerRepository,
    EvaluationRepository,
    CompetencyScoreRepository,
    RecommendationRepository,
    BenchmarkRepository,
    AIDecisionLogRepository,
)

__all__ = [
    "init_db",
    "get_session",
    "engine",
    "UserRepository",
    "SessionRepository",
    "AnswerRepository",
    "EvaluationRepository",
    "CompetencyScoreRepository",
    "RecommendationRepository",
    "BenchmarkRepository",
    "AIDecisionLogRepository",
]
