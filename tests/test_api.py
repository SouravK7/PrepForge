"""
Tests for FastAPI routes.

Validates that endpoints return correct status codes,
parse schemas correctly, and call the underlying services.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.dependencies import get_db, get_current_user
from database.models import Base, User
from schemas.report_schema import SessionSummary
from schemas.evaluation_schema import ReadinessEnum


# ─── Test Database Setup ─────────────────────────────────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_active=True,
        target_role="Software Engineer",
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


# ─── Tests ───────────────────────────────────────────────────

def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


@patch("api.routes.auth_routes.UserRepository")
@patch("api.routes.auth_routes.create_access_token")
def test_register(mock_create_token, mock_user_repo) -> None:
    """Test user registration."""
    # Setup mocks
    mock_repo_instance = MagicMock()
    mock_user = MagicMock(id=1, username="newuser", target_role="Software Engineer")
    mock_repo_instance.create.return_value = mock_user
    mock_user_repo.return_value = mock_repo_instance
    mock_create_token.return_value = "fake-token"

    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "target_role": "Data Analyst",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["access_token"] == "fake-token"
    assert data["username"] == "newuser"


@patch("api.routes.interview_routes.InterviewService")
def test_start_session(mock_service) -> None:
    """Test starting an interview session."""
    mock_instance = MagicMock()
    mock_instance.start_session.return_value = MagicMock(
        session_id=1,
        job_role="Software Engineer",
        blueprint=[{"phase": "introduction", "count": 1, "type": "hr"}],
        first_question=None,
    )
    mock_service.return_value = mock_instance

    response = client.post(
        "/api/interview/start",
        json={"job_role": "Software Engineer"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == 1
    assert data["job_role"] == "Software Engineer"


@patch("api.routes.interview_routes.EvaluationService")
def test_submit_answer(mock_service) -> None:
    """Test submitting an answer."""
    mock_instance = MagicMock()
    mock_eval = MagicMock()
    mock_eval.session_id = 1
    mock_eval.scores.semantic = 80.0
    mock_eval.scores.concept = 80.0
    mock_eval.scores.communication = 80.0
    mock_eval.scores.evidence = 80.0
    mock_eval.scores.reasoning = 80.0
    mock_eval.scores.weighted_final = 80.0
    mock_eval.grade.value = "B"
    mock_eval.readiness_level.value = "good"
    mock_eval.evidence.matched_concepts = []
    mock_eval.evidence.missing_concepts = []
    mock_eval.evidence.strengths = []
    mock_eval.evidence.weaknesses = []
    mock_eval.explanation.semantic_reason = ""
    mock_eval.explanation.concept_reason = ""
    mock_eval.explanation.communication_reason = ""
    mock_eval.explanation.evidence_reason = ""
    mock_eval.explanation.reasoning_reason = ""
    mock_eval.explanation.overall_summary = ""
    mock_eval.explanation.improvement_tip = ""
    mock_eval.competency_delta = 0.1

    mock_instance.evaluate_answer.return_value = MagicMock(
        evaluation=mock_eval,
        answer_id=1,
    )
    mock_service.return_value = mock_instance

    response = client.post(
        "/api/interview/submit-answer",
        json={
            "session_id": 1,
            "question_id": "q1",
            "competency_id": "comp1",
            "question_text": "text",
            "sample_answer": "sample",
            "user_answer": "my answer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer_id"] == 1
    assert data["scores"]["weighted_final"] == 80.0


@patch("api.routes.analytics_routes.AnalyticsService")
def test_get_dashboard(mock_service) -> None:
    """Test dashboard endpoint."""
    mock_instance = MagicMock()
    mock_instance.get_dashboard_stats.return_value = {
        "overview": {"total_sessions": 5}
    }
    mock_service.return_value = mock_instance

    response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    assert response.json()["overview"]["total_sessions"] == 5


@patch("api.routes.competency_routes.CompetencyService")
def test_get_readiness(mock_service) -> None:
    """Test overall readiness endpoint."""
    mock_instance = MagicMock()
    mock_instance.get_overall_readiness.return_value = 86.0
    mock_service.return_value = mock_instance

    response = client.get("/api/competencies/readiness?job_role=AI Engineer")

    assert response.status_code == 200
    data = response.json()
    assert data["readiness_percentage"] == 86.0
    assert data["readiness_label"] == "Excellent"

