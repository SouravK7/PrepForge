"""
Tests for the database layer.

Tests all repositories using an in-memory SQLite database.
No fixtures depend on external services.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.repositories import (
    AnswerRepository,
    BenchmarkRepository,
    AIDecisionLogRepository,
    CompetencyScoreRepository,
    EvaluationRepository,
    RecommendationRepository,
    SessionRepository,
    UserRepository,
)
from schemas.competency_schema import CompetencyScore as CompetencyScoreSchema


# ─── Test Database Setup ─────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """
    Provide an isolated in-memory SQLite session per test.

    Creates all tables fresh for each test and tears them down after.
    """
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


# ─── Helpers ─────────────────────────────────────────────────

def create_test_user(session, username: str = "testuser") -> int:
    """Create a user and return its ID."""
    repo = UserRepository(session)
    user = repo.create(
        username=username,
        email=f"{username}@test.com",
        password="password123",
        full_name="Test User",
        target_role="Software Engineer",
        experience_level="entry_level",
    )
    session.flush()
    return user.id


def create_test_session(session, user_id: int) -> int:
    """Create an interview session and return its ID."""
    repo = SessionRepository(session)
    s = repo.create(
        user_id=user_id,
        job_role="Software Engineer",
        difficulty="intermediate",
        total_questions=5,
    )
    session.flush()
    return s.id


def create_test_answer(session, session_id: int, user_id: int) -> int:
    """Create an answer and return its ID."""
    repo = AnswerRepository(session)
    a = repo.create(
        session_id=session_id,
        user_id=user_id,
        question_id="q_se_oop_001",
        competency_id="comp_se_oop",
        question_text="Explain OOP.",
        question_type="technical",
        answer_text="OOP stands for Object Oriented Programming.",
        time_taken=60,
    )
    session.flush()
    return a.id


# ─── UserRepository Tests ────────────────────────────────────

class TestUserRepository:
    """Tests for UserRepository."""

    def test_create_user(self, db_session) -> None:
        """create() persists a new user."""
        repo = UserRepository(db_session)
        user = repo.create(
            username="alice",
            email="alice@test.com",
            password="secret",
        )
        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@test.com"
        assert user.is_active is True

    def test_password_is_hashed(self, db_session) -> None:
        """Passwords are not stored in plain text."""
        repo = UserRepository(db_session)
        user = repo.create(
            username="alice",
            email="alice@test.com",
            password="myplainpassword",
        )
        assert user.password_hash != "myplainpassword"
        assert len(user.password_hash) == 64  # SHA-256 hex digest

    def test_get_by_id(self, db_session) -> None:
        """get_by_id() returns correct user."""
        user_id = create_test_user(db_session)
        repo = UserRepository(db_session)
        user = repo.get_by_id(user_id)
        assert user is not None
        assert user.id == user_id

    def test_get_by_id_missing_returns_none(self, db_session) -> None:
        """get_by_id() returns None for unknown id."""
        repo = UserRepository(db_session)
        assert repo.get_by_id(9999) is None

    def test_get_by_username(self, db_session) -> None:
        """get_by_username() finds user by username."""
        create_test_user(db_session, "bob")
        repo = UserRepository(db_session)
        user = repo.get_by_username("bob")
        assert user is not None
        assert user.username == "bob"

    def test_get_by_username_missing_returns_none(self, db_session) -> None:
        """get_by_username() returns None for unknown username."""
        repo = UserRepository(db_session)
        assert repo.get_by_username("nonexistent") is None

    def test_authenticate_valid_credentials(self, db_session) -> None:
        """authenticate() returns user on valid credentials."""
        repo = UserRepository(db_session)
        repo.create(username="carol", email="carol@test.com", password="pass123")
        db_session.flush()

        user = repo.authenticate("carol", "pass123")
        assert user is not None
        assert user.username == "carol"

    def test_authenticate_wrong_password(self, db_session) -> None:
        """authenticate() returns None on wrong password."""
        repo = UserRepository(db_session)
        repo.create(username="carol", email="carol@test.com", password="pass123")
        db_session.flush()

        user = repo.authenticate("carol", "wrongpassword")
        assert user is None

    def test_authenticate_inactive_user(self, db_session) -> None:
        """authenticate() returns None for inactive accounts."""
        repo = UserRepository(db_session)
        user_id = create_test_user(db_session)
        repo.deactivate(user_id)
        db_session.flush()

        user = repo.authenticate("testuser", "password123")
        assert user is None

    def test_update_profile(self, db_session) -> None:
        """update_profile() modifies user fields."""
        user_id = create_test_user(db_session)
        repo = UserRepository(db_session)
        updated = repo.update_profile(
            user_id=user_id,
            full_name="Updated Name",
            target_role="Data Analyst",
        )
        assert updated is not None
        assert updated.full_name == "Updated Name"
        assert updated.target_role == "Data Analyst"

    def test_deactivate(self, db_session) -> None:
        """deactivate() sets is_active to False."""
        user_id = create_test_user(db_session)
        repo = UserRepository(db_session)
        result = repo.deactivate(user_id)
        assert result is True

        user = repo.get_by_id(user_id)
        assert user.is_active is False

    def test_deactivate_missing_user(self, db_session) -> None:
        """deactivate() returns False for unknown user."""
        repo = UserRepository(db_session)
        assert repo.deactivate(9999) is False


# ─── SessionRepository Tests ─────────────────────────────────

class TestSessionRepository:
    """Tests for SessionRepository."""

    def test_create_session(self, db_session) -> None:
        """create() persists a new interview session."""
        user_id = create_test_user(db_session)
        repo = SessionRepository(db_session)
        s = repo.create(
            user_id=user_id,
            job_role="Software Engineer",
            difficulty="intermediate",
            total_questions=10,
        )
        assert s.id is not None
        assert s.status == "in_progress"
        assert s.job_role == "Software Engineer"

    def test_get_by_id(self, db_session) -> None:
        """get_by_id() returns correct session."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = SessionRepository(db_session)
        s = repo.get_by_id(session_id)
        assert s is not None
        assert s.id == session_id

    def test_get_user_sessions(self, db_session) -> None:
        """get_user_sessions() returns all user sessions."""
        user_id = create_test_user(db_session)
        repo = SessionRepository(db_session)
        repo.create(user_id=user_id, job_role="Software Engineer")
        repo.create(user_id=user_id, job_role="Data Analyst")
        db_session.flush()

        sessions = repo.get_user_sessions(user_id)
        assert len(sessions) == 2

    def test_complete_session(self, db_session) -> None:
        """complete_session() updates status and scores."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = SessionRepository(db_session)

        completed = repo.complete_session(
            session_id=session_id,
            overall_score=75.0,
            technical_score=70.0,
            hr_score=85.0,
            readiness_level="good",
            answered_questions=5,
        )

        assert completed.status == "completed"
        assert completed.overall_score == 75.0
        assert completed.readiness_level == "good"
        assert completed.completed_at is not None

    def test_get_completed_sessions(self, db_session) -> None:
        """get_completed_sessions() only returns completed."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = SessionRepository(db_session)

        # One in-progress, one completed
        create_test_session(db_session, user_id)
        repo.complete_session(
            session_id=session_id,
            overall_score=70.0,
            technical_score=70.0,
            hr_score=70.0,
            readiness_level="good",
            answered_questions=5,
        )

        completed = repo.get_completed_sessions(user_id)
        assert len(completed) == 1
        assert completed[0].status == "completed"

    def test_get_score_trend(self, db_session) -> None:
        """get_score_trend() returns list of dicts."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = SessionRepository(db_session)
        repo.complete_session(
            session_id=session_id,
            overall_score=65.0,
            technical_score=60.0,
            hr_score=75.0,
            readiness_level="average",
            answered_questions=4,
        )

        trend = repo.get_score_trend(user_id)
        assert isinstance(trend, list)
        assert len(trend) == 1
        assert trend[0]["score"] == 65.0


# ─── AnswerRepository Tests ──────────────────────────────────

class TestAnswerRepository:
    """Tests for AnswerRepository."""

    def test_create_answer(self, db_session) -> None:
        """create() persists a new answer."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = AnswerRepository(db_session)

        answer = repo.create(
            session_id=session_id,
            user_id=user_id,
            question_id="q_001",
            competency_id="comp_se_oop",
            question_text="Explain OOP.",
            question_type="technical",
            answer_text="OOP is Object Oriented Programming.",
        )

        assert answer.id is not None
        assert answer.question_id == "q_001"
        assert answer.answer_text == "OOP is Object Oriented Programming."

    def test_get_session_answers(self, db_session) -> None:
        """get_session_answers() returns all answers for session."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)

        repo = AnswerRepository(db_session)
        repo.create(session_id=session_id, user_id=user_id, question_id="q1",
                    competency_id="comp_a", question_text="Q1", question_type="technical",
                    answer_text="A1")
        repo.create(session_id=session_id, user_id=user_id, question_id="q2",
                    competency_id="comp_b", question_text="Q2", question_type="technical",
                    answer_text="A2")
        db_session.flush()

        answers = repo.get_session_answers(session_id)
        assert len(answers) == 2

    def test_get_user_answers_for_competency(self, db_session) -> None:
        """get_user_answers_for_competency() filters correctly."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)

        repo = AnswerRepository(db_session)
        repo.create(session_id=session_id, user_id=user_id, question_id="q1",
                    competency_id="comp_se_oop", question_text="Q1", question_type="technical",
                    answer_text="A1")
        repo.create(session_id=session_id, user_id=user_id, question_id="q2",
                    competency_id="comp_se_databases", question_text="Q2", question_type="technical",
                    answer_text="A2")
        db_session.flush()

        oop_answers = repo.get_user_answers_for_competency(user_id, "comp_se_oop")
        assert len(oop_answers) == 1
        assert oop_answers[0].competency_id == "comp_se_oop"


# ─── CompetencyScoreRepository Tests ─────────────────────────

class TestCompetencyScoreRepository:
    """Tests for CompetencyScoreRepository."""

    def _make_schema(
        self,
        user_id: int,
        comp_id: str = "comp_se_oop",
        confidence: float = 0.4,
    ) -> CompetencyScoreSchema:
        """Helper to create CompetencyScore schema."""
        return CompetencyScoreSchema(
            user_id=user_id,
            competency_id=comp_id,
            confidence=confidence,
            elo_rating=1000.0,
            evidence_count=2,
            improvement_trend=0.05,
        )

    def test_upsert_creates_new(self, db_session) -> None:
        """upsert() creates record when none exists."""
        user_id = create_test_user(db_session)
        repo = CompetencyScoreRepository(db_session)

        schema = self._make_schema(user_id)
        record = repo.upsert(schema)

        assert record.id is not None
        assert record.confidence == 0.4

    def test_upsert_updates_existing(self, db_session) -> None:
        """upsert() updates existing record."""
        user_id = create_test_user(db_session)
        repo = CompetencyScoreRepository(db_session)

        repo.upsert(self._make_schema(user_id, confidence=0.3))
        db_session.flush()

        updated_schema = self._make_schema(user_id, confidence=0.6)
        record = repo.upsert(updated_schema)

        assert record.confidence == 0.6

        # Confirm only one record exists
        all_records = repo.get_all_for_user(user_id)
        assert len(all_records) == 1

    def test_get_all_for_user(self, db_session) -> None:
        """get_all_for_user() returns all competency scores."""
        user_id = create_test_user(db_session)
        repo = CompetencyScoreRepository(db_session)

        repo.upsert(self._make_schema(user_id, "comp_se_oop", 0.4))
        repo.upsert(self._make_schema(user_id, "comp_se_databases", 0.2))
        db_session.flush()

        records = repo.get_all_for_user(user_id)
        assert len(records) == 2

    def test_get_weak_competencies(self, db_session) -> None:
        """get_weak_competencies() filters below threshold."""
        user_id = create_test_user(db_session)
        repo = CompetencyScoreRepository(db_session)

        repo.upsert(self._make_schema(user_id, "comp_se_oop", 0.8))  # strong
        repo.upsert(self._make_schema(user_id, "comp_se_databases", 0.2))  # weak
        db_session.flush()

        weak = repo.get_weak_competencies(user_id, threshold=0.5)
        assert len(weak) == 1
        assert weak[0].competency_id == "comp_se_databases"

    def test_to_schema_dict(self, db_session) -> None:
        """to_schema_dict() returns dict of CompetencyScore schemas."""
        user_id = create_test_user(db_session)
        repo = CompetencyScoreRepository(db_session)

        repo.upsert(self._make_schema(user_id, "comp_se_oop", 0.5))
        db_session.flush()

        schema_dict = repo.to_schema_dict(user_id)
        assert "comp_se_oop" in schema_dict
        assert isinstance(schema_dict["comp_se_oop"], CompetencyScoreSchema)


# ─── RecommendationRepository Tests ─────────────────────────

class TestRecommendationRepository:
    """Tests for RecommendationRepository."""

    def _make_recommendation(self, user_id: int, session_id: int):
        """Create a mock Recommendation schema."""
        from schemas.recommendation_schema import Recommendation
        return Recommendation(
            id="abc12345",
            user_id=user_id,
            session_id=session_id,
            competency_id="comp_se_oop",
            competency_name="OOP",
            title="Study OOP fundamentals",
            description="Review all four OOP pillars.",
            resource=None,
            priority="high",
            week_number=1,
            estimated_hours=3.0,
        )

    def test_create_from_schema(self, db_session) -> None:
        """create_from_schema() persists a recommendation."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = RecommendationRepository(db_session)

        rec = self._make_recommendation(user_id, session_id)
        record = repo.create_from_schema(rec)

        assert record.id is not None
        assert record.competency_id == "comp_se_oop"
        assert record.priority == "high"

    def test_bulk_create(self, db_session) -> None:
        """bulk_create() persists multiple recommendations."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = RecommendationRepository(db_session)

        recs = [self._make_recommendation(user_id, session_id) for _ in range(3)]
        records = repo.bulk_create(recs)

        assert len(records) == 3

    def test_get_user_recommendations(self, db_session) -> None:
        """get_user_recommendations() returns user recs."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = RecommendationRepository(db_session)

        repo.create_from_schema(self._make_recommendation(user_id, session_id))
        db_session.flush()

        recs = repo.get_user_recommendations(user_id)
        assert len(recs) == 1

    def test_mark_completed(self, db_session) -> None:
        """mark_completed() sets is_completed True."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = RecommendationRepository(db_session)

        record = repo.create_from_schema(
            self._make_recommendation(user_id, session_id)
        )
        db_session.flush()

        result = repo.mark_completed(record.id, user_id)
        assert result is True

        recs = repo.get_user_recommendations(user_id, completed=True)
        assert len(recs) == 1

    def test_get_completion_rate(self, db_session) -> None:
        """get_completion_rate() computes correctly."""
        user_id = create_test_user(db_session)
        session_id = create_test_session(db_session, user_id)
        repo = RecommendationRepository(db_session)

        r1 = repo.create_from_schema(self._make_recommendation(user_id, session_id))
        r2 = repo.create_from_schema(self._make_recommendation(user_id, session_id))
        db_session.flush()

        repo.mark_completed(r1.id, user_id)

        rate = repo.get_completion_rate(user_id)
        assert abs(rate - 0.5) < 0.01

    def test_completion_rate_zero_when_no_recs(self, db_session) -> None:
        """get_completion_rate() returns 0.0 when no recommendations."""
        user_id = create_test_user(db_session)
        repo = RecommendationRepository(db_session)
        assert repo.get_completion_rate(user_id) == 0.0


# ─── BenchmarkRepository Tests ───────────────────────────────

class TestBenchmarkRepository:
    """Tests for BenchmarkRepository."""

    def test_save_run(self, db_session) -> None:
        """save_run() persists benchmark run."""
        repo = BenchmarkRepository(db_session)
        run = repo.save_run(
            run_id="run_001",
            experiment_name="full_ensemble",
            benchmark_file="oop_benchmark_v1",
            evaluators_used=["semantic", "concept", "communication"],
            total_answers=8,
            mae=12.04,
            rmse=12.94,
            pearson_r=0.9545,
            spearman_r=0.9048,
        )

        assert run.id is not None
        assert run.pearson_r == 0.9545

    def test_get_all_runs(self, db_session) -> None:
        """get_all_runs() returns all benchmark runs."""
        repo = BenchmarkRepository(db_session)
        repo.save_run("run_001", "exp1", "oop_benchmark_v1", [], 8, 12.0, 13.0, 0.95, 0.90)
        repo.save_run("run_002", "exp2", "hr_benchmark_v1", [], 8, 11.0, 12.0, 0.96, 0.91)
        db_session.flush()

        runs = repo.get_all_runs()
        assert len(runs) == 2

    def test_get_best_run(self, db_session) -> None:
        """get_best_run() returns run with highest Pearson R."""
        repo = BenchmarkRepository(db_session)
        repo.save_run("run_001", "exp1", "oop_benchmark_v1", [], 8, 12.0, 13.0, 0.90, 0.88)
        repo.save_run("run_002", "exp2", "hr_benchmark_v1", [], 8, 11.0, 12.0, 0.97, 0.95)
        db_session.flush()

        best = repo.get_best_run()
        assert best is not None
        assert best.pearson_r == 0.97


# ─── AIDecisionLogRepository Tests ───────────────────────────

class TestAIDecisionLogRepository:
    """Tests for AIDecisionLogRepository."""

    def test_log_entry(self, db_session) -> None:
        """log() persists a decision entry."""
        repo = AIDecisionLogRepository(db_session)
        entry = repo.log(
            decision_type="evaluation",
            input_summary="OOP answer received",
            output_summary="Score: 72.5",
            reasoning="High semantic similarity, 3/4 concepts matched",
            confidence=0.9,
            session_id="session_42",
        )

        assert entry.id is not None
        assert entry.decision_type == "evaluation"

    def test_get_recent(self, db_session) -> None:
        """get_recent() returns recent logs."""
        repo = AIDecisionLogRepository(db_session)
        repo.log(decision_type="evaluation", session_id="s1")
        repo.log(decision_type="recommendation", session_id="s1")
        db_session.flush()

        all_logs = repo.get_recent()
        assert len(all_logs) == 2

    def test_get_recent_filtered_by_type(self, db_session) -> None:
        """get_recent() filters by decision_type."""
        repo = AIDecisionLogRepository(db_session)
        repo.log(decision_type="evaluation")
        repo.log(decision_type="recommendation")
        db_session.flush()

        eval_logs = repo.get_recent(decision_type="evaluation")
        assert len(eval_logs) == 1
        assert eval_logs[0].decision_type == "evaluation"

    def test_get_for_session(self, db_session) -> None:
        """get_for_session() returns logs for specific session."""
        repo = AIDecisionLogRepository(db_session)
        repo.log(decision_type="evaluation", session_id="session_1")
        repo.log(decision_type="evaluation", session_id="session_2")
        db_session.flush()

        session_logs = repo.get_for_session("session_1")
        assert len(session_logs) == 1


# ─── Database Health Check ────────────────────────────────────

class TestDatabaseSetup:
    """Tests for database setup utilities."""

    def test_health_check_passes(self) -> None:
        """health_check() returns True for working database."""
        from database.db_setup import health_check
        assert health_check() is True

    def test_init_db_creates_tables(self) -> None:
        """init_db() creates all tables without error."""
        from database.db_setup import init_db
        init_db()  # Should not raise
