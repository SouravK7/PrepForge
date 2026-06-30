"""
Home page.

Landing page showing readiness summary and quick actions.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import get_api_client, require_auth
from frontend.components.score_cards import readiness_gauge


def render() -> None:
    """Render the home page."""
    if not require_auth():
        return

    client = get_api_client()
    role = st.session_state.get("target_role", "Software Engineer")
    username = st.session_state.get("username", "User")

    st.markdown(f"# Welcome back, {username}")
    st.markdown(f"*Preparing for: **{role}***")
    st.markdown("---")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        try:
            readiness_data = client.get_readiness(role)
            readiness_gauge(
                readiness_data.get("readiness_percentage", 0.0),
                f"{role} Readiness",
            )
        except ValueError:
            st.info("Complete an interview to see your readiness score.")

    with col_right:
        st.markdown("### Quick Actions")

        if st.button("Start New Interview", use_container_width=True, type="primary",
                     key="home_start_interview"):
            st.session_state.current_page = "interview"
            st.rerun()

        if st.button("View Dashboard", use_container_width=True, key="home_dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()

        if st.button("View Skill Map", use_container_width=True, key="home_skillmap"):
            st.session_state.current_page = "skill_map"
            st.rerun()

        if st.button("View Recommendations", use_container_width=True,
                     key="home_recommendations"):
            st.session_state.current_page = "recommendations"
            st.rerun()

    st.markdown("---")
    st.markdown("### Top Skill Gaps to Address")

    try:
        gaps = client.get_skill_gaps(role, top_n=3)
        if gaps:
            for gap in gaps:
                priority = gap.get("priority", "medium")
                name = gap.get("competency_name", "")
                confidence = gap.get("current_confidence", 0) * 100
                action = gap.get("recommended_action", "")

                priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                icon = priority_icons.get(priority, "⚪")

                with st.expander(f"{icon} {name} — Confidence: {confidence:.0f}%"):
                    st.write(action)
        else:
            st.success("No significant skill gaps detected. You are well prepared!")
    except ValueError:
        st.info("Complete an interview to see your skill gaps.")

    st.markdown("---")
    st.markdown("### Recent Sessions")

    try:
        history = client.get_session_history(limit=3)
        if history:
            for session in history:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{session.get('job_role', '')}**")
                    st.caption(session.get("completed_at", ""))
                with col2:
                    score = session.get("overall_score", 0)
                    st.metric("Score", f"{score:.1f}")
                with col3:
                    st.write(session.get("readiness_level", "").title())
        else:
            st.info("No sessions yet. Start your first interview!")
    except ValueError:
        pass
