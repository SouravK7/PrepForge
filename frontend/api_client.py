"""
API client for Streamlit frontend.

All HTTP calls to the FastAPI backend go through this class.
No page imports requests directly.
"""

from __future__ import annotations

from typing import Any, Optional

import requests


class APIClient:
    """
    HTTP client for the FastAPI backend.

    Handles authentication headers, error formatting,
    and response parsing for all API calls.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        token: Optional[str] = None,
    ) -> None:
        """
        Initialize API client.

        Args:
            base_url: FastAPI backend base URL.
            token: JWT access token for authenticated requests.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        """
        Make a GET request.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            ValueError: On HTTP error.
        """
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                params=params,
                timeout=30,
            )
            if not response.ok:
                error = response.json().get("detail", response.text)
                raise ValueError(f"API error {response.status_code}: {error}")
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ValueError(
                "Cannot connect to backend. "
                "Make sure the API server is running."
            )

    def _post(self, path: str, data: dict) -> dict | list:
        """
        Make a POST request.

        Args:
            path: API endpoint path.
            data: Request body.

        Returns:
            Parsed JSON response.

        Raises:
            ValueError: On HTTP error.
        """
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=data,
                timeout=60,
            )
            if not response.ok:
                error = response.json().get("detail", response.text)
                raise ValueError(f"API error {response.status_code}: {error}")
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ValueError(
                "Cannot connect to backend. "
                "Make sure the API server is running."
            )

    def _put(self, path: str, data: dict | None = None) -> dict:
        """Make a PUT request."""
        try:
            response = requests.put(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=data or {},
                timeout=30,
            )
            if not response.ok:
                error = response.json().get("detail", response.text)
                raise ValueError(f"API error {response.status_code}: {error}")
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ValueError("Cannot connect to backend.")

    # ── Auth ───────────────────────────────────────────────────

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        target_role: str = "Software Engineer",
        experience_level: str = "Fresher (0-1 years)",
    ) -> dict:
        """Register a new user."""
        return self._post("/api/auth/register", {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "target_role": target_role,
            "experience_level": experience_level,
        })

    def login(self, username: str, password: str) -> dict:
        """Login and receive JWT token."""
        return self._post("/api/auth/login", {
            "username": username,
            "password": password,
        })

    def get_profile(self) -> dict:
        """Get current user profile."""
        return self._get("/api/auth/me")

    def update_profile(self, data: dict) -> dict:
        """Update user profile."""
        return self._put("/api/auth/me", data)

    # ── Interview ──────────────────────────────────────────────

    def start_session(
        self,
        job_role: str,
        difficulty: str = "intermediate",
        experience_level: str = "",
        total_questions: int = 10,
    ) -> dict:
        """Start a new interview session."""
        return self._post("/api/interview/start", {
            "job_role": job_role,
            "difficulty": difficulty,
            "experience_level": experience_level,
            "total_questions": total_questions,
        })

    def get_next_question(
        self,
        session_id: int,
        asked_question_ids: list[str],
        last_score: float | None = None,
        last_competency_id: str | None = None,
        question_number: int = 1,
        total_questions: int = 10,
    ) -> dict:
        """Get next adaptive question."""
        return self._post("/api/interview/next-question", {
            "session_id": session_id,
            "asked_question_ids": asked_question_ids,
            "last_score": last_score,
            "last_competency_id": last_competency_id,
            "question_number": question_number,
            "total_questions": total_questions,
        })

    def submit_answer(self, answer_data: dict) -> dict:
        """Submit answer and get evaluation."""
        return self._post("/api/interview/submit-answer", answer_data)

    def complete_session(
        self,
        session_id: int,
        evaluation_scores: list[float],
        technical_scores: list[float],
        hr_scores: list[float],
        answered_questions: int,
    ) -> dict:
        """Complete interview session."""
        return self._post("/api/interview/complete", {
            "session_id": session_id,
            "evaluation_scores": evaluation_scores,
            "technical_scores": technical_scores,
            "hr_scores": hr_scores,
            "answered_questions": answered_questions,
        })

    def get_session_history(self, limit: int = 10) -> list:
        """Get completed session history."""
        return self._get("/api/interview/history", {"limit": limit})

    def get_session_details(self, session_id: int) -> dict:
        """Get session details."""
        return self._get(f"/api/interview/session/{session_id}")

    # ── Evaluation ─────────────────────────────────────────────

    def get_session_evaluations(self, session_id: int) -> list:
        """Get evaluations for a session."""
        return self._get(f"/api/evaluation/session/{session_id}")

    # ── Competencies ───────────────────────────────────────────

    def get_skill_graph(self, job_role: str = "Software Engineer") -> dict:
        """Get skill confidence graph."""
        return self._get("/api/competencies/graph", {"job_role": job_role})

    def get_skill_gaps(
        self,
        job_role: str = "Software Engineer",
        top_n: int = 10,
    ) -> list:
        """Get prioritized skill gaps."""
        return self._get(
            "/api/competencies/gaps",
            {"job_role": job_role, "top_n": top_n},
        )

    def get_readiness(self, job_role: str = "Software Engineer") -> dict:
        """Get overall readiness percentage."""
        return self._get(
            "/api/competencies/readiness",
            {"job_role": job_role},
        )

    def get_competency_scores(self) -> list:
        """Get all competency scores."""
        return self._get("/api/competencies/scores")

    # ── Recommendations ────────────────────────────────────────

    def generate_recommendations(
        self,
        session_id: int,
        target_role: str = "Software Engineer",
        max_weeks: int = 6,
    ) -> dict:
        """Generate and save recommendations."""
        return self._post("/api/recommendations/generate", {
            "session_id": session_id,
            "target_role": target_role,
            "max_weeks": max_weeks,
        })

    def get_recommendations(
        self,
        completed: bool | None = None,
    ) -> list:
        """Get saved recommendations."""
        params: dict[str, Any] = {}
        if completed is not None:
            params["completed"] = completed
        return self._get("/api/recommendations/", params)

    def mark_recommendation_completed(
        self,
        recommendation_id: int,
    ) -> dict:
        """Mark recommendation as completed."""
        return self._put(
            f"/api/recommendations/{recommendation_id}/complete"
        )

    def get_next_steps(
        self,
        target_role: str = "Software Engineer",
        top_n: int = 3,
    ) -> list:
        """Get immediate next step recommendations."""
        return self._get(
            "/api/recommendations/next-steps",
            {"target_role": target_role, "top_n": top_n},
        )

    # ── Analytics ──────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        """Get dashboard statistics."""
        return self._get("/api/analytics/dashboard")

    def get_score_trend(
        self,
        job_role: str | None = None,
        limit: int = 10,
    ) -> list:
        """Get score trend data."""
        params: dict[str, Any] = {"limit": limit}
        if job_role:
            params["job_role"] = job_role
        return self._get("/api/analytics/score-trend", params)

    def get_competency_radar(self) -> dict:
        """Get competency radar chart data."""
        return self._get("/api/analytics/competency-radar")

    # ── Benchmark ──────────────────────────────────────────────

    def run_benchmark(
        self,
        benchmark_file: str = "oop_benchmark_v1",
        experiment_name: str = "full_ensemble",
    ) -> dict:
        """Run benchmark validation."""
        return self._post("/api/benchmark/run", {
            "benchmark_file": benchmark_file,
            "experiment_name": experiment_name,
            "save_report": True,
        })

    def get_benchmark_history(self) -> list:
        """Get benchmark run history."""
        return self._get("/api/benchmark/history")

    # ── System ─────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Check if backend is reachable."""
        try:
            self._get("/health")
            return True
        except Exception:
            return False
