"""
Streamlit session state management.

Centralizes all session state access and initialization.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from frontend.api_client import APIClient


def init_session_state() -> None:
    """Initialize all session state keys with defaults."""
    defaults: dict = {
        # Auth state
        "authenticated": False,
        "token": None,
        "user_id": None,
        "username": None,
        "target_role": "Software Engineer",
        # Interview state
        "session_id": None,
        "current_question": None,
        "asked_question_ids": [],
        "question_number": 0,
        "total_questions": 10,
        "evaluation_scores": [],
        "technical_scores": [],
        "hr_scores": [],
        "session_evaluations": [],
        "interview_active": False,
        "interview_complete": False,
        # UI state
        "current_page": "home",
        "last_evaluation": None,
        "answer_submitted": False,
        "time_started": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_client() -> APIClient:
    """
    Get API client configured with current token.

    Returns:
        APIClient with auth token if authenticated.
    """
    return APIClient(token=st.session_state.get("token"))


def set_authenticated(
    token: str,
    user_id: int,
    username: str,
    target_role: str,
) -> None:
    """
    Set authenticated state after login.

    Args:
        token: JWT access token.
        user_id: User database ID.
        username: Username.
        target_role: User's target job role.
    """
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.target_role = target_role


def logout() -> None:
    """Clear all authentication state."""
    keys_to_clear = [
        "authenticated", "token", "user_id", "username",
        "target_role", "session_id", "current_question",
        "asked_question_ids", "question_number", "evaluation_scores",
        "technical_scores", "hr_scores", "session_evaluations",
        "interview_active", "interview_complete", "last_evaluation",
        "answer_submitted",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    init_session_state()


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def require_auth() -> bool:
    """
    Check authentication and redirect to auth page if needed.

    Returns:
        True if authenticated, False if redirected.
    """
    if not is_authenticated():
        st.session_state.current_page = "auth"
        return False
    return True


def reset_interview_state() -> None:
    """Reset interview-related state for a new session."""
    st.session_state.session_id = None
    st.session_state.current_question = None
    st.session_state.asked_question_ids = []
    st.session_state.question_number = 0
    st.session_state.evaluation_scores = []
    st.session_state.technical_scores = []
    st.session_state.hr_scores = []
    st.session_state.session_evaluations = []
    st.session_state.interview_active = False
    st.session_state.interview_complete = False
    st.session_state.last_evaluation = None
    st.session_state.answer_submitted = False
