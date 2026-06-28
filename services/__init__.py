"""
Service layer package.

Services orchestrate AI pipelines and database repositories.
They contain business logic only. No ML code. No SQL.

Services:
    InterviewService:       Manages interview session lifecycle.
    EvaluationService:      Orchestrates evaluation pipeline + persistence.
    CompetencyService:      Manages competency score updates and gaps.
    RecommendationService:  Generates and persists recommendations.
    AnalyticsService:       Computes dashboard statistics.
    ReportService:          Generates session reports.
"""

from services.interview_service import InterviewService
from services.evaluation_service import EvaluationService
from services.competency_service import CompetencyService
from services.recommendation_service import RecommendationService
from services.analytics_service import AnalyticsService
from services.report_service import ReportService

__all__ = [
    "InterviewService",
    "EvaluationService",
    "CompetencyService",
    "RecommendationService",
    "AnalyticsService",
    "ReportService",
]
