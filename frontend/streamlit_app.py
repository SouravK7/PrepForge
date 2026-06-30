"""
Streamlit application main entry point.

Routes page navigation, initializes session state,
and renders the sidebar and selected page.
"""

from __future__ import annotations

import streamlit as st

from frontend.session_state import init_session_state, is_authenticated
from frontend.components.sidebar import render_sidebar
from frontend.api_client import APIClient


def main() -> None:
    """
    Main Streamlit application entry point.

    Configures the page, initializes session state,
    renders the sidebar, and dispatches to the correct page.
    """
    st.set_page_config(
        page_title="PrepForge AI — Interview Prep",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()

    # Backend health check banner
    client = APIClient()
    if not client.health_check():
        st.error(
            "Backend API is not reachable at http://127.0.0.1:8000. "
            "Start it with:  uvicorn api.main:app --reload"
        )

    # Render sidebar and get current page
    render_sidebar()
    current_page = st.session_state.get("current_page", "home")

    # Redirect unauthenticated users trying to access protected pages
    protected_pages = {
        "interview", "results", "dashboard", "skill_map", "recommendations"
    }
    if current_page in protected_pages and not is_authenticated():
        current_page = "auth"
        st.session_state.current_page = "auth"

    # ── Page dispatcher ────────────────────────────────────────
    if current_page == "home":
        from frontend.pages.home import render
        render()

    elif current_page == "auth":
        from frontend.pages.auth import render
        render()

    elif current_page == "interview":
        from frontend.pages.interview import render
        render()

    elif current_page == "results":
        from frontend.pages.results import render
        render()

    elif current_page == "dashboard":
        from frontend.pages.dashboard import render
        render()

    elif current_page == "skill_map":
        from frontend.pages.skill_map import render
        render()

    elif current_page == "recommendations":
        from frontend.pages.recommendations import render
        render()

    else:
        st.error(f"Unknown page: {current_page}")
        st.session_state.current_page = "home"
        st.rerun()
