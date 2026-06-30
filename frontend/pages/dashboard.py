"""
Dashboard page.

Performance analytics, score trends, and session history.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import get_api_client, require_auth
from frontend.components.charts import (
    score_trend_chart,
    session_overview_metrics,
    skill_confidence_bar,
)


def render() -> None:
    """Render the analytics dashboard page."""
    if not require_auth():
        return

    client = get_api_client()

    st.markdown("# Dashboard")
    st.markdown("*Your performance analytics and progress over time*")
    st.markdown("---")

    # ── Overview metrics ────────────────────────────────────────
    try:
        dashboard = client.get_dashboard()
        overview = dashboard.get("overview", {})
        session_overview_metrics(overview)
    except ValueError as e:
        st.warning(f"Could not load dashboard: {e}")
        overview = {}
        dashboard = {}

    st.markdown("---")

    # ── Score trend ─────────────────────────────────────────────
    st.markdown("### Score Trend")
    try:
        trend = client.get_score_trend(limit=15)
        score_trend_chart(trend)
    except ValueError:
        st.info("No score trend data yet.")

    # ── Competency confidence ────────────────────────────────────
    st.markdown("---")
    st.markdown("### Competency Confidence")
    try:
        scores = client.get_competency_scores()
        if scores:
            skill_confidence_bar(scores)
        else:
            st.info("No competency scores yet. Complete an interview to populate this chart.")
    except ValueError:
        pass

    # ── Role performance breakdown ───────────────────────────────
    role_perf = dashboard.get("role_performance", {})
    if role_perf:
        st.markdown("---")
        st.markdown("### Performance by Role")

        cols = st.columns(min(len(role_perf), 3))
        for i, (role, avg_score) in enumerate(role_perf.items()):
            with cols[i % 3]:
                st.metric(role, f"{avg_score:.1f}")

    # ── Recommendations status ───────────────────────────────────
    completion_rate = dashboard.get("recommendation_completion_rate", 0)
    pending = dashboard.get("pending_recommendations", [])
    if completion_rate > 0 or pending:
        st.markdown("---")
        st.markdown("### Learning Progress")

        col_rate, col_pending = st.columns([1, 2])
        with col_rate:
            st.metric("Recommendation Completion", f"{completion_rate:.0f}%")

        with col_pending:
            if pending:
                st.markdown("**Next up:**")
                for rec in pending:
                    priority = rec.get("priority", "medium")
                    title = rec.get("title", "")
                    week = rec.get("week_number", 1)
                    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    st.caption(
                        f"{icons.get(priority, '')} Week {week}: {title}"
                    )

    # ── Session history ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Session History")

    try:
        history = client.get_session_history(limit=10)
        if history:
            for session in history:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{session.get('job_role', '')}**")
                    st.caption(session.get("completed_at", ""))
                with col2:
                    score = session.get("overall_score", 0)
                    st.metric("Score", f"{score:.1f}", label_visibility="collapsed")
                with col3:
                    st.write(session.get("readiness_level", "").title())
                with col4:
                    st.write(f"{session.get('answered_questions', 0)} Qs")
                st.markdown("---")
        else:
            st.info("No completed sessions yet. Start your first interview!")
            if st.button("Start Interview", key="dashboard_start_interview"):
                st.session_state.current_page = "interview"
                st.rerun()
    except ValueError:
        pass
