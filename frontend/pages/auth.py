"""
Authentication page.

Login and registration UI.
"""

from __future__ import annotations

import streamlit as st
from frontend.api_client import APIClient
from frontend.session_state import set_authenticated

ROLES = [
    "Software Engineer",
    "Data Analyst",
    "AI Engineer",
    "Web Developer",
    "Data Scientist",
]

EXPERIENCE_LEVELS = [
    "Fresher (0-1 years)",
    "Junior (1-3 years)",
    "Mid-Level (3-5 years)",
    "Senior (5+ years)",
]


def render() -> None:
    """Render the authentication page."""
    st.markdown("# PrepForge AI")
    st.markdown("*Competency-driven adaptive interview preparation*")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        _render_login()

    with tab_register:
        _render_register()


def _render_login() -> None:
    """Render login form."""
    st.markdown("### Login to Your Account")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button(
            "Login", use_container_width=True, type="primary"
        )

    if submit:
        if not username or not password:
            st.error("Please enter username and password.")
            return

        client = APIClient()
        try:
            with st.spinner("Logging in..."):
                result = client.login(username, password)

            set_authenticated(
                token=result["access_token"],
                user_id=result["user_id"],
                username=result["username"],
                target_role=result.get("target_role", "Software Engineer"),
            )
            st.session_state.current_page = "home"
            st.success("Login successful!")
            st.rerun()

        except ValueError as e:
            st.error(str(e))


def _render_register() -> None:
    """Render registration form."""
    st.markdown("### Create New Account")

    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        full_name = st.text_input("Full Name (optional)", key="reg_name")
        target_role = st.selectbox("Target Job Role", ROLES, key="reg_role")
        experience = st.selectbox(
            "Experience Level", EXPERIENCE_LEVELS, key="reg_exp"
        )
        submit = st.form_submit_button(
            "Create Account", use_container_width=True, type="primary"
        )

    if submit:
        if not username or not email or not password:
            st.error("Username, email, and password are required.")
            return

        client = APIClient()
        try:
            with st.spinner("Creating account..."):
                result = client.register(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    target_role=target_role,
                    experience_level=experience,
                )

            set_authenticated(
                token=result["access_token"],
                user_id=result["user_id"],
                username=result["username"],
                target_role=result.get("target_role", target_role),
            )
            st.session_state.current_page = "home"
            st.success("Account created! Welcome to PrepForge.")
            st.rerun()

        except ValueError as e:
            st.error(str(e))
