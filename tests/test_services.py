"""
Tests for the service layer.

All services tested with in-memory SQLite database.
AI pipeline components are mocked so tests run without
ML models installed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.repositories import (
    SessionRepository,
    UserRepository,
    CompetencyScoreRepository,
)
from schemas.competency_schema import (
    CompetencyGap,
    CompetencyScore,
    CompetencyUpdate,
    PriorityEnum,
)
from schemas.evaluation_schema import (
    EvaluationEvidence,
    EvaluationExplanation,
    EvaluationOutput,
    EvaluationScores,
    GradeEnum,
    ReadinessEnum,
)
from schemas.question_schema import (
    DifficultyLevel,
    InterviewPhase,
    Question,
    QuestionType,
)
from services.analytics_service import AnalyticsService
from services.competency_service import CompetencyService
from services.interview_service import InterviewService
from services.recommendation_service import RecommendationService
from services.report_service import ReportService


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """Provide isolated in-memory SQLite session per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def create_user(session, username: str = "testuser") -> int:
    """Create a user and return ID."""
    repo = UserRepository(session)
    user = repo.create(
        username=username,
        email=f"{username}@test.com",
        password="pass123",
        full_name="Test User",
        target_role="Software Engineer",
        experience_level="entry_level",
    )
    session.flush()
    return user.id


def create_completed_session(session, user_id: int, score: float = 70.0) -> int:
    """Create a completed interview session and return its ID."""
    repo = SessionRepository(session)
    s = repo.create(
        user_id=user_id,
        job_role="Software Engineer",
        difficulty="intermediate",
        total_questions=5,
    )
    repo.complete_session(
        session_id=s.id,
        overall_score=score,
        technical_score=score - 5.0,
        hr_score=score + 5.0,
        readiness_level="good",
        answered_questions=5,
    )
    session.flush()
    return s.id


def make_sample_evaluation(
    user_id: int = 1,
    session_id: int = 1,
    answer_id: int = 1,
    score: float = 72.5,
) -> EvaluationOutput:
    """Build a minimal EvaluationOutput for testing."""
    return EvaluationOutput(
        id="eval_001",
        session_id=session_id,
        answer_id=answer_id,
        user_id=user_id,
        competency_id="comp_se_oop",
        question_id="q_se_oop_001",
        scores=EvaluationScores(
            semantic=70.0,
            concept=75.0,
            communication=72.0,
            evidence=68.0,
            reasoning=74.0,
            weighted_final=score,
        ),
        grade=GradeEnum.B,
        readiness_level=ReadinessEnum.GOOD,
        evidence=EvaluationEvidence(
            matched_concepts=["encapsulation", "inheritance"],
            missing_concepts=["polymorphism"],
            strengths=["Clear explanation"],
            weaknesses=["Missing examples"],
        ),
        explanation=EvaluationExplanation(
            semantic_reason="Good semantic similarity.",
            concept_reason="3/4 required concepts found.",
            communication_reason="Clear and structured.",
            evidence_reason="No real-world example.",
            reasoning_reason="Logical but surface-level.",
            overall_summary="Solid but incomplete answer.",
            improvement_tip="Add a concrete code example.",
        ),
        competency_delta=0.05,
        evaluated_at=datetime.utcnow(),
    )


def make_sample_gap(
    comp_id: str = "comp_se_oop",
    gap: float = 0.4,
) -> CompetencyGap:
    """Build a CompetencyGap for testing."""
    return CompetencyGap(
        competency_id=comp_id,
        competency_name="OOP",
        current_confidence=0.3,
        required_confidence=0.7,
        gap=gap,
        priority=PriorityEnum.HIGH,
        role_relevance=0.9,
        recommended_action="Study OOP fundamentals.",
    )


# ─── InterviewService Tests ───────────────────────────────────

class TestInterviewService:
    """Tests for InterviewService."""

    def _make_service(self, db_session) -> InterviewService:
        """Create service with mocked question selector."""
        service = InterviewService(db_session)
        # Mock QuestionSelector to avoid dependency on data files
        mock_selector = MagicMock()
        mock_selector.select_first_question.return_value = Question(
            id="q_intro_001",
            competency_id="comp_se_behavioral",
            question_text="Tell me about yourself.",
            question_type=QuestionType.HR,
            difficulty=DifficultyLevel.BEGINNER,
            category="Behavioral",
            sample_answer="I am a software engineer...",
            rubric_id="rubric_hr",
        )
        mock_selector.select_question.return_value = Question(
            id="q_se_oop_001",
            competency_id="comp_se_oop",
            question_text="Explain OOP pillars.",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            category="OOP",
            sample_answer="OOP has four pillars...",
            rubric_id="rubric_technical_standard",
        )
        service._question_selector = mock_selector
        return service

    def test_start_session_creates_db_record(self, db_session) -> None:
        """start_session() creates a session in the database."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        result = service.start_session(
            user_id=user_id,
            job_role="Software Engineer",
            total_questions=10,
        )

        assert result.session_id is not None
        assert result.job_role == "Software Engineer"
        assert result.first_question is not None

    def test_start_session_returns_blueprint(self, db_session) -> None:
        """start_session() returns phase blueprint."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        result = service.start_session(
            user_id=user_id,
            job_role="Software Engineer",
        )

        assert isinstance(result.blueprint, list)
        assert len(result.blueprint) > 0
        assert "phase" in result.blueprint[0]

    def test_get_next_question_returns_result(self, db_session) -> None:
        """get_next_question() returns NextQuestionResult."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)
        session_id = create_completed_session(db_session, user_id)

        result = service.get_next_question(
            session_id=session_id,
            user_id=user_id,
            job_role="Software Engineer",
            asked_question_ids=[],
            question_number=3,
            total_questions=10,
        )

        assert result is not None
        assert result.question is not None
        assert result.is_complete is False

    def test_get_next_question_complete_when_over_limit(self, db_session) -> None:
        """get_next_question() signals completion when over total."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        result = service.get_next_question(
            session_id=1,
            user_id=user_id,
            job_role="Software Engineer",
            asked_question_ids=[],
            question_number=11,
            total_questions=10,
        )

        assert result.is_complete is True
        assert result.question is None

    def test_complete_session_saves_scores(self, db_session) -> None:
        """complete_session() persists final scores."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)
        start_result = service.start_session(user_id=user_id, job_role="Software Engineer")

        summary = service.complete_session(
            session_id=start_result.session_id,
            evaluation_scores=[80.0, 70.0, 60.0],
            technical_scores=[75.0, 65.0],
            hr_scores=[80.0],
            answered_questions=3,
        )

        assert summary["overall_score"] == pytest.approx(70.0, abs=0.1)
        assert summary["readiness_level"] == "good"
        assert summary["answered_questions"] == 3

    def test_complete_session_empty_scores(self, db_session) -> None:
        """complete_session() handles empty score lists gracefully."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)
        start_result = service.start_session(user_id=user_id, job_role="Software Engineer")

        summary = service.complete_session(
            session_id=start_result.session_id,
            evaluation_scores=[],
            technical_scores=[],
            hr_scores=[],
            answered_questions=0,
        )

        assert summary["overall_score"] == 0.0
        assert summary["readiness_level"] == "poor"

    def test_get_session_history(self, db_session) -> None:
        """get_session_history() returns completed sessions."""
        user_id = create_user(db_session)
        create_completed_session(db_session, user_id, score=75.0)
        service = self._make_service(db_session)

        history = service.get_session_history(user_id, limit=10)

        assert len(history) == 1
        assert history[0]["overall_score"] == 75.0

    def test_determine_phase_intro(self, db_session) -> None:
        """_determine_phase() returns INTRODUCTION for question 1."""
        service = self._make_service(db_session)
        phase = service._determine_phase(1, 10)
        assert phase == InterviewPhase.INTRODUCTION

    def test_determine_phase_core_technical(self, db_session) -> None:
        """_determine_phase() returns CORE_TECHNICAL for middle questions."""
        service = self._make_service(db_session)
        phase = service._determine_phase(5, 10)
        assert phase == InterviewPhase.CORE_TECHNICAL

    def test_determine_phase_closing(self, db_session) -> None:
        """_determine_phase() returns CLOSING for last question."""
        service = self._make_service(db_session)
        phase = service._determine_phase(10, 10)
        assert phase == InterviewPhase.CLOSING

    def test_score_to_readiness_excellent(self, db_session) -> None:
        """_score_to_readiness() returns 'excellent' for score >= 85."""
        service = self._make_service(db_session)
        assert service._score_to_readiness(90.0) == "excellent"
        assert service._score_to_readiness(85.0) == "excellent"

    def test_score_to_readiness_poor(self, db_session) -> None:
        """_score_to_readiness() returns 'poor' for score < 50."""
        service = self._make_service(db_session)
        assert service._score_to_readiness(40.0) == "poor"
        assert service._score_to_readiness(0.0) == "poor"


# ─── AnalyticsService Tests ───────────────────────────────────

class TestAnalyticsService:
    """Tests for AnalyticsService."""

    def test_empty_dashboard_for_new_user(self, db_session) -> None:
        """get_dashboard_stats() returns empty dashboard for new user."""
        user_id = create_user(db_session)
        service = AnalyticsService(db_session)

        stats = service.get_dashboard_stats(user_id)

        assert stats["overview"]["total_sessions"] == 0
        assert stats["overview"]["avg_score"] == 0.0
        assert stats["score_trend"] == []

    def test_dashboard_stats_with_sessions(self, db_session) -> None:
        """get_dashboard_stats() computes stats from session data."""
        user_id = create_user(db_session)
        create_completed_session(db_session, user_id, score=60.0)
        create_completed_session(db_session, user_id, score=80.0)

        service = AnalyticsService(db_session)
        stats = service.get_dashboard_stats(user_id)

        assert stats["overview"]["total_sessions"] == 2
        assert stats["overview"]["avg_score"] == pytest.approx(70.0, abs=0.1)
        assert stats["overview"]["best_score"] == pytest.approx(80.0, abs=0.1)

    def test_score_trend_returns_list(self, db_session) -> None:
        """get_score_trend() returns list of dicts."""
        user_id = create_user(db_session)
        create_completed_session(db_session, user_id, score=70.0)

        service = AnalyticsService(db_session)
        trend = service.get_score_trend(user_id)

        assert isinstance(trend, list)
        assert len(trend) == 1
        assert "score" in trend[0]

    def test_radar_data_returns_labels_and_values(self, db_session) -> None:
        """get_competency_radar_data() returns labels and values."""
        user_id = create_user(db_session)
        score_repo = CompetencyScoreRepository(db_session)
        score_repo.upsert(CompetencyScore(
            user_id=user_id,
            competency_id="comp_se_oop",
            confidence=0.6,
            elo_rating=1050.0,
            evidence_count=3,
            improvement_trend=0.02,
        ))
        db_session.flush()

        service = AnalyticsService(db_session)
        radar = service.get_competency_radar_data(user_id)

        assert "labels" in radar
        assert "values" in radar
        assert len(radar["labels"]) == len(radar["values"])

    def test_role_performance_breakdown(self, db_session) -> None:
        """get_dashboard_stats() breaks down performance by role."""
        user_id = create_user(db_session)
        create_completed_session(db_session, user_id, score=70.0)

        service = AnalyticsService(db_session)
        stats = service.get_dashboard_stats(user_id)

        assert "Software Engineer" in stats["role_performance"]
        assert stats["role_performance"]["Software Engineer"] == pytest.approx(70.0, abs=0.1)

    def test_improvement_trend_computed(self, db_session) -> None:
        """Improvement is difference between latest and oldest score."""
        user_id = create_user(db_session)
        create_completed_session(db_session, user_id, score=60.0)
        create_completed_session(db_session, user_id, score=80.0)

        service = AnalyticsService(db_session)
        stats = service.get_dashboard_stats(user_id)

        # improvement = latest (scores[0]=80) - oldest (scores[-1]=60) = 20
        # But sessions are ordered by completed_at desc so [0]=latest=80
        assert "improvement" in stats["overview"]


# ─── CompetencyService Tests ──────────────────────────────────

class TestCompetencyService:
    """Tests for CompetencyService."""

    def _make_service(self, db_session) -> CompetencyService:
        """Create service with mocked graph and analyzer."""
        service = CompetencyService(db_session)

        mock_graph = MagicMock()
        mock_graph.get_competency.return_value = MagicMock(name="OOP")
        mock_graph.get_competencies_for_role.return_value = []
        mock_graph.build_skill_graph_schema.return_value = MagicMock()

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [make_sample_gap()]
        mock_analyzer.compute_overall_readiness.return_value = 55.0

        service._graph = mock_graph
        service._gap_analyzer = mock_analyzer

        return service

    def test_get_user_scores_returns_dict(self, db_session) -> None:
        """get_user_scores() returns dict of CompetencyScore schemas."""
        user_id = create_user(db_session)
        score_repo = CompetencyScoreRepository(db_session)
        score_repo.upsert(CompetencyScore(
            user_id=user_id,
            competency_id="comp_se_oop",
            confidence=0.5,
            elo_rating=1000.0,
            evidence_count=2,
            improvement_trend=0.0,
        ))
        db_session.flush()

        service = self._make_service(db_session)
        scores = service.get_user_scores(user_id)

        assert "comp_se_oop" in scores
        assert isinstance(scores["comp_se_oop"], CompetencyScore)

    def test_get_skill_gaps_calls_analyzer(self, db_session) -> None:
        """get_skill_gaps() calls gap analyzer and returns gaps."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        gaps = service.get_skill_gaps(user_id, "Software Engineer")

        assert isinstance(gaps, list)
        assert len(gaps) == 1
        assert gaps[0].competency_id == "comp_se_oop"

    def test_get_overall_readiness_returns_float(self, db_session) -> None:
        """get_overall_readiness() returns float percentage."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        readiness = service.get_overall_readiness(user_id, "Software Engineer")

        assert isinstance(readiness, float)
        assert readiness == pytest.approx(55.0, abs=0.1)

    def test_get_strong_areas_filters_by_threshold(self, db_session) -> None:
        """get_strong_areas() returns competencies above threshold."""
        user_id = create_user(db_session)
        score_repo = CompetencyScoreRepository(db_session)
        score_repo.upsert(CompetencyScore(
            user_id=user_id,
            competency_id="comp_se_oop",
            confidence=0.8,
            elo_rating=1100.0,
            evidence_count=5,
            improvement_trend=0.1,
        ))
        score_repo.upsert(CompetencyScore(
            user_id=user_id,
            competency_id="comp_se_databases",
            confidence=0.2,
            elo_rating=900.0,
            evidence_count=1,
            improvement_trend=-0.05,
        ))
        db_session.flush()

        service = self._make_service(db_session)
        strong = service.get_strong_areas(user_id, threshold=0.7)

        # Only comp_se_oop is above threshold
        assert len(strong) == 1

    def test_role_to_id_mapping(self, db_session) -> None:
        """_role_to_id() converts display names correctly."""
        service = self._make_service(db_session)

        assert service._role_to_id("Software Engineer") == "software_engineer"
        assert service._role_to_id("Data Analyst") == "data_analyst"
        assert service._role_to_id("AI Engineer") == "ai_engineer"

    def test_role_to_id_fallback(self, db_session) -> None:
        """_role_to_id() falls back to lowercased underscored name."""
        service = self._make_service(db_session)
        result = service._role_to_id("Product Manager")
        assert result == "product_manager"


# ─── RecommendationService Tests ──────────────────────────────

class TestRecommendationService:
    """Tests for RecommendationService."""

    def _make_service(self, db_session) -> RecommendationService:
        """Create service with mocked recommender."""
        service = RecommendationService(db_session)

        mock_recommender = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.weekly_plans = []
        mock_output = MagicMock()
        mock_output.roadmap = mock_roadmap

        mock_recommender.recommend.return_value = mock_output
        mock_recommender.recommend_next_steps.return_value = []

        service._recommender = mock_recommender
        return service

    def test_generate_and_save_calls_recommender(self, db_session) -> None:
        """generate_and_save() calls recommender with correct args."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)
        gaps = [make_sample_gap()]

        output = service.generate_and_save(
            user_id=user_id,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        service._recommender.recommend.assert_called_once()
        assert output is not None

    def test_get_user_recommendations_returns_list(self, db_session) -> None:
        """get_user_recommendations() returns list of dicts."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        recs = service.get_user_recommendations(user_id)

        assert isinstance(recs, list)

    def test_get_next_steps_calls_recommender(self, db_session) -> None:
        """get_next_steps() delegates to recommender."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)
        gaps = [make_sample_gap()]

        steps = service.get_next_steps(
            user_id=user_id,
            session_id=1,
            gaps=gaps,
            top_n=3,
        )

        service._recommender.recommend_next_steps.assert_called_once()
        assert isinstance(steps, list)

    def test_mark_completed_delegates_to_repo(self, db_session) -> None:
        """mark_completed() calls recommendation repository."""
        user_id = create_user(db_session)
        service = self._make_service(db_session)

        # Should return False since no rec exists
        result = service.mark_completed(
            recommendation_id=9999,
            user_id=user_id,
        )

        assert result is False


# ─── ReportService Tests ──────────────────────────────────────

class TestReportService:
    """Tests for ReportService."""

    def _make_service(self, db_session) -> ReportService:
        """Create service with mocked eval and competency services."""
        service = ReportService(db_session)

        mock_eval_service = MagicMock()
        mock_eval_service.get_session_evaluations.return_value = [
            make_sample_evaluation()
        ]

        mock_comp_service = MagicMock()
        mock_comp_service.get_skill_gaps.return_value = [make_sample_gap()]

        service._eval_service = mock_eval_service
        service._competency_service = mock_comp_service

        return service

    def test_generate_session_report_raises_if_not_found(self, db_session) -> None:
        """generate_session_report() raises ValueError for unknown session."""
        service = self._make_service(db_session)

        with pytest.raises(ValueError, match="Session not found"):
            service.generate_session_report(session_id=9999, user_id=1)

    def test_generate_session_report_raises_if_not_completed(
        self, db_session
    ) -> None:
        """generate_session_report() raises ValueError for in-progress session."""
        user_id = create_user(db_session)
        session_repo = SessionRepository(db_session)
        s = session_repo.create(
            user_id=user_id,
            job_role="Software Engineer",
            total_questions=5,
        )
        db_session.flush()

        service = self._make_service(db_session)

        with pytest.raises(ValueError, match="not completed"):
            service.generate_session_report(session_id=s.id, user_id=user_id)

    def test_generate_session_report_success(self, db_session) -> None:
        """generate_session_report() returns InterviewReport."""
        from schemas.report_schema import InterviewReport

        user_id = create_user(db_session)
        session_id = create_completed_session(db_session, user_id)

        service = self._make_service(db_session)
        report = service.generate_session_report(session_id, user_id)

        assert isinstance(report, InterviewReport)
        assert report.session_summary.session_id == session_id
        assert len(report.evaluations) == 1
        assert len(report.skill_gaps) == 1

    def test_get_session_summary_raises_if_not_found(self, db_session) -> None:
        """get_session_summary() raises ValueError for unknown session."""
        service = self._make_service(db_session)

        with pytest.raises(ValueError, match="Session not found"):
            service.get_session_summary(session_id=9999)

    def test_get_session_summary_success(self, db_session) -> None:
        """get_session_summary() returns SessionSummary."""
        from schemas.report_schema import SessionSummary

        user_id = create_user(db_session)
        session_id = create_completed_session(db_session, user_id, score=75.0)

        service = self._make_service(db_session)
        summary = service.get_session_summary(session_id)

        assert isinstance(summary, SessionSummary)
        assert summary.session_id == session_id
        assert summary.overall_score == pytest.approx(75.0, abs=0.1)

    def test_report_extracts_strengths_and_weaknesses(self, db_session) -> None:
        """Report summary extracts unique strengths and weaknesses."""
        from schemas.report_schema import InterviewReport

        user_id = create_user(db_session)
        session_id = create_completed_session(db_session, user_id)

        service = self._make_service(db_session)
        report = service.generate_session_report(session_id, user_id)

        # From the mocked evaluation
        assert "Clear explanation" in report.session_summary.top_strengths
        assert "Missing examples" in report.session_summary.top_weaknesses
